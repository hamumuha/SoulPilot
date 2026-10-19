from typing import Optional

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from core.security import get_user_by_token
from db.session import get_db
from models.db_models import User


def get_current_user(
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    user = get_user_by_token(db, token)
    if not user:
        raise HTTPException(status_code=401, detail="未登录或会话已过期，请重新登录")
    return user


def optional_user(
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
) -> Optional[User]:
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    return get_user_by_token(db, token)
