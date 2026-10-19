"""Context-aware, structured voice understanding with an optional local model."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from app.qa.ollama import OllamaProvider, OllamaUnavailableError
from app.voice.interpreter import Interpretation

ALLOWED_COMMANDS = {
    "OPEN_DASHBOARD", "OPEN_LESSON", "OPEN_QUIZ", "SHOW_PROGRESS", "GO_BACK",
    "START_LESSON", "SELECT_SUBJECT", "REPEAT", "READ_LESSON",
    "NEXT_SECTION",
    "READ_QUESTION", "SELECT_OPTION_A", "SELECT_OPTION_B", "SELECT_OPTION_C",
    "SELECT_OPTION_D", "NEXT_QUESTION", "SUBMIT_ANSWER", "STOP_SPEAKING",
    "STOP_LISTENING", "STOP", "CANCEL", "HELP", "CONFIRM",
}


@dataclass(frozen=True)
class Understanding:
    interpretation: Interpretation
    category: str
    response: str | None = None
    clarification: str | None = None


def _prompt(text: str, context: dict[str, Any]) -> str:
    return f"""You classify one learner voice request for a small educational app.
Return JSON only with exactly these keys:
category (application|learning|follow_up|clarification|unsupported),
command (one allowed command or null), confidence (0 to 1), response (short text or null),
clarification (short question or null).
Allowed commands: {", ".join(sorted(ALLOWED_COMMANDS))}.
Never invent commands, routes, answers, or facts. A learning question is not an application command.
For learning or follow_up requests, response must be a concise answer grounded only in the supplied
lesson/question context; if that context is insufficient, return clarification instead of guessing.
Use screen and recent turns to resolve words such as that, again, next, and back.
Request: {text}
Context: {json.dumps(context, separators=(",", ":"))}"""


def _parse(value: str, fallback: Interpretation) -> Understanding | None:
    value = value.strip()
    if value.startswith("```") and value.endswith("```"):
        value = value.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    try:
        data = json.loads(value)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    category = data.get("category")
    command = data.get("command")
    confidence = data.get("confidence")
    if category not in {"application", "learning", "follow_up", "clarification", "unsupported"}:
        return None
    if command is not None and command not in ALLOWED_COMMANDS:
        return None
    if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
        return None
    if command is not None and confidence < 0.7:
        command = None
        category = "clarification"
    interpretation = Interpretation(
        intent="command" if command else ("question" if category == "learning" else "unknown"),
        confidence=float(confidence),
        command=command,
        answer=None,
    )
    return Understanding(
        interpretation=interpretation,
        category=category,
        response=data.get("response") if isinstance(data.get("response"), str) else None,
        clarification=data.get("clarification") if isinstance(data.get("clarification"), str) else None,
    )


def understand(text: str, context: dict[str, Any], fallback: Interpretation, provider: OllamaProvider) -> Understanding:
    """Use the configured local model only after deterministic handling misses."""
    if not provider.configured:
        return Understanding(fallback, "learning" if fallback.intent == "question" else "unsupported")
    try:
        result = _parse(provider.answer(_prompt(text, context)), fallback)
    except OllamaUnavailableError:
        result = None
    return result or Understanding(
        Interpretation(intent="unknown", confidence=0.0),
        "clarification",
        clarification="I’m not sure what you want to do. Could you say that another way?",
    )
