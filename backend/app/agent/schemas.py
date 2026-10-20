"""Pydantic schemas for the Voice2Learn Browser Agent Runtime."""

from __future__ import annotations

from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class ActionType(str, Enum):
    NAVIGATE = "navigate"
    CLICK = "click"
    SCROLL = "scroll"
    READ_ALOUD = "read_aloud"
    SPEAK_TO_USER = "speak_to_user"
    COMPLETE_TASK = "complete_task"
    ASK_CLARIFICATION = "ask_clarification"


class AgentAction(BaseModel):
    action_type: ActionType
    thought: str = Field(..., description="Agent internal reasoning for choosing this action")
    target_url: str | None = None
    selector: str | None = None
    element_text: str | None = None
    scroll_direction: str | None = None
    text_to_speak: str | None = None
    message: str | None = None
    success: bool = True


class AgentObservation(BaseModel):
    action_type: ActionType
    success: bool
    current_url: str
    page_title: str
    visible_text_snippet: str | None = None
    error: str | None = None


class AgentContext(BaseModel):
    learner_id: str = "demo-learner"
    current_url: str = "/dashboard"
    page_title: str = "Dashboard"
    dom_summary: str | None = None
    interactive_elements: list[dict[str, Any]] = Field(default_factory=list)
    active_position: dict[str, Any] | None = None


class AgentStep(BaseModel):
    step_number: int
    thought: str
    action: AgentAction
    observation: AgentObservation | None = None


class AgentRunRequest(BaseModel):
    prompt: str
    context: AgentContext = Field(default_factory=AgentContext)
    max_steps: int = 5


class AgentRunResponse(BaseModel):
    run_id: str
    status: str  # "completed", "needs_clarification", "failed"
    steps: list[AgentStep]
    final_message: str
    target_url: str | None = None
    total_steps: int
