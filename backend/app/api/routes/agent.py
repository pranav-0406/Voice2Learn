"""FastAPI router for the AI Browser Agent runtime."""

from fastapi import APIRouter, Depends, status

from app.agent.runtime import AgentRuntime
from app.agent.schemas import AgentRunRequest, AgentRunResponse
from app.api.dependencies import get_agent_runtime

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/run", response_model=AgentRunResponse, status_code=status.HTTP_200_OK)
def run_browser_agent(
    payload: AgentRunRequest,
    agent_runtime: AgentRuntime = Depends(get_agent_runtime),
) -> AgentRunResponse:
    """Execute the AI Browser Agent loop for a student natural language prompt."""
    return agent_runtime.run(payload)
