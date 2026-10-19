import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from config.constants import BUILTIN_TEMPLATES
from db.session import get_db
from models.db_models import CustomTemplate
from models.schemas import SettingUpdate, TemplateCreate, TemplateUpdate
from services.setting_service import get_setting, set_setting

router = APIRouter(prefix="/api", tags=["templates"])


@router.get("/templates/builtin")
def get_builtin_templates():
    return BUILTIN_TEMPLATES


@router.get("/templates/custom")
def get_custom_templates(db: Session = Depends(get_db)):
    rows = db.query(CustomTemplate).order_by(CustomTemplate.created_at.desc()).all()
    return [
        {"id": r.id, "name": r.name, "icon": r.icon, "category": r.category, "prompt": r.prompt, "isBuiltin": False}
        for r in rows
    ]


@router.post("/templates/custom")
def create_custom_template(body: TemplateCreate, db: Session = Depends(get_db)):
    tpl = CustomTemplate(id=str(uuid.uuid4()), **body.model_dump())
    db.add(tpl)
    db.commit()
    return {"id": tpl.id, **body.model_dump(), "isBuiltin": False}


@router.put("/templates/custom/{template_id}")
def update_custom_template(template_id: str, body: TemplateUpdate, db: Session = Depends(get_db)):
    tpl = db.query(CustomTemplate).filter(CustomTemplate.id == template_id).first()
    if not tpl:
        raise HTTPException(404, "模板不存在")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(tpl, field, value)
    db.commit()
    return {"success": True}


@router.delete("/templates/custom/{template_id}")
def delete_custom_template(template_id: str, db: Session = Depends(get_db)):
    tpl = db.query(CustomTemplate).filter(CustomTemplate.id == template_id).first()
    if not tpl:
        raise HTTPException(404, "模板不存在")
    db.delete(tpl)
    db.commit()
    return {"success": True}


@router.get("/templates/quick-access")
def get_quick_access(db: Session = Depends(get_db)):
    return get_setting(db, "quick_access_templates", ["summarize", "translate", "polish", "explain"])


@router.put("/templates/quick-access")
def set_quick_access(body: SettingUpdate, db: Session = Depends(get_db)):
    return set_setting(db, "quick_access_templates", body.value)
