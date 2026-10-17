"""Small rule-based interpreter; it is intentionally not an ML classifier."""

from dataclasses import dataclass
from typing import Literal

Intent = Literal["command", "quiz_answer", "question", "unknown"]

COMMANDS = {
    "start lesson": "START_LESSON",
    "start": "START_LESSON",
    "select subject": "SELECT_SUBJECT",
    "choose science": "SELECT_SUBJECT",
    "repeat": "REPEAT",
    "repeat that": "REPEAT",
    "next": "NEXT_QUESTION",
    "next question": "NEXT_QUESTION",
    "submit": "SUBMIT_ANSWER",
    "submit answer": "SUBMIT_ANSWER",
    "show progress": "SHOW_PROGRESS",
    "progress": "SHOW_PROGRESS",
    "help": "HELP",
    "stop": "STOP",
    "confirm": "CONFIRM",
    "cancel": "CANCEL",
}

QUESTION_STARTERS = ("what", "why", "how", "when", "where", "who", "which", "can you", "tell me")


@dataclass(frozen=True)
class Interpretation:
    intent: Intent
    confidence: float
    command: str | None = None
    answer: str | None = None


def interpret_text(text: str, active_quiz: bool) -> Interpretation:
    """Classify only clear commands, questions, or answers in an active quiz context."""
    cleaned = " ".join(text.strip().split())
    normalised = cleaned.casefold()
    if not cleaned:
        return Interpretation(intent="unknown", confidence=0.0)
    if normalised in COMMANDS:
        return Interpretation(intent="command", confidence=1.0, command=COMMANDS[normalised])
    if normalised.endswith("?") or normalised.startswith(QUESTION_STARTERS):
        return Interpretation(intent="question", confidence=0.9)
    if active_quiz and len(cleaned) >= 2 and normalised not in {"maybe", "i do not know", "not sure"}:
        return Interpretation(intent="quiz_answer", confidence=0.8, answer=cleaned)
    return Interpretation(intent="unknown", confidence=0.2)
