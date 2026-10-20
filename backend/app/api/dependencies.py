"""Reusable FastAPI dependencies."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import get_settings
from app.core.security import decode_access_token
from app.db.database import Database

security_bearer = HTTPBearer(auto_error=False)


def get_database() -> Database:
    return Database(get_settings().database_path)


def get_current_student(
    auth: HTTPAuthorizationCredentials | None = Depends(security_bearer),
    database: Database = Depends(get_database),
) -> dict:
    if not auth or not auth.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_access_token(auth.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    student = database.get_student_by_id(payload["sub"])
    if not student:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Student not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return student


def get_curriculum_retriever(database: Database = Depends(get_database)):
    from app.qa.retriever import CurriculumRetriever
    return CurriculumRetriever(database)


def get_curriculum_assistant(
    retriever=Depends(get_curriculum_retriever),
):
    from app.qa.assistant import CurriculumAssistant
    return CurriculumAssistant(retriever)


def get_curriculum_resolver(database: Database = Depends(get_database)):
    from app.curriculum.resolver import CurriculumResolver
    return CurriculumResolver(database)


def get_agent_runtime(
    database: Database = Depends(get_database),
    resolver=Depends(get_curriculum_resolver),
    settings=Depends(get_settings),
):
    from app.agent.runtime import AgentRuntime
    return AgentRuntime(database=database, resolver=resolver, settings=settings)

