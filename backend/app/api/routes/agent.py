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
    print(f"\n{'-'*70}", flush=True)
    print(f"🤖  [AI BROWSER AGENT CALLED]: Prompt: \"{payload.prompt}\"", flush=True)
    response = agent_runtime.run(payload)
    print(f"🎯  [AGENT EXECUTION STATUS]: {response.status.upper()}", flush=True)
    if response.target_url:
        print(f"🌐  [WEBSITE NAVIGATING TO]: {response.target_url}", flush=True)
    print(f"🗣️  [WEBSITE RESPONDS TO USER]: \"{response.final_message}\"", flush=True)
    print(f"{'-'*70}\n", flush=True)
    return response
