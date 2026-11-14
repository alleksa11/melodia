from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.auth import router as auth_router
from app.api.routes.favorites import router as favorites_router
from app.api.routes.history import router as history_router
from app.api.routes.search import router as search_router
from app.api.routes.tracks import router as tracks_router
from app.core.config import get_settings

settings = get_settings()
app = FastAPI(
    title=f"{settings.app_name} API",
    description="Семантический поиск музыкальных композиций с эмоциональным ранжированием.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api")
app.include_router(search_router, prefix="/api")
app.include_router(tracks_router, prefix="/api")
app.include_router(favorites_router, prefix="/api")
app.include_router(history_router, prefix="/api")


@app.get("/api/health", tags=["service"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "moodify-api", "version": "1.0.0"}
