import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.dependencies import get_current_user
from config.constants import PROVIDER_TEMPLATES
from db.session import get_db
from models.db_models import ApiConfig, User
from models.schemas import (
    ApiConfigCreate,
    ApiConfigResponse,
    ApiConfigUpdate,
    SettingUpdate,
    TestApiRequest,
)
from services.ai_service import ai_service
from services.privacy import decrypt_secret, encrypt_secret
from services.setting_service import get_active_config, get_setting, set_setting

router = APIRouter(prefix="/api", tags=["settings"])

# 与前端约定好的各设置项默认值
SETTING_DEFAULTS = {
    "pet_settings": {"petSize": "medium", "petImageUrl": None, "alwaysOnTop": False, "clickThrough": False, "autoOpenChat": False},
    "theme_settings": {"darkMode": False, "chatTheme": "shiba", "chatFontSize": "medium"},
    "general_settings": {"saveHistory": True, "markdownPath": "./conversations", "mcpEnabled": False},
    "network_proxy": {"enabled": False, "host": "127.0.0.1", "port": 7890},
    "proxy_config": {"enabled": False, "port": 3001, "autoSyncApiConfigs": True},
    "quick_access_templates": ["summarize", "translate", "polish", "explain"],
    "active_config_id": None,
}
INTERNAL_SETTING_KEYS = {"privacy_migration_v1"}


@router.get("/providers")
def get_providers():
    return PROVIDER_TEMPLATES


@router.get("/settings/{key}")
def read_setting(
    key: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if key in INTERNAL_SETTING_KEYS:
        raise HTTPException(404, "设置不存在")
    return get_setting(db, key, SETTING_DEFAULTS.get(key))


@router.put("/settings/{key}")
def update_setting(
    key: str,
    body: SettingUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if key in INTERNAL_SETTING_KEYS:
        raise HTTPException(403, "该设置由系统管理")
    if key == "context_memory_ttl_days":
        raise HTTPException(403, "请通过上下文管理员接口修改记忆保留期限")
    return set_setting(db, key, body.value)


@router.get("/api-configs", response_model=list[ApiConfigResponse])
def list_api_configs(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(ApiConfig).order_by(ApiConfig.created_at.desc()).all()


@router.post("/api-configs", response_model=ApiConfigResponse)
def create_api_config(
    body: ApiConfigCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    config_id = str(uuid.uuid4())
    if body.is_default:
        db.query(ApiConfig).update({ApiConfig.is_default: False})
    values = body.model_dump()
    values["api_key"] = encrypt_secret(values["api_key"])
    config = ApiConfig(id=config_id, **values)
    db.add(config)
    if not get_setting(db, "active_config_id"):
        set_setting(db, "active_config_id", config_id)
    db.commit()
    db.refresh(config)
    return config


@router.put("/api-configs/{config_id}", response_model=ApiConfigResponse)
def update_api_config(
    config_id: str,
    body: ApiConfigUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    config = db.query(ApiConfig).filter(ApiConfig.id == config_id).first()
    if not config:
        raise HTTPException(404, "配置不存在")
    if body.is_default:
        db.query(ApiConfig).update({ApiConfig.is_default: False})
    for field, value in body.model_dump(exclude_unset=True).items():
        if field == "api_key":
            if value is None:
                continue
            value = encrypt_secret(value)
        setattr(config, field, value)
    db.commit()
    db.refresh(config)
    return config


@router.delete("/api-configs/{config_id}")
def delete_api_config(
    config_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    config = db.query(ApiConfig).filter(ApiConfig.id == config_id).first()
    if not config:
        raise HTTPException(404, "配置不存在")
    db.delete(config)
    active_id = get_setting(db, "active_config_id")
    if active_id == config_id:
        set_setting(db, "active_config_id", None)
    db.commit()
    return {"success": True}


@router.post("/api-configs/{config_id}/activate")
def activate_config(
    config_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    config = db.query(ApiConfig).filter(ApiConfig.id == config_id).first()
    if not config:
        raise HTTPException(404, "配置不存在")
    set_setting(db, "active_config_id", config_id)
    return {"success": True, "activeConfigId": config_id}


@router.get("/api-configs/active")
def get_active_api_config(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    config = get_active_config(db)
    if not config:
        return None
    return ApiConfigResponse.model_validate(config)


@router.post("/api-configs/test")
async def test_api_config(body: TestApiRequest, user: User = Depends(get_current_user)):
    return await ai_service.test_connection(body.provider, body.api_url, body.api_key, body.selected_model)


@router.post("/api-configs/{config_id}/test")
async def test_saved_api_config(
    config_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    config = db.query(ApiConfig).filter(ApiConfig.id == config_id).first()
    if not config:
        raise HTTPException(404, "配置不存在")
    return await ai_service.test_connection(
        config.provider,
        config.api_url,
        decrypt_secret(config.api_key),
        config.selected_model,
    )
