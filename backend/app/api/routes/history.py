from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.domain.schemas import SearchHistoryOut
from app.models import SearchHistory, User

router = APIRouter(prefix="/history", tags=["history"])


@router.get("", response_model=list[SearchHistoryOut])
def list_history(
    limit: int = Query(default=30, ge=1, le=100),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> list[SearchHistoryOut]:
    entries = session.scalars(
        select(SearchHistory).where(SearchHistory.user_id == user.id).order_by(SearchHistory.created_at.desc()).limit(limit)
    )
    return [SearchHistoryOut.model_validate(item) for item in entries]
