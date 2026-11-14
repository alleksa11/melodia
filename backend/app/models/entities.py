from datetime import datetime, timezone
from uuid import UUID, uuid4

from pgvector.sqlalchemy import VECTOR
from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(80))
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    favorites: Mapped[list["Favorite"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    search_history: Mapped[list["SearchHistory"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Track(Base):
    __tablename__ = "tracks"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column(String(180), index=True)
    artist: Mapped[str] = mapped_column(String(180), index=True)
    genre: Mapped[str] = mapped_column(String(80), index=True)
    description: Mapped[str] = mapped_column(Text)
    listening_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    emotion_scores: Mapped[dict[str, float]] = mapped_column(JSON, default=dict)
    embedding: Mapped[list[float] | None] = mapped_column(VECTOR(get_settings().embedding_dimensions), nullable=True)
    embedding_model: Mapped[str | None] = mapped_column(String(250), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    favorites: Mapped[list["Favorite"]] = relationship(back_populates="track", cascade="all, delete-orphan")


class Favorite(Base):
    __tablename__ = "favorites"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    track_id: Mapped[UUID] = mapped_column(ForeignKey("tracks.id", ondelete="CASCADE"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user: Mapped[User] = relationship(back_populates="favorites")
    track: Mapped[Track] = relationship(back_populates="favorites")


class SearchHistory(Base):
    __tablename__ = "search_history"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    query: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user: Mapped[User] = relationship(back_populates="search_history")
