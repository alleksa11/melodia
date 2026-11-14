from functools import lru_cache
from threading import Lock
from typing import Sequence

from app.core.config import get_settings


class ModelUnavailable(RuntimeError):
    """Raised when the optional embedding runtime or model cannot be loaded."""


class EmbeddingService:
    def __init__(self) -> None:
        self.model_name = get_settings().embedding_model
        self._model = None
        self._lock = Lock()

    def _load(self):
        with self._lock:
            if self._model is not None:
                return self._model
            try:
                from sentence_transformers import SentenceTransformer

                self._model = SentenceTransformer(self.model_name, device="cpu")
                return self._model
            except Exception as exc:
                raise ModelUnavailable(
                    "Не удалось загрузить модель. Установите backend с extra [ml] и проверьте "
                    "доступ к Hugging Face при первом запуске."
                ) from exc

    def encode_query(self, text: str) -> list[float]:
        model = self._load()
        encoder = getattr(model, "encode_query", model.encode)
        result = encoder(text, normalize_embeddings=True, show_progress_bar=False)
        return result.tolist()

    def encode_documents(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        model = self._load()
        encoder = getattr(model, "encode_document", model.encode)
        result = encoder(list(texts), normalize_embeddings=True, show_progress_bar=False)
        return result.tolist()


@lru_cache(maxsize=1)
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()
