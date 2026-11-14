from app.domain.schemas import ScoreBreakdown, TrackOut
from app.models import Track


def track_to_out(
    track: Track,
    *,
    score: float = 0,
    score_breakdown: ScoreBreakdown | None = None,
    is_favorite: bool = False,
) -> TrackOut:
    return TrackOut(
        id=track.id,
        title=track.title,
        artist=track.artist,
        genre=track.genre,
        description=track.description,
        emotion_scores=track.emotion_scores or {},
        listening_url=track.listening_url,
        score=score,
        score_breakdown=score_breakdown,
        is_favorite=is_favorite,
    )
