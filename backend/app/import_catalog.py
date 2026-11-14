import csv
import sys
from pathlib import Path
from urllib.parse import urlparse

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import Track
from app.services.emotion_analyzer import EMOTIONS

REQUIRED_COLUMNS = {"title", "artist", "genre", "description"}


def import_csv(path: Path) -> tuple[int, int]:
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        columns = set(reader.fieldnames or ())
        missing = REQUIRED_COLUMNS - columns
        if missing:
            raise ValueError(f"В CSV отсутствуют обязательные столбцы: {', '.join(sorted(missing))}")

        added = updated = 0
        seen: dict[tuple[str, str], Track] = {}
        with SessionLocal() as session:
            for line_number, row in enumerate(reader, start=2):
                title, artist, genre, description = (row.get(key, "").strip() for key in ("title", "artist", "genre", "description"))
                if not all((title, artist, genre, description)):
                    raise ValueError(f"Строка {line_number}: title, artist, genre и description обязательны")

                emotions: dict[str, float] = {}
                for emotion in EMOTIONS:
                    raw_value = (row.get(emotion) or "0").strip()
                    value = float(raw_value) if raw_value else 0.0
                    if not 0.0 <= value <= 1.0:
                        raise ValueError(f"Строка {line_number}: {emotion} должен быть в диапазоне 0..1")
                    emotions[emotion] = value

                listening_url = (row.get("listening_url") or "").strip() or None
                if listening_url:
                    parsed_url = urlparse(listening_url)
                    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
                        raise ValueError(f"Строка {line_number}: listening_url должен быть HTTP(S)-ссылкой")

                key = (title, artist)
                track = seen.get(key) or session.scalar(select(Track).where(Track.title == title, Track.artist == artist))
                fields = {
                    "genre": genre,
                    "description": description,
                    "listening_url": listening_url,
                    "emotion_scores": emotions,
                    "embedding": None,
                    "embedding_model": None,
                }
                if track is None:
                    track = Track(title=title, artist=artist, **fields)
                    session.add(track)
                    added += 1
                else:
                    for field, value in fields.items():
                        setattr(track, field, value)
                    updated += 1
                seen[key] = track
            session.commit()
        return added, updated


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Использование: python -m app.import_catalog <path-to-csv>")
    inserted, changed = import_csv(Path(sys.argv[1]))
    print(f"Добавлено: {inserted}; обновлено: {changed}")
