from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_optional_user
from app.domain.schemas import SearchRequest, SearchResponse
from app.models import User
from app.services.search_service import SearchService, save_search

router = APIRouter(prefix="/search", tags=["search"])
search_service = SearchService()


@router.post("", response_model=SearchResponse)
def search(
    request: SearchRequest,
    session: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
) -> SearchResponse:
    response = search_service.search(request, session, user.id if user else None)
    save_search(session, user.id if user else None, request.query)
    return response
