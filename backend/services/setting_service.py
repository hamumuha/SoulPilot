from typing import Any, Optional

from sqlalchemy.orm import Session

from models.db_models import ApiConfig, Setting


def get_setting(db: Session, key: str, default: Any = None) -> Any:
    row = db.query(Setting).filter(Setting.setting_key == key).first()
    if row:
        return row.setting_value
    return default


def set_setting(db: Session, key: str, value: Any) -> Any:
    row = db.query(Setting).filter(Setting.setting_key == key).first()
    if row:
        row.setting_value = value
    else:
        row = Setting(setting_key=key, setting_value=value)
        db.add(row)
    db.commit()
    return value


def get_active_config(db: Session) -> Optional[ApiConfig]:
    active_id = get_setting(db, "active_config_id")
    if active_id:
        config = db.query(ApiConfig).filter(ApiConfig.id == active_id, ApiConfig.enabled == True).first()
        if config:
            return config
    return db.query(ApiConfig).filter(ApiConfig.enabled == True, ApiConfig.is_default == True).first()
