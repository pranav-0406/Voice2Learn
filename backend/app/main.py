
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.api.routes.learners import router as learners_router
from app.api.routes.lessons import router as lessons_router
from app.api.routes.progress import router as progress_router
from app.api.routes.quiz import router as quiz_router
from app.api.routes.subjects import router as subjects_router
from app.api.routes.voice import router as voice_router
from app.core.config import get_settings
from app.db.database import initialize_database

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Prepare the local SQLite schema and bundled lesson data at startup."""
    initialize_database(get_settings().database_path)
    yield

app = FastAPI(
    title="Voice2Learn API",
    description="Voice-first adaptive learning for children with mobility challenges",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(health_router, prefix="/api")
app.include_router(learners_router, prefix="/api")
app.include_router(subjects_router, prefix="/api")
app.include_router(lessons_router, prefix="/api")
app.include_router(quiz_router, prefix="/api")
app.include_router(progress_router, prefix="/api")
app.include_router(voice_router, prefix="/api")
