"""Readiness endpoint for local development and deployment checks."""

from typing import Literal, TypedDict

from fastapi import APIRouter

router = APIRouter(tags=["system"])


class HealthResponse(TypedDict):
    status: Literal["ok"]
    message: str
    stt_backend: Literal["not_configured"]
    llm_backend: Literal["not_configured"]
    retrieval_ready: bool


@router.get("/health", response_model=HealthResponse, summary="Check backend readiness")
def health_check() -> HealthResponse:
    """Report the backend state without overstating unavailable integrations."""
    return {
        "status": "ok",
        "message": "Voice2Learn backend is running",
        "stt_backend": "not_configured",
        "llm_backend": "not_configured",
        "retrieval_ready": False,
    }
