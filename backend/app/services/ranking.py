from app.services.emotion_analyzer import EMOTIONS

BASE_WEIGHTS = {"semantic": 0.5, "emotion": 0.4, "genre": 0.1}


def emotion_similarity(query: dict[str, float], track: dict[str, float]) -> float:
    difference = sum(abs(query.get(key, 0.0) - track.get(key, 0.0)) for key in EMOTIONS)
    return max(0.0, 1.0 - difference / len(EMOTIONS))


def combined_score(
    *, semantic: float, emotion: float | None, genre: float | None
) -> tuple[float, dict[str, float | None]]:
    active = {"semantic": semantic}
    if emotion is not None:
        active["emotion"] = emotion
    if genre is not None:
        active["genre"] = genre
    total_weight = sum(BASE_WEIGHTS[key] for key in active)
    score = sum(BASE_WEIGHTS[key] * value for key, value in active.items()) / total_weight
    return score, {"semantic": semantic, "emotion": emotion, "genre": genre}
