from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.dependencies import get_current_user
from db.session import get_db
from models.db_models import User
from models.schemas import SoulAnalyzeRequest, SoulAnalyzeResponse
from services import soul_service

router = APIRouter(prefix="/api", tags=["agent"])


@router.post("/soul/analyze", response_model=SoulAnalyzeResponse)
async def soul_analyze(body: SoulAnalyzeRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """心灵之旅情绪分析接口：业务逻辑在 services/soul_service。"""
    result = await soul_service.analyze(db, user, body.emotion, body.user_input, body.conversation_id)
    return SoulAnalyzeResponse(**result)
