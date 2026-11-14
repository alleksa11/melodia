from sqlalchemy import func, select

from app.core.database import SessionLocal
from app.data.demo_catalog import DEMO_TRACKS
from app.models import Track


def seed_demo_catalog() -> int:
    with SessionLocal() as session:
        existing = session.scalar(select(func.count()).select_from(Track)) or 0
        if existing:
            return 0
        session.add_all(Track(**item) for item in DEMO_TRACKS)
        session.commit()
        return len(DEMO_TRACKS)


if __name__ == "__main__":
    print(f"Добавлено демонстрационных композиций: {seed_demo_catalog()}")
