from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Melodia"
    environment: str = "development"
    database_url: str = "postgresql+psycopg://melodia:melodia_local@localhost:5432/melodia"
    jwt_secret_key: str = "change-this-development-secret-before-deploying"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    embedding_dimensions: Literal[384] = 384
    emotion_model: str = "Aniemore/rubert-tiny2-russian-emotion-detection"
    cors_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=(".env", "../.env"), env_file_encoding="utf-8", extra="ignore")

    @field_validator("embedding_dimensions", mode="before")
    @classmethod
    def parse_embedding_dimensions(cls, value: object) -> int:
        # Environment variables arrive as strings, while this model dimension is fixed.
        return int(value)

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
