"""Learner creation endpoint."""

from datetime import UTC, datetime
import sqlite3
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_database
from app.api.schemas import LearnerCreate, LearnerResponse
from app.db.database import Database

router = APIRouter(tags=["learners"])


@router.post("/learners", response_model=LearnerResponse, status_code=status.HTTP_201_CREATED)
def create_learner(payload: LearnerCreate, database: Database = Depends(get_database)) -> LearnerResponse:
    """Create a local learner record without collecting identifying information."""
    nickname = payload.nickname.strip()
    if not nickname:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Nickname cannot be blank")

    try:
        learner = database.create_learner(
            learner_id=str(uuid4()),
            nickname=nickname,
            grade_band=payload.grade_band,
            created_at=datetime.now(UTC).isoformat(),
        )
    except sqlite3.Error as error:
        raise HTTPException(status_code=500, detail="Unable to create learner") from error
    return LearnerResponse.model_validate(learner)
