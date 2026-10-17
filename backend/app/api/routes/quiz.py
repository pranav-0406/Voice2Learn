"""Adaptive quiz delivery and answer evaluation endpoints."""

from datetime import UTC, datetime
import sqlite3
from uuid import uuid4
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import get_database
from app.api.schemas import QuizAnswerRequest, QuizAnswerResponse, QuizNextResponse
from app.db.database import Database

router = APIRouter(tags=["quiz"])


@router.get("/quiz/next", response_model=QuizNextResponse)
def get_next_question(
    learner_id: UUID = Query(),
    subject: str = Query(min_length=1),
    database: Database = Depends(get_database),
) -> QuizNextResponse:
    """Return an unanswered question near the learner's current target difficulty."""
    learner_id_value = str(learner_id)
    if database.get_learner(learner_id_value) is None:
        raise HTTPException(status_code=404, detail="Learner not found")
    subject_id = subject.casefold().strip()
    if not database.subject_exists(subject_id):
        raise HTTPException(status_code=400, detail="Unsupported subject")
    question = database.get_next_question(learner_id_value, subject_id)
    if question is None:
        return QuizNextResponse(question=None, message="No unanswered questions remain for this subject")
    return QuizNextResponse(question=question, message="Question ready")


@router.post("/quiz/answer", response_model=QuizAnswerResponse)
def answer_question(
    payload: QuizAnswerRequest, database: Database = Depends(get_database)
) -> QuizAnswerResponse:
    """Evaluate and persist one answer without ever returning accepted answers."""
    learner_id = str(payload.learner_id)
    if database.get_learner(learner_id) is None:
        raise HTTPException(status_code=404, detail="Learner not found")
    if not database.question_exists(payload.question_id):
        raise HTTPException(status_code=404, detail="Question not found")
    submitted_answer = payload.answer.strip()
    if not submitted_answer:
        raise HTTPException(status_code=422, detail="Answer cannot be blank")
    try:
        result = database.submit_answer(
            learner_id=learner_id,
            question_id=payload.question_id,
            submitted_answer=submitted_answer,
            attempt_id=str(uuid4()),
            created_at=datetime.now(UTC).isoformat(),
        )
    except sqlite3.Error as error:
        raise HTTPException(status_code=500, detail="Unable to record answer") from error
    if result is None:
        raise HTTPException(status_code=404, detail="Learner or question not found")
    if result["duplicate_submission"]:
        message = "This question was already recorded. Your score was not changed."
    elif result["correct"]:
        message = "Correct! Keep going."
    else:
        message = "Not quite. Review the lesson and try another question."
    return QuizAnswerResponse(**result, message=message)
