from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.dependencies import get_current_user
from core.security import create_session, hash_password, new_user_id, verify_password
from db.session import get_db
from models.db_models import Session as SessionRow, User
from models.schemas import AuthResponse, LoginRequest, RegisterRequest, UserPublic

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    username = body.username.strip()
    if not username or len(username) < 2:
        raise HTTPException(400, "用户名至少 2 个字符")
    if len(body.password) < 4:
        raise HTTPException(400, "密码至少 4 个字符")
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(400, "用户名已存在")
    user = User(id=new_user_id(), username=username, password_hash=hash_password(body.password))
    db.add(user)
    db.commit()
    token = create_session(db, user.id)
    return AuthResponse(token=token, user=UserPublic(id=user.id, username=user.username))


@router.post("/login", response_model=AuthResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username.strip()).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "用户名或密码错误")
    token = create_session(db, user.id)
    return AuthResponse(token=token, user=UserPublic(id=user.id, username=user.username))


@router.post("/logout")
def logout(current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(SessionRow).filter(SessionRow.user_id == current.id).delete()
    db.commit()
    return {"success": True}


@router.get("/me", response_model=UserPublic)
def me(current: User = Depends(get_current_user)):
    return UserPublic(id=current.id, username=current.username)
