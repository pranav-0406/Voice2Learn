"""Available subject endpoints."""

from fastapi import APIRouter, Depends

from app.api.dependencies import get_database
from app.api.schemas import SubjectsResponse
from app.db.database import Database

router = APIRouter(tags=["learning"])


@router.get("/subjects", response_model=SubjectsResponse)
def list_subjects(database: Database = Depends(get_database)) -> SubjectsResponse:
    """List subjects with seeded English learning content."""
    return SubjectsResponse(subjects=database.list_subjects())
