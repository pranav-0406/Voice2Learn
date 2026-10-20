from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_database
from app.api.schemas import (
    LearnerPositionResponse,
    LearnerPositionSaveRequest,
    ProgressResponse,
)
from app.db.database import Database

router = APIRouter(tags=["progress"])


@router.get("/progress/{learner_id}", response_model=ProgressResponse)
def get_progress(learner_id: UUID, database: Database = Depends(get_database)) -> ProgressResponse:
    """Return persisted points, ability, streaks, and topic and lesson progress."""
    progress = database.get_progress(str(learner_id))
    if progress is None:
        raise HTTPException(status_code=404, detail="Learner not found")
    return ProgressResponse.model_validate(progress)


@router.post("/progress/position", response_model=LearnerPositionResponse)
def save_active_position(
    payload: LearnerPositionSaveRequest,
    database: Database = Depends(get_database),
) -> LearnerPositionResponse:
    """Save the learner's last visited curriculum concept/chapter position."""
    saved = database.save_active_position(
        learner_id=payload.learner_id,
        subject_id=payload.subject_id,
        chapter_id=payload.chapter_id,
        concept_id=payload.concept_id,
    )
    pos = database.get_active_position(payload.learner_id, payload.subject_id)
    if not pos:
        return LearnerPositionResponse(**saved)
    return LearnerPositionResponse(**pos)


@router.get("/progress/{learner_id}/position", response_model=LearnerPositionResponse | None)
def get_active_position(
    learner_id: str,
    subject_id: str | None = Query(default=None),
    database: Database = Depends(get_database),
) -> LearnerPositionResponse | None:
    """Get the learner's last visited concept/chapter position."""
    pos = database.get_active_position(learner_id, subject_id)
    if not pos:
        return None
    return LearnerPositionResponse(**pos)
