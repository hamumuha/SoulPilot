import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.dependencies import get_current_user
from db.session import get_db
from models.db_models import ContextMemory, Conversation, Message, User
from models.schemas import ConversationSave
from services.privacy import redact_sensitive_data

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.post("")
def create_conversation(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    conv_id = str(uuid.uuid4())
    conv = Conversation(id=conv_id, title="新对话", user_id=user.id, source="chat")
    db.add(conv)
    db.commit()
    return {"id": conv_id, "title": "新对话"}


@router.get("/user/active")
def get_active_conversation(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """获取当前用户的最近一个对话（没有则新建），供 hamu-pet 与心灵之旅共享。"""
    conv = (
        db.query(Conversation)
        .filter(Conversation.user_id == user.id)
        .order_by(Conversation.updated_at.desc())
        .first()
    )
    if not conv:
        conv_id = str(uuid.uuid4())
        conv = Conversation(id=conv_id, title="新对话", user_id=user.id, source="chat")
        db.add(conv)
        db.commit()
        db.refresh(conv)
    return {"id": conv.id, "title": conv.title, "source": conv.source or "chat"}


@router.get("/user")
def list_user_conversations(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = (
        db.query(Conversation)
        .filter(Conversation.user_id == user.id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )
    return [
        {
            "id": r.id,
            "title": redact_sensitive_data(r.title or ""),
            "source": r.source or "chat",
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


@router.delete("/{conversation_id}")
def delete_conversation(conversation_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """删除对话及其全部消息。

    消息表 conversation_id 无外键级联约束，必须在同一事务内先显式删除消息、
    再删除会话，否则会残留孤儿消息或删除失败。
    """
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(404, "对话不存在")
    if conv.user_id and conv.user_id != user.id:
        raise HTTPException(403, "无权删除该对话")

    deleted_messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .delete(synchronize_session=False)
    )
    deleted_memories = (
        db.query(ContextMemory)
        .filter(ContextMemory.conversation_id == conversation_id)
        .delete(synchronize_session=False)
    )
    db.delete(conv)
    db.commit()
    return {
        "success": True,
        "deleted": conversation_id,
        "deleted_messages": deleted_messages,
        "deleted_memories": deleted_memories,
    }


@router.get("/{conversation_id}/messages")
def get_conversation_messages(conversation_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(404, "对话不存在")
    if conv.user_id and conv.user_id != user.id:
        raise HTTPException(403, "无权访问该对话")
    rows = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .all()
    )
    return [
        {
            "id": r.id,
            "role": r.role,
            "content": redact_sensitive_data(r.content),
            "model": r.model,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


@router.post("/save")
def save_conversation(body: ConversationSave, user: User = Depends(get_current_user)):
    """导出对话为 Markdown（对话内容已由 /api/chat/stream 实时入库，此处不再重复写库）。"""
    md_lines = [f"# AI对话记录\n\n> 创建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"]
    q_idx = 0
    for msg in body.messages:
        if msg.role == "user":
            q_idx += 1
            md_lines.append(f"\n## 问题 {q_idx}\n\n{redact_sensitive_data(msg.content)}\n")
        elif msg.role == "assistant":
            md_lines.append(f"\n## 回答 {q_idx}\n\n{redact_sensitive_data(msg.content)}\n")
    markdown = "\n".join(md_lines)
    return {"success": True, "markdown": markdown}
