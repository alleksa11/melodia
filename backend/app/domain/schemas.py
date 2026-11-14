from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl


class UserCreate(BaseModel):
    email: EmailStr
    display_name: str = Field(min_length=2, max_length=80)
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    display_name: str
    created_at: datetime


class TokenOut(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    user: UserOut


class SearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=500, description="Описание желаемой музыки")
    genre: str | None = Field(default=None, max_length=80)
    limit: int = Field(default=10, ge=1, le=30)


class ScoreBreakdown(BaseModel):
    semantic: float | None = None
    lexical: float | None = None
    emotion: float | None = None
    genre: float | None = None


class TrackOut(BaseModel):
    id: UUID
    title: str
    artist: str
    genre: str
    description: str
    emotion_scores: dict[str, float]
    listening_url: HttpUrl | None = None
    score: float = 0
    score_breakdown: ScoreBreakdown | None = None
    is_favorite: bool = False


class SearchResponse(BaseModel):
    query: str
    mode: Literal["hybrid", "lexical_fallback"]
    emotion_mode: Literal["rubert_multi_label", "lexicon"]
    embedding_model: str | None = None
    notice: str | None = None
    results: list[TrackOut]


class SearchHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    query: str
    created_at: datetime


class MessageOut(BaseModel):
    message: str
