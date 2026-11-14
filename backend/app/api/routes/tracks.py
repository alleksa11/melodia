from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domain.mappers import track_to_out
from app.domain.schemas import TrackOut
from app.models import Track

router = APIRouter(prefix="/tracks", tags=["tracks"])


@router.get("", response_model=list[TrackOut])
def list_tracks(
    genre: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_db),
) -> list[TrackOut]:
    statement = select(Track).order_by(Track.artist, Track.title).limit(limit)
    if genre:
        statement = statement.where(Track.genre.ilike(f"%{genre.strip()}%"))
    return [track_to_out(track) for track in session.scalars(statement)]


@router.get("/{track_id}", response_model=TrackOut)
def get_track(track_id: UUID, session: Session = Depends(get_db)) -> TrackOut:
    track = session.get(Track, track_id)
    if track is None:
        raise HTTPException(status_code=404, detail="Композиция не найдена")
    return track_to_out(track)
