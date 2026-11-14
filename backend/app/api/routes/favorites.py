from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.domain.mappers import track_to_out
from app.domain.schemas import TrackOut
from app.models import Favorite, Track, User

router = APIRouter(prefix="/favorites", tags=["favorites"])


@router.get("", response_model=list[TrackOut])
def list_favorites(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> list[TrackOut]:
    tracks = session.scalars(
        select(Track).join(Favorite).where(Favorite.user_id == user.id).order_by(Favorite.created_at.desc())
    )
    return [track_to_out(track, is_favorite=True) for track in tracks]


@router.post("/{track_id}", status_code=status.HTTP_201_CREATED)
def add_favorite(
    track_id: UUID,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> dict[str, str]:
    track = session.get(Track, track_id)
    if track is None:
        raise HTTPException(status_code=404, detail="Композиция не найдена")
    favorite = session.get(Favorite, (user.id, track_id))
    if favorite is None:
        session.add(Favorite(user_id=user.id, track_id=track_id))
        session.commit()
    return {"message": "Композиция добавлена в избранное"}


@router.delete("/{track_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_favorite(
    track_id: UUID,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> None:
    favorite = session.get(Favorite, (user.id, track_id))
    if favorite is not None:
        session.delete(favorite)
        session.commit()
