"""Lesson retrieval endpoint."""

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_database
from app.api.schemas import LessonResponse
from app.db.database import Database

router = APIRouter(tags=["learning"])


@router.get("/lessons/{lesson_id}", response_model=LessonResponse)
def get_lesson(lesson_id: str, database: Database = Depends(get_database)) -> LessonResponse:
    """Return one seeded lesson or a standard HTTP 404 response."""
    lesson = database.get_lesson(lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")
    return LessonResponse.model_validate(lesson)
