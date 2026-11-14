import re
from threading import Lock
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.domain.schemas import ScoreBreakdown, SearchRequest, SearchResponse, TrackOut
from app.models import Favorite, SearchHistory, Track
from app.repositories.track_repository import TrackRepository
from app.services.embedding_service import ModelUnavailable, get_embedding_service
from app.services.emotion_analyzer import EmotionAnalyzer
from app.services.ranking import combined_score, emotion_similarity

TOKEN_RE = re.compile(r"[а-яёa-z0-9]+", re.IGNORECASE)
STOP_WORDS = {"в", "во", "для", "и", "из", "к", "как", "мне", "музыку", "на", "не", "о", "под", "после", "с", "что", "хочу", "это", "послушать"}


def _lexical_score(query: str, track: Track) -> float:
    query_terms = {token.lower() for token in TOKEN_RE.findall(query) if token.lower() not in STOP_WORDS}
    if not query_terms:
        return 0.0
    track_text = f"{track.title} {track.artist} {track.genre} {track.description}"
    track_terms = {token.lower() for token in TOKEN_RE.findall(track_text)}
    matched = sum(any(term == candidate or (len(term) > 5 and candidate.startswith(term[:6])) for candidate in track_terms) for term in query_terms)
    return matched / len(query_terms)


def _track_text(track: Track) -> str:
    return f"{track.title}. {track.artist}. Жанр: {track.genre}. {track.description}"


class SearchService:
    def __init__(self) -> None:
        self.emotion_analyzer = EmotionAnalyzer()
        self._backfill_lock = Lock()

    def _backfill_embeddings(self, repository: TrackRepository, session: Session) -> None:
        with self._backfill_lock:
            settings = get_settings()
            missing = repository.tracks_without_embeddings(model_name=settings.embedding_model)
            if not missing:
                return
            vectors = get_embedding_service().encode_documents([_track_text(track) for track in missing])
            for track, vector in zip(missing, vectors, strict=True):
                track.embedding = vector
                track.embedding_model = settings.embedding_model
            session.commit()

    @staticmethod
    def _favorite_ids(session: Session, user_id: UUID | None) -> set[UUID]:
        if user_id is None:
            return set()
        return set(session.scalars(select(Favorite.track_id).where(Favorite.user_id == user_id)))

    def search(self, request: SearchRequest, session: Session, user_id: UUID | None = None) -> SearchResponse:
        repository = TrackRepository(session)
        query_emotions = self.emotion_analyzer.analyze(request.query)
        has_emotion_signal = self.emotion_analyzer.has_signal(query_emotions)
        notice = None

        try:
            self._backfill_embeddings(repository, session)
            query_vector = get_embedding_service().encode_query(request.query)
            candidates = repository.nearest(query_vector, limit=max(request.limit * 8, 80), genre=request.genre)
            mode = "hybrid"
            scored_candidates = [
                (track, max(0.0, min(1.0, 1.0 - distance / 2.0)), None)
                for track, distance in candidates
            ]
        except ModelUnavailable as exc:
            mode = "lexical_fallback"
            notice = str(exc)
            tracks = repository.list_tracks(genre=request.genre, limit=300)
            scored_candidates = [(track, None, _lexical_score(request.query, track)) for track in tracks]

        favorite_ids = self._favorite_ids(session, user_id)
        results: list[TrackOut] = []
        for track, semantic_score, lexical_score in scored_candidates:
            emotion_score = emotion_similarity(query_emotions, track.emotion_scores or {}) if has_emotion_signal else None
            if mode == "lexical_fallback" and (lexical_score or 0.0) <= 0 and (emotion_score or 0.0) < 0.82:
                continue
            genre_score = 1.0 if request.genre else None
            primary_score = semantic_score if semantic_score is not None else (lexical_score or 0.0)
            score, breakdown = combined_score(
                semantic=primary_score,
                emotion=emotion_score,
                genre=genre_score,
            )
            if semantic_score is None:
                breakdown["semantic"] = None
                breakdown["lexical"] = lexical_score

            results.append(
                TrackOut(
                    id=track.id,
                    title=track.title,
                    artist=track.artist,
                    genre=track.genre,
                    description=track.description,
                    emotion_scores=track.emotion_scores or {},
                    listening_url=track.listening_url,
                    score=round(score, 4),
                    score_breakdown=ScoreBreakdown(**breakdown),
                    is_favorite=track.id in favorite_ids,
                )
            )

        results.sort(key=lambda item: item.score, reverse=True)
        return SearchResponse(
            query=request.query,
            mode=mode,
            emotion_mode=self.emotion_analyzer.mode,
            embedding_model=get_settings().embedding_model if mode == "hybrid" else None,
            notice=notice,
            results=results[: request.limit],
        )


def save_search(session: Session, user_id: UUID | None, query: str) -> None:
    if user_id is None:
        return
    session.add(SearchHistory(user_id=user_id, query=query))
    session.commit()
