"""Agent Runtime Loop & Action Execution Engine powered by openai/gpt-oss-120b on Groq."""

from __future__ import annotations

import json
import logging
import re
import uuid
from typing import Any

from app.agent.schemas import (
    ActionType,
    AgentAction,
    AgentContext,
    AgentObservation,
    AgentRunRequest,
    AgentRunResponse,
    AgentStep,
)
from app.agent.tools import AGENT_TOOLS, parse_tool_call
from app.core.config import Settings, get_settings
from app.curriculum.resolver import CurriculumResolver
from app.db.database import Database

logger = logging.getLogger(__name__)

ALLOWED_EXACT_ROUTES = {"/dashboard", "/quiz", "/progress", "/login", "/register"}
ALLOWED_ROUTE_PREFIXES = ("/concept/",)


def is_valid_route(url: str | None) -> bool:
    """Validate that target navigation URL belongs to an allowed application screen."""
    if not url or not isinstance(url, str):
        return False
    clean = url.strip()
    if clean in ALLOWED_EXACT_ROUTES:
        return True
    if any(clean.startswith(p) for p in ALLOWED_ROUTE_PREFIXES):
        parts = clean.split("/")
        if len(parts) == 3 and parts[2].strip() and bool(re.match(r"^[a-zA-Z0-9_-]+$", parts[2])):
            return True
    return False


SYSTEM_PROMPT = """You are the Voice2Learn AI Browser Agent for Class 6 Tamil Nadu State Board (English-medium) students.
Your mission is to understand student natural-language requests and operate the website interface to help them learn.

Application Pages:
- Dashboard: `/dashboard`
- Interactive Concept Lessons: `/concept/:conceptId` (e.g., `/concept/sci-ch02-c01` for Science Unit 2: Force & Motion)
- Adaptive Quiz: `/quiz`
- Student Progress: `/progress`

Class 6 Curriculum Map:
- Science (7 units): Unit 1 (Measurements), Unit 2 (Force and Motion), Unit 3 (Matter Around Us), Unit 4 (The World of Plants), Unit 5 (The World of Animals), Unit 6 (Health and Hygiene), Unit 7 (Computer — An Introduction)
- Mathematics (6 units): Unit 1 (Numbers), Unit 2 (Introduction to Algebra), Unit 3 (Ratio and Proportion), Unit 4 (Geometry), Unit 5 (Statistics), Unit 6 (Information Processing)
- English (3 units): Unit 1 (Sea Turtles), Unit 2 (When the Trees Walked), Unit 3 (A Visitor from Distant Lands)
- Social Science (8 units): Unit 1 (What is History?), Unit 2 (Human Evolution), Unit 3 (Indus Civilisation), Unit 4 (Ancient Cities of Tamilagam), Unit 5 (The Universe and Solar System), Unit 6 (Land and Oceans), Unit 7 (Understanding Diversity), Unit 8 (Achieving Equality)

Operating Rules:
1. Always resolve curriculum units accurately: When a student asks for a unit (e.g., "Go to Science Unit 2 and start where I left off"), call `resolve_curriculum` first.
2. If the student asks to "start where I left off" and has an active position in that subject, prioritize their saved active concept.
3. If a requested unit does NOT exist (e.g. Science Unit 99), do NOT invent or guess another lesson. Call `complete_task` or `ask_clarification` explaining honestly what units exist.
4. Keep spoken messages encouraging, warm, and appropriate for an 11-year-old Class 6 student in simple English.
5. Use `navigate` to switch pages. When the final page is reached, call `complete_task`.
"""


