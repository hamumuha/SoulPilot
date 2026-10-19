import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from api.dependencies import get_current_user
from config.settings import CONTEXT_ADMIN_USERNAMES
from db.session import get_db
from models.db_models import ContextMemory, User
from models.schemas import ContextMemoryCreate, ContextMemoryUpdate, ContextRetentionUpdate
from services.context_service import (
    DEFAULT_TTL_DAYS,
    cleanup_expired,
    expiry_for,
    get_ttl_days,
)
from services.privacy import redact_sensitive_data
from services.setting_service import set_setting

router = APIRouter(prefix="/api/context", tags=["context"])


def _is_admin(user: User) -> bool:
    return user.username.lower() in CONTEXT_ADMIN_USERNAMES


def _memory_payload(memory: ContextMemory) -> dict:
    return {
        "id": memory.id,
        "kind": memory.kind,
        "title": redact_sensitive_data(memory.title),
        "content": redact_sensitive_data(memory.content),
        "source": memory.source,
        "conversation_id": memory.conversation_id,
        "expires_at": memory.expires_at.isoformat() if memory.expires_at else None,
        "created_at": memory.created_at.isoformat() if memory.created_at else None,
        "updated_at": memory.updated_at.isoformat() if memory.updated_at else None,
        "is_global": memory.user_id is None,
    }


@router.get("/memories")
def list_memories(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    admin = _is_admin(user)
    cleanup_expired(db, user.id, include_global=admin)
    query = db.query(ContextMemory).filter(
        or_(
            ContextMemory.user_id == user.id,
            ContextMemory.kind == "global_knowledge",
        ),
        or_(ContextMemory.expires_at.is_(None), ContextMemory.expires_at > datetime.utcnow()),
    )
    rows = query.order_by(ContextMemory.updated_at.desc()).limit(200).all()
    return {
        "is_admin": admin,
        "memories": [_memory_payload(row) for row in rows],
        "ttl_days": get_ttl_days(db),
        "default_ttl_days": DEFAULT_TTL_DAYS,
    }


@router.post("/memories")
def create_memory(
    body: ContextMemoryCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if body.kind == "global_knowledge" and not _is_admin(user):
        raise HTTPException(403, "只有配置的上下文管理员可以维护全局知识")
    if not body.title.strip() or not body.content.strip():
        raise HTTPException(422, "标题和内容不能为空")
    memory = ContextMemory(
        id=str(uuid.uuid4()),
        user_id=None if body.kind == "global_knowledge" else user.id,
        kind=body.kind,
        title=body.title.strip(),
        content=body.content.strip(),
        source="manual",
        expires_at=expiry_for(db, body.kind),
    )
    db.add(memory)
    db.commit()
    db.refresh(memory)
    return _memory_payload(memory)


@router.put("/memories/{memory_id}")
def update_memory(
    memory_id: str,
    body: ContextMemoryUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    memory = db.query(ContextMemory).filter(ContextMemory.id == memory_id).first()
    if not memory:
        raise HTTPException(404, "记忆不存在")
    if memory.kind not in {"preference", "global_knowledge"}:
        raise HTTPException(403, "自动生成的摘要和工具结果不能编辑")
    if memory.user_id != user.id and not (memory.user_id is None and _is_admin(user)):
        raise HTTPException(403, "无权编辑该记忆")
    values = body.model_dump(exclude_unset=True)
    if "title" in values:
        if not values["title"].strip():
            raise HTTPException(422, "标题不能为空")
        memory.title = redact_sensitive_data(values["title"].strip())
    if "content" in values:
        if not values["content"].strip():
            raise HTTPException(422, "内容不能为空")
        memory.content = redact_sensitive_data(values["content"].strip())
    memory.expires_at = expiry_for(db, memory.kind)
    db.commit()
    db.refresh(memory)
    return _memory_payload(memory)


@router.delete("/memories")
def clear_user_memories(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    deleted = (
        db.query(ContextMemory)
        .filter(ContextMemory.user_id == user.id)
        .delete(synchronize_session=False)
    )
    db.commit()
    return {"success": True, "deleted": deleted}


@router.delete("/memories/{memory_id}")
def delete_memory(
    memory_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    memory = db.query(ContextMemory).filter(ContextMemory.id == memory_id).first()
    if not memory:
        raise HTTPException(404, "记忆不存在")
    if memory.user_id != user.id and not (memory.user_id is None and _is_admin(user)):
        raise HTTPException(403, "无权删除该记忆")
    db.delete(memory)
    db.commit()
    return {"success": True}


@router.post("/cleanup")
def cleanup_memories(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    deleted = cleanup_expired(db, user.id, include_global=_is_admin(user))
    return {"success": True, "deleted": deleted}


@router.put("/retention")
def update_retention(
    body: ContextRetentionUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not _is_admin(user):
        raise HTTPException(403, "只有配置的上下文管理员可以修改保留期限")
    values = body.ttl_days
    if set(values) != set(DEFAULT_TTL_DAYS):
        raise HTTPException(422, "必须为每种记忆类型提供保留天数")
    for kind, days in values.items():
        if days is not None and not 1 <= days <= 3650:
            raise HTTPException(422, f"{kind} 的保留期限必须为 1 至 3650 天，或设为 null 表示永不过期")
    set_setting(db, "context_memory_ttl_days", values)
    for memory in db.query(ContextMemory).all():
        days = values[memory.kind]
        memory.expires_at = (
            (memory.created_at or datetime.utcnow()) + timedelta(days=days)
            if days is not None
            else None
        )
    db.commit()
    return {"ttl_days": get_ttl_days(db)}
