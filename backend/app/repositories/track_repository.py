from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import Track


class TrackRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_tracks(self, *, genre: str | None = None, limit: int = 50) -> list[Track]:
        statement = select(Track).order_by(Track.artist, Track.title).limit(limit)
        if genre:
            statement = statement.where(Track.genre.ilike(f"%{genre.strip()}%"))
        return list(self.session.scalars(statement))

    def tracks_without_embeddings(self, *, model_name: str, genre: str | None = None) -> list[Track]:
        statement = select(Track).where(
            or_(Track.embedding.is_(None), Track.embedding_model.is_(None), Track.embedding_model != model_name)
        )
        if genre:
            statement = statement.where(Track.genre.ilike(f"%{genre.strip()}%"))
        return list(self.session.scalars(statement))

    def nearest(self, vector: list[float], *, limit: int, genre: str | None = None) -> list[tuple[Track, float]]:
        distance = Track.embedding.cosine_distance(vector).label("distance")
        statement = select(Track, distance).where(Track.embedding.is_not(None)).order_by(distance).limit(limit)
        if genre:
            statement = statement.where(Track.genre.ilike(f"%{genre.strip()}%"))
        return [(track, float(distance_value)) for track, distance_value in self.session.execute(statement).all()]