class AgentRuntime:
    """Executes the agent reasoning and action loop."""

    def __init__(
        self,
        database: Database,
        resolver: CurriculumResolver,
        settings: Settings | None = None,
    ) -> None:
        self.database = database
        self.resolver = resolver
        self.settings = settings or get_settings()

    def _get_groq_client(self) -> Any:
        if not self.settings.groq_api_key:
            return None
        try:
            from groq import Groq
            return Groq(
                api_key=self.settings.groq_api_key,
                timeout=float(self.settings.groq_timeout_seconds),
            )
        except Exception as exc:
            logger.warning("Failed to initialize Groq client for agent: %s", exc)
            return None

    def execute_curriculum_resolution(self, args: dict[str, Any]) -> dict[str, Any]:
        """Resolve curriculum entity against real SQLite database."""
        subject = args.get("subject", "")
        unit_number = args.get("unit_number")
        topic_query = args.get("topic_query")

        resolved = self.resolver.resolve(
            query=topic_query,
            subject=subject,
            unit_number=unit_number,
        )
        return {
            "found": resolved.found,
            "subject_id": resolved.subject_id,
            "subject_name": resolved.subject_name,
            "chapter_id": resolved.chapter_id,
            "chapter_title": resolved.chapter_title,
            "chapter_number": resolved.chapter_number,
            "concept_id": resolved.concept_id,
            "target_url": resolved.target_url,
            "error": resolved.error,
            "available_units": resolved.available_units,
        }

    def run(self, request: AgentRunRequest) -> AgentRunResponse:
        """Run the multi-step reasoning and action loop."""
        run_id = f"run_{uuid.uuid4().hex[:8]}"
        client = self._get_groq_client()
        model = self.settings.groq_agent_model

        # Fallback if no Groq client configured (e.g. offline testing)
        if not client:
            return self._fallback_rule_execution(run_id, request)

        # Retrieve active learner position from DB if available
        active_pos = self.database.get_active_position(request.context.learner_id)
        context_description = (
            f"Current URL: {request.context.current_url}\n"
            f"Page Title: {request.context.page_title}\n"
            f"Learner Active Position: {json.dumps(active_pos) if active_pos else 'None'}\n"
            f"Interactive Elements visible: {len(request.context.interactive_elements)}"
        )

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Student Request: {request.prompt}\n\n"
                    f"Browser State:\n{context_description}"
                ),
            },
        ]

        steps: list[AgentStep] = []
        final_message = ""
        target_url: str | None = None
        status = "completed"

        for step_idx in range(1, request.max_steps + 1):
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    tools=AGENT_TOOLS,
                    tool_choice="auto",
                    temperature=0.1,
                )
            except Exception as exc:
                logger.error("Groq agent call failed: %s", exc)
                return self._fallback_rule_execution(run_id, request)

            msg = response.choices[0].message
            tool_calls = getattr(msg, "tool_calls", None)

            # If model returned text instead of a tool call
            if not tool_calls:
                thought = msg.content or "Processing student request"
                action = AgentAction(
                    action_type=ActionType.COMPLETE_TASK,
                    thought=thought,
                    message=thought,
                    success=True,
                )
                step = AgentStep(
                    step_number=step_idx,
                    thought=thought,
                    action=action,
                )
                steps.append(step)
                final_message = thought
                break

            # Handle the tool call
            tool_call = tool_calls[0]
            func_name = tool_call.function.name
            func_args_str = tool_call.function.arguments

            # Case A: Internal curriculum resolution tool
            if func_name == "resolve_curriculum":
                try:
                    args = json.loads(func_args_str)
                except Exception:
                    args = {}
                resolution_result = self.execute_curriculum_resolution(args)

                # Feed resolution result back to model in conversation
                messages.append(msg)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": "resolve_curriculum",
                    "content": json.dumps(resolution_result),
                })

                # Check if student already had active position for this subject
                if resolution_result.get("found"):
                    sub_id = resolution_result.get("subject_id")
                    pos = self.database.get_active_position(request.context.learner_id, subject_id=sub_id)
                    if pos and "start where i left off" in request.prompt.lower():
                        resolution_result["concept_id"] = pos["concept_id"]
                        resolution_result["target_url"] = f"/concept/{pos['concept_id']}"
                        resolution_result["resumed_position"] = True

                    # Route safety validation
                    resolved_target = resolution_result.get("target_url")
                    if not is_valid_route(resolved_target):
                        resolution_result["found"] = False
                        resolution_result["error"] = f"Resolved route '{resolved_target}' failed safety validation."
                        resolution_result["target_url"] = None

                action = AgentAction(
                    action_type=ActionType.NAVIGATE if resolution_result.get("found") else ActionType.ASK_CLARIFICATION,
                    thought=f"Resolved curriculum query for {args.get('subject')} Unit {args.get('unit_number')}",
                    target_url=resolution_result.get("target_url"),
                    message=resolution_result.get("error"),
                    success=resolution_result.get("found", False),
                )
                step = AgentStep(
                    step_number=step_idx,
                    thought=action.thought,
                    action=action,
                    observation=AgentObservation(
                        action_type=action.action_type,
                        success=resolution_result.get("found", False),
                        current_url=request.context.current_url,
                        page_title=request.context.page_title,
                        visible_text_snippet=resolution_result.get("chapter_title"),
                        error=resolution_result.get("error"),
                    ),
                )
                steps.append(step)

                # If entity was not found, complete with honest clarification
                if not resolution_result.get("found"):
                    final_message = resolution_result.get("error") or "That unit does not exist in our curriculum."
                    status = "needs_clarification"
                    target_url = None
                    break

                target_url = resolution_result.get("target_url")
                continue

            # Case B: Standard browser actions
            action = parse_tool_call(func_name, func_args_str)
            step = AgentStep(
                step_number=step_idx,
                thought=action.thought,
                action=action,
            )
            steps.append(step)

            if action.action_type == ActionType.NAVIGATE:
                if not is_valid_route(action.target_url):
                    action.success = False
                    final_message = f"I cannot navigate to {action.target_url} because it is not an allowed lesson route."
                    status = "failed"
                    step.observation = AgentObservation(
                        action_type=ActionType.NAVIGATE,
                        success=False,
                        current_url=request.context.current_url,
                        page_title=request.context.page_title,
                        error=final_message,
                    )
                    target_url = None
                    break

                target_url = action.target_url
                # Simulate observation of navigation
                step.observation = AgentObservation(
                    action_type=ActionType.NAVIGATE,
                    success=True,
                    current_url=action.target_url or request.context.current_url,
                    page_title="Loaded Page",
                )
                messages.append(msg)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": func_name,
                    "content": json.dumps({"status": "navigated", "url": action.target_url}),
                })

            elif action.action_type == ActionType.COMPLETE_TASK:
                final_message = action.message or "I have opened that lesson for you."
                status = "completed" if action.success else "failed"
                break

            elif action.action_type == ActionType.ASK_CLARIFICATION:
                final_message = action.message or "Could you clarify which lesson you would like to open?"
                status = "needs_clarification"
                break

            else:
                messages.append(msg)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": func_name,
                    "content": json.dumps({"status": "executed"}),
                })

        if not final_message and steps:
            last_action = steps[-1].action
            final_message = last_action.message or f"Completed action {last_action.action_type.value}."

        return AgentRunResponse(
            run_id=run_id,
            status=status,
            steps=steps,
            final_message=final_message,
            target_url=target_url,
            total_steps=len(steps),
        )

    def _fallback_rule_execution(self, run_id: str, request: AgentRunRequest) -> AgentRunResponse:
        """Deterministic fallback when Groq LLM API is unavailable."""
        prompt_lower = request.prompt.lower()

        # Quiz request
        if "quiz" in prompt_lower:
            action = AgentAction(
                action_type=ActionType.NAVIGATE,
                thought="Student requested adaptive quiz",
                target_url="/quiz",
            )
            return AgentRunResponse(
                run_id=run_id,
                status="completed",
                steps=[
                    AgentStep(step_number=1, thought=action.thought, action=action),
                    AgentStep(
                        step_number=2,
                        thought="Task complete",
                        action=AgentAction(
                            action_type=ActionType.COMPLETE_TASK,
                            thought="Navigated to quiz",
                            message="Here is your adaptive quiz. Let's practice!",
                            success=True,
                        ),
                    ),
                ],
                final_message="Here is your adaptive quiz. Let's practice!",
                target_url="/quiz",
                total_steps=2,
            )

        # Dashboard / Home request
        if any(w in prompt_lower for w in ("dashboard", "home", "main menu")):
            action = AgentAction(
                action_type=ActionType.NAVIGATE,
                thought="Student requested dashboard",
                target_url="/dashboard",
            )
            return AgentRunResponse(
                run_id=run_id,
                status="completed",
                steps=[
                    AgentStep(step_number=1, thought=action.thought, action=action),
                    AgentStep(
                        step_number=2,
                        thought="Task complete",
                        action=AgentAction(
                            action_type=ActionType.COMPLETE_TASK,
                            thought="Navigated to dashboard",
                            message="Here is your main dashboard.",
                            success=True,
                        ),
                    ),
                ],
                final_message="Here is your main dashboard.",
                target_url="/dashboard",
                total_steps=2,
            )

        # Progress request
        if "progress" in prompt_lower or "score" in prompt_lower or "stats" in prompt_lower:
            action = AgentAction(
                action_type=ActionType.NAVIGATE,
                thought="Student requested progress view",
                target_url="/progress",
            )
            return AgentRunResponse(
                run_id=run_id,
                status="completed",
                steps=[
                    AgentStep(step_number=1, thought=action.thought, action=action),
                    AgentStep(
                        step_number=2,
                        thought="Task complete",
                        action=AgentAction(
                            action_type=ActionType.COMPLETE_TASK,
                            thought="Navigated to progress",
                            message="Here is your learning progress and scores.",
                            success=True,
                        ),
                    ),
                ],
                final_message="Here is your learning progress and scores.",
                target_url="/progress",
                total_steps=2,
            )

        # General continue / resume learning request (no specific unit given)
        if (
            not re.search(r"\b(?:unit|chapter)\b", prompt_lower)
            and any(w in prompt_lower for w in ("continue", "where i left off", "resume", "keep learning"))
        ):
            pos = self.database.get_active_position(request.context.learner_id)
            concept_url = f"/concept/{pos['concept_id']}" if pos and pos.get("concept_id") else "/concept/sci-ch01-c01"
            if is_valid_route(concept_url):
                msg = (
                    "Welcome back! Let's continue right where you left off."
                    if pos
                    else "Let's continue learning! Opening your first lesson."
                )
                step1 = AgentStep(
                    step_number=1,
                    thought="Resuming learner position",
                    action=AgentAction(
                        action_type=ActionType.NAVIGATE,
                        thought="Navigating to active concept",
                        target_url=concept_url,
                    ),
                )
                step2 = AgentStep(
                    step_number=2,
                    thought="Speaking confirmation to student",
                    action=AgentAction(
                        action_type=ActionType.COMPLETE_TASK,
                        thought="Finished navigation",
                        message=msg,
                        success=True,
                    ),
                )
                return AgentRunResponse(
                    run_id=run_id,
                    status="completed",
                    steps=[step1, step2],
                    final_message=msg,
                    target_url=concept_url,
                    total_steps=2,
                )

        # Curriculum resolution
        resolved = self.resolver.resolve(query=request.prompt)
        if resolved.found:
            concept_url = resolved.target_url or f"/concept/{resolved.concept_id}"

            # Check if student requested to start where left off
            if "where i left off" in prompt_lower or "continue" in prompt_lower:
                pos = self.database.get_active_position(
                    request.context.learner_id,
                    subject_id=resolved.subject_id,
                )
                if pos and pos.get("concept_id"):
                    concept_url = f"/concept/{pos['concept_id']}"

            if is_valid_route(concept_url):
                step1 = AgentStep(
                    step_number=1,
                    thought=f"Resolved to {resolved.subject_name} Chapter {resolved.chapter_number}: {resolved.chapter_title}",
                    action=AgentAction(
                        action_type=ActionType.NAVIGATE,
                        thought="Navigating to concept lesson",
                        target_url=concept_url,
                    ),
                )
                step2 = AgentStep(
                    step_number=2,
                    thought="Speaking confirmation to student",
                    action=AgentAction(
                        action_type=ActionType.COMPLETE_TASK,
                        thought="Finished navigation",
                        message=f"I have opened {resolved.subject_name} {resolved.chapter_title} for you. Ready to learn!",
                        success=True,
                    ),
                )
                return AgentRunResponse(
                    run_id=run_id,
                    status="completed",
                    steps=[step1, step2],
                    final_message=step2.action.message or "Lesson opened.",
                    target_url=concept_url,
                    total_steps=2,
                )

        # Not found / honest error
        error_msg = resolved.error or "I could not find that lesson in our Class 6 curriculum."
        return AgentRunResponse(
            run_id=run_id,
            status="needs_clarification",
            steps=[
                AgentStep(
                    step_number=1,
                    thought="Curriculum query was not found or invalid",
                    action=AgentAction(
                        action_type=ActionType.ASK_CLARIFICATION,
                        thought="Explaining available units to student",
                        message=error_msg,
                        success=False,
                    ),
                )
            ],
            final_message=error_msg,
            target_url=None,
            total_steps=1,
        )
