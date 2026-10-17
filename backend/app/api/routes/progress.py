"""Learner progress endpoint."""

from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID

from app.api.dependencies import get_database
from app.api.schemas import ProgressResponse
from app.db.database import Database

router = APIRouter(tags=["progress"])


@router.get("/progress/{learner_id}", response_model=ProgressResponse)
def get_progress(learner_id: UUID, database: Database = Depends(get_database)) -> ProgressResponse:
    """Return persisted points, ability, streaks, and topic and lesson progress."""
    progress = database.get_progress(str(learner_id))
    if progress is None:
        raise HTTPException(status_code=404, detail="Learner not found")
    return ProgressResponse.model_validate(progress)
