import hashlib
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from models.db_models import Session as SessionRow, User

# 简单的会话有效期：7 天
SESSION_DAYS = 7


def hash_session_token(token: str) -> str:
    if len(token) == 64 and all(char in "0123456789abcdef" for char in token.lower()):
        return token.lower()
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
    return f"{salt}${hashed.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, hashed_hex = stored.split("$", 1)
    except ValueError:
        return False
    hashed = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
    return hashed.hex() == hashed_hex


def create_session(db: Session, user_id: str) -> str:
    # 清理该用户旧会话，保持单点登录
    db.query(SessionRow).filter(SessionRow.user_id == user_id).delete()
    token = secrets.token_urlsafe(32)
    expires = datetime.now() + timedelta(days=SESSION_DAYS)
    db.add(SessionRow(token=hash_session_token(token), user_id=user_id, expires_at=expires))
    db.commit()
    return token


def get_user_by_token(db: Session, token: Optional[str]) -> Optional[User]:
    if not token:
        return None
    row = db.query(SessionRow).filter(SessionRow.token == hash_session_token(token)).first()
    if not row:
        return None
    if row.expires_at and row.expires_at < datetime.now():
        db.delete(row)
        db.commit()
        return None
    return db.query(User).filter(User.id == row.user_id).first()


def new_user_id() -> str:
    return str(uuid.uuid4())
