"""Small rule-based interpreter; it is intentionally not an ML classifier."""

import string
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Literal

Intent = Literal["command", "quiz_answer", "question", "unknown"]

COMMANDS = {
    "open dashboard": "OPEN_DASHBOARD",
    "open science": "OPEN_LESSON",
    "open lesson": "OPEN_LESSON",
    "go to lesson": "OPEN_LESSON",
    "open quiz": "OPEN_QUIZ",
    "start quiz": "OPEN_QUIZ",
    "show my progress": "SHOW_PROGRESS",
    "go back": "GO_BACK",
    "start lesson": "START_LESSON",
    "start": "START_LESSON",
    "select subject": "SELECT_SUBJECT",
    "choose science": "SELECT_SUBJECT",
    "repeat": "REPEAT",
    "repeat that": "REPEAT",
    "read lesson aloud": "READ_LESSON",
    "read lesson": "READ_LESSON",
    "next section": "NEXT_SECTION",
    "read question": "READ_QUESTION",
    "repeat question": "READ_QUESTION",
    "select option a": "SELECT_OPTION_A",
    "select option b": "SELECT_OPTION_B",
    "select option c": "SELECT_OPTION_C",
    "select option d": "SELECT_OPTION_D",
    "next": "NEXT_QUESTION",
    "next question": "NEXT_QUESTION",
    "submit": "SUBMIT_ANSWER",
    "submit answer": "SUBMIT_ANSWER",
    "show progress": "SHOW_PROGRESS",
    "progress": "SHOW_PROGRESS",
    "help": "HELP",
    "stop": "STOP",
    "stop speaking": "STOP_SPEAKING",
    "stop listening": "STOP_LISTENING",
    "confirm": "CONFIRM",
    "cancel": "CANCEL",
}

QUESTION_STARTERS = ("what", "why", "how", "when", "where", "who", "which", "can you", "tell me")

ALIASES: tuple[tuple[str, str], ...] = (
    ("open dashboard", "OPEN_DASHBOARD"),
    ("go to dashboard", "OPEN_DASHBOARD"),
    ("show dashboard", "OPEN_DASHBOARD"),
    ("open home", "OPEN_DASHBOARD"),
    ("go home", "OPEN_DASHBOARD"),
    ("open science", "OPEN_LESSON"),
    ("open science lesson", "OPEN_LESSON"),
    ("start science", "OPEN_LESSON"),
    ("continue lesson", "OPEN_LESSON"),
    ("go to lesson", "OPEN_LESSON"),
    ("open quiz", "OPEN_QUIZ"),
    ("start quiz", "OPEN_QUIZ"),
    ("begin quiz", "OPEN_QUIZ"),
    ("take quiz", "OPEN_QUIZ"),
    ("open test", "OPEN_QUIZ"),
    ("show my progress", "SHOW_PROGRESS"),
    ("check my progress", "SHOW_PROGRESS"),
    ("show my score", "SHOW_PROGRESS"),
    ("how am i doing", "SHOW_PROGRESS"),
    ("go back", "GO_BACK"),
    ("take me back", "GO_BACK"),
    ("previous page", "GO_BACK"),
    ("read lesson", "READ_LESSON"),
    ("read this lesson", "READ_LESSON"),
    ("read question", "READ_QUESTION"),
    ("read this question", "READ_QUESTION"),
    ("repeat that", "REPEAT"),
    ("say that again", "REPEAT"),
    ("repeat question", "READ_QUESTION"),
    ("stop speaking", "STOP_SPEAKING"),
    ("stop talking", "STOP_SPEAKING"),
    ("be quiet", "STOP_SPEAKING"),
    ("stop listening", "STOP_LISTENING"),
    ("cancel that", "CANCEL"),
    ("help me", "HELP"),
    ("what can i say", "HELP"),
)


def _normalise(text: str) -> str:
    text = text.casefold().replace("’", "'")
    return " ".join("".join(char if char.isalnum() or char == "'" else " " for char in text).split())


def _paraphrase_command(normalised: str) -> tuple[str, float] | None:
    normalised = normalised.removesuffix(" please").strip()
    if normalised in {"help", "please help"}:
        return "HELP", 1.0
    if normalised in {"start", "start lesson"}:
        return "START_LESSON", 1.0
    if normalised in {"select subject", "choose science"}:
        return "SELECT_SUBJECT", 1.0
    if normalised in {"repeat"}:
        return "REPEAT", 1.0
    if normalised in {"next", "next question"}:
        return "NEXT_QUESTION", 1.0
    if normalised in {"submit", "submit answer", "confirm"}:
        return "SUBMIT_ANSWER" if normalised != "confirm" else "CONFIRM", 1.0
    if normalised in {"show progress", "progress"}:
        return "SHOW_PROGRESS", 1.0
    if normalised == "stop":
        return "STOP", 1.0
    if normalised == "cancel":
        return "CANCEL", 1.0
    for letter in "abcd":
        if normalised in {f"select option {letter}", f"choose option {letter}", f"pick option {letter}", f"option {letter}"}:
            return f"SELECT_OPTION_{letter.upper()}", 0.98
    for phrase, command in ALIASES:
        if normalised == phrase:
            return command, 0.96
    for prefix in ("can you ", "could you ", "please "):
        if normalised.startswith(prefix):
            stripped = normalised.removeprefix(prefix)
            result = _paraphrase_command(stripped)
            if result:
                return result[0], min(result[1], 0.94)
    for prefix in ("open ", "go to ", "take me to ", "start ", "begin ", "launch "):
        if normalised.startswith(prefix):
            target = normalised[len(prefix):].removeprefix("the ").strip()
            if target in {"dashboard", "home", "main page"}:
                return "OPEN_DASHBOARD", 0.93
            if target in {"quiz", "test", "questions"}:
                return "OPEN_QUIZ", 0.93
            if target in {"lesson", "science", "science lesson"}:
                return "OPEN_LESSON", 0.93
    candidates_by_command: dict[str, float] = {}
    for phrase, command in tuple(COMMANDS.items()) + ALIASES:
        if len(normalised) >= 4 and len(phrase) >= 4:
            score = SequenceMatcher(None, normalised, phrase).ratio()
            candidates_by_command[command] = max(candidates_by_command.get(command, 0), score)
    candidates = sorted(((score, command) for command, score in candidates_by_command.items()), reverse=True)
    if candidates and candidates[0][0] >= 0.84 and (
        len(candidates) == 1 or candidates[0][0] - candidates[1][0] >= 0.04
    ):
        return candidates[0][1], 0.84
    return None


@dataclass(frozen=True)
class Interpretation:
    intent: Intent
    confidence: float
    command: str | None = None
    answer: str | None = None


def interpret_text(text: str, active_quiz: bool) -> Interpretation:
    """Classify only clear commands, questions, or answers in an active quiz context."""
    cleaned = " ".join(text.strip().split())
    normalised = _normalise(cleaned).strip(string.punctuation + " ")
    if not cleaned:
        return Interpretation(intent="unknown", confidence=0.0)
    command = _paraphrase_command(normalised)
    if command:
        return Interpretation(intent="command", confidence=command[1], command=command[0])
    if cleaned.rstrip().endswith("?") or normalised.startswith(QUESTION_STARTERS):
        return Interpretation(intent="question", confidence=0.9)
    if active_quiz and len(cleaned) >= 2 and normalised not in {"maybe", "i do not know", "not sure"}:
        return Interpretation(intent="quiz_answer", confidence=0.8, answer=cleaned)
    return Interpretation(intent="unknown", confidence=0.2)
