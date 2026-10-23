"""Small rule-based interpreter; it is intentionally not an ML classifier."""

import re
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
    "show me progress": "SHOW_PROGRESS",
    "show me the progress": "SHOW_PROGRESS",
    "show the progress": "SHOW_PROGRESS",
    "progress": "SHOW_PROGRESS",
    "help": "HELP",
    "stop": "STOP",
    "stop speaking": "STOP_SPEAKING",
    "stop listening": "STOP_LISTENING",
    "confirm": "CONFIRM",
    "cancel": "CANCEL",
    "hint": "HINT",
    "give hint": "HINT",
    "give me a hint": "HINT",
    "need a hint": "HINT",
    "show hint": "HINT",
    "next concept": "NEXT_CONCEPT",
    "next idea": "NEXT_CONCEPT",
    "previous concept": "PREV_CONCEPT",
    "previous idea": "PREV_CONCEPT",
}

QUESTION_STARTERS = ("what", "why", "how", "when", "where", "who", "which", "can you tell me", "tell me")

ALIASES: tuple[tuple[str, str], ...] = (
    # Dashboard & Navigation
    ("open dashboard", "OPEN_DASHBOARD"),
    ("go to dashboard", "OPEN_DASHBOARD"),
    ("show dashboard", "OPEN_DASHBOARD"),
    ("open home", "OPEN_DASHBOARD"),
    ("go home", "OPEN_DASHBOARD"),
    ("take me home", "OPEN_DASHBOARD"),
    ("go to home screen", "OPEN_DASHBOARD"),
    ("back to main menu", "OPEN_DASHBOARD"),
    ("main menu", "OPEN_DASHBOARD"),
    ("open overview", "OPEN_DASHBOARD"),
    # Lessons & Concept Learning
    ("open science", "OPEN_LESSON"),
    ("open science lesson", "OPEN_LESSON"),
    ("start science", "OPEN_LESSON"),
    ("continue lesson", "OPEN_LESSON"),
    ("go to lesson", "OPEN_LESSON"),
    ("let's study science", "OPEN_LESSON"),
    ("open science chapter", "OPEN_LESSON"),
    ("continue learning", "OPEN_LESSON"),
    ("let's continue learning", "OPEN_LESSON"),
    ("keep learning", "OPEN_LESSON"),
    ("let's learn", "OPEN_LESSON"),
    ("resume lesson", "OPEN_LESSON"),
    ("resume learning", "OPEN_LESSON"),
    ("read lesson", "READ_LESSON"),
    ("read this lesson", "READ_LESSON"),
    ("read lesson aloud", "READ_LESSON"),
    ("read aloud", "READ_LESSON"),
    ("read this aloud", "READ_LESSON"),
    ("read it to me", "READ_LESSON"),
    ("narrate lesson", "READ_LESSON"),
    ("speak the concept", "READ_LESSON"),
    ("next concept", "NEXT_CONCEPT"),
    ("next idea", "NEXT_CONCEPT"),
    ("next point", "NEXT_CONCEPT"),
    ("forward", "NEXT_CONCEPT"),
    ("previous concept", "PREV_CONCEPT"),
    ("previous idea", "PREV_CONCEPT"),
    ("last point", "PREV_CONCEPT"),
    # Quiz & Practice
    ("open quiz", "OPEN_QUIZ"),
    ("start quiz", "OPEN_QUIZ"),
    ("begin quiz", "OPEN_QUIZ"),
    ("take quiz", "OPEN_QUIZ"),
    ("open test", "OPEN_QUIZ"),
    ("let's practice", "OPEN_QUIZ"),
    ("test my knowledge", "OPEN_QUIZ"),
    ("start the quiz", "OPEN_QUIZ"),
    ("quiz me", "OPEN_QUIZ"),
    ("practice quiz", "OPEN_QUIZ"),
    ("take a test", "OPEN_QUIZ"),
    ("practice questions", "OPEN_QUIZ"),
    ("english quiz", "OPEN_QUIZ"),
    ("math quiz", "OPEN_QUIZ"),
    ("mathematics quiz", "OPEN_QUIZ"),
    ("science quiz", "OPEN_QUIZ"),
    ("social science quiz", "OPEN_QUIZ"),
    ("social quiz", "OPEN_QUIZ"),
    ("quiz in english", "OPEN_QUIZ"),
    ("quiz in math", "OPEN_QUIZ"),
    ("quiz in mathematics", "OPEN_QUIZ"),
    ("quiz in science", "OPEN_QUIZ"),
    ("quiz in social science", "OPEN_QUIZ"),
    ("quiz in english subject", "OPEN_QUIZ"),
    ("quiz in math subject", "OPEN_QUIZ"),
    ("quiz in science subject", "OPEN_QUIZ"),
    ("quiz in social science subject", "OPEN_QUIZ"),
    ("open english quiz", "OPEN_QUIZ"),
    ("open math quiz", "OPEN_QUIZ"),
    ("open science quiz", "OPEN_QUIZ"),
    ("open social science quiz", "OPEN_QUIZ"),
    ("start english quiz", "OPEN_QUIZ"),
    ("start math quiz", "OPEN_QUIZ"),
    ("start science quiz", "OPEN_QUIZ"),
    ("start social science quiz", "OPEN_QUIZ"),
    ("take english quiz", "OPEN_QUIZ"),
    ("take math quiz", "OPEN_QUIZ"),
    ("take science quiz", "OPEN_QUIZ"),
    ("take social science quiz", "OPEN_QUIZ"),
    ("read question", "READ_QUESTION"),
    ("read this question", "READ_QUESTION"),
    ("repeat question", "READ_QUESTION"),
    ("read question again", "READ_QUESTION"),
    ("submit", "SUBMIT_ANSWER"),
    ("submit answer", "SUBMIT_ANSWER"),
    ("submit my answer", "SUBMIT_ANSWER"),
    ("submit this", "SUBMIT_ANSWER"),
    ("lock in my answer", "SUBMIT_ANSWER"),
    ("final answer", "SUBMIT_ANSWER"),
    ("next question", "NEXT_QUESTION"),
    ("another question", "NEXT_QUESTION"),
    ("move on", "NEXT_QUESTION"),
    ("next one", "NEXT_QUESTION"),
    # Hints (conversational + polite forms)
    ("hint", "HINT"),
    ("need a hint", "HINT"),
    ("give me a hint", "HINT"),
    ("give me a clue", "HINT"),
    ("could you give me a clue", "HINT"),
    ("could you give me a hint", "HINT"),
    ("can i get a hint", "HINT"),
    ("help me with this question", "HINT"),
    ("show hint", "HINT"),
    ("i need a hint", "HINT"),
    ("hint please", "HINT"),
    ("clue please", "HINT"),
    ("give clue", "HINT"),
    # Progress & Stats
    ("show my progress", "SHOW_PROGRESS"),
    ("show me progress", "SHOW_PROGRESS"),
    ("show me the progress", "SHOW_PROGRESS"),
    ("show the progress", "SHOW_PROGRESS"),
    ("see my progress", "SHOW_PROGRESS"),
    ("i want to see my progress", "SHOW_PROGRESS"),
    ("let's see my progress", "SHOW_PROGRESS"),
    ("open my progress", "SHOW_PROGRESS"),
    ("open progress", "SHOW_PROGRESS"),
    ("check my progress", "SHOW_PROGRESS"),
    ("show my score", "SHOW_PROGRESS"),
    ("how am i doing", "SHOW_PROGRESS"),
    ("how many points do i have", "SHOW_PROGRESS"),
    ("view my stats", "SHOW_PROGRESS"),
    ("show achievements", "SHOW_PROGRESS"),
    ("view progress", "SHOW_PROGRESS"),
    # Navigation & Control
    ("go back", "GO_BACK"),
    ("take me back", "GO_BACK"),
    ("previous page", "GO_BACK"),
    ("return", "GO_BACK"),
    ("back up", "GO_BACK"),
    ("repeat that", "REPEAT"),
    ("say that again", "REPEAT"),
    ("pardon", "REPEAT"),
    ("explain this again", "REPEAT"),
    ("can you explain that again", "REPEAT"),
    ("say it again", "REPEAT"),
    ("once more", "REPEAT"),
    # Quiz option reading
    ("what does option a say", "READ_QUESTION"),
    ("what does option b say", "READ_QUESTION"),
    ("what does option c say", "READ_QUESTION"),
    ("what does option d say", "READ_QUESTION"),
    ("read the choices", "READ_QUESTION"),
    ("read the options", "READ_QUESTION"),
    # Stop speaking / stop listening
    ("stop speaking", "STOP_SPEAKING"),
    ("stop talking", "STOP_SPEAKING"),
    ("be quiet", "STOP_SPEAKING"),
    ("hush", "STOP_SPEAKING"),
    ("mute voice", "STOP_SPEAKING"),
    ("stop listening", "STOP_LISTENING"),
    ("pause voice", "STOP_LISTENING"),
    ("cancel that", "CANCEL"),
    ("help me", "HELP"),
    ("what can i say", "HELP"),
    ("how do i use this", "HELP"),
    ("instructions", "HELP"),
)


def _normalise(text: str) -> str:
    text = text.casefold().replace("’", "'")
    return " ".join("".join(char if char.isalnum() or char == "'" else " " for char in text).split())


def _paraphrase_command(normalised: str) -> tuple[str, float] | None:
    normalised = normalised.removesuffix(" please").removesuffix(" now").strip()
    if normalised in {"help", "please help", "help me", "instructions"}:
        return "HELP", 1.0
    if normalised in {"start", "start lesson"}:
        return "START_LESSON", 1.0
    if normalised in {"select subject", "choose science"}:
        return "SELECT_SUBJECT", 1.0
    if normalised in {"next", "next question", "another question", "next one", "move on"}:
        return "NEXT_QUESTION", 1.0
    if normalised in {"next concept", "next idea", "next point", "forward"}:
        return "NEXT_CONCEPT", 1.0
    if normalised in {"previous concept", "prev concept", "previous idea", "last point"}:
        return "PREV_CONCEPT", 1.0
    if normalised in {
        "hint", "give hint", "give me a hint", "need a hint", "show hint",
        "give me a clue", "clue", "could you give me a clue", "could you give me a hint",
        "can i get a hint", "hint please", "clue please",
    }:
        return "HINT", 1.0
    if normalised in {
        "repeat", "repeat that", "say that again", "pardon",
        "explain this again", "can you explain that again", "say it again", "once more",
    }:
        return "REPEAT", 1.0
    if normalised in {
        "read question", "read this question", "repeat question",
        "read question again", "read the choices", "read the options",
        "what does option a say", "what does option b say",
        "what does option c say", "what does option d say",
    }:
        return "READ_QUESTION", 1.0
    if normalised in {"submit", "submit answer", "submit this", "lock in my answer", "final answer", "confirm"}:
        return "SUBMIT_ANSWER" if normalised != "confirm" else "CONFIRM", 1.0
    if normalised in {
        "show progress", "progress", "show my progress", "show me progress",
        "show me the progress", "show the progress", "see my progress",
        "i want to see my progress", "let's see my progress", "show my score",
        "view progress", "open progress", "open my progress",
    }:
        return "SHOW_PROGRESS", 1.0
    if normalised in {
        "continue learning", "let's continue learning", "keep learning",
        "resume lesson", "resume learning", "continue lesson",
    }:
        return "OPEN_LESSON", 1.0
    if normalised in {"stop", "stop speaking", "be quiet", "stop talking", "hush"}:
        return "STOP_SPEAKING" if normalised != "stop" else "STOP", 1.0
    if normalised == "cancel":
        return "CANCEL", 1.0

    # Specific unit/chapter requests must not be captured by generic parameterless commands
    if re.search(r"\b(?:unit|chapter)\s*(?:#|no\.?|number)?\s*[a-z0-9]+\b", normalised):
        return None

    # Letter choice detection (supports "option a", "pick b", "choose c", "letter d", "i think it's a")
    for letter in "abcd":
        choice_phrases = {
            f"select option {letter}",
            f"choose option {letter}",
            f"pick option {letter}",
            f"option {letter}",
            f"pick {letter}",
            f"choose {letter}",
            f"select {letter}",
            f"letter {letter}",
            f"it is {letter}",
            f"it's {letter}",
            f"its {letter}",
        }
        if normalised in choice_phrases:
            return f"SELECT_OPTION_{letter.upper()}", 0.98

    for phrase, command in ALIASES:
        if normalised == phrase:
            return command, 0.96

    # Politeness and conversational prefix stripping
    conversational_prefixes = (
        "no, ",
        "no ",
        "nah, ",
        "nah ",
        "okay, ",
        "okay ",
        "ok, ",
        "ok ",
        "well, ",
        "well ",
        "can you please ",
        "could you please ",
        "can you ",
        "could you ",
        "please ",
        "i want to ",
        "i'd like to ",
        "let me ",
        "i think it's ",
        "i think its ",
        "i choose ",
        "i pick ",
    )
    for prefix in conversational_prefixes:
        if normalised.startswith(prefix):
            stripped = normalised.removeprefix(prefix).strip()
            result = _paraphrase_command(stripped)
            if result:
                return result[0], min(result[1], 0.94)

    for prefix in ("open ", "go to ", "take me to ", "start ", "begin ", "launch "):
        if normalised.startswith(prefix):
            target = normalised[len(prefix):].removeprefix("the ").strip()
            if target in {"dashboard", "home", "main page", "main menu", "home screen"}:
                return "OPEN_DASHBOARD", 0.93
            if (
                target in {"quiz", "test", "questions", "practice"}
                or target.endswith(" quiz")
                or target.endswith(" test")
                or target.startswith("quiz in ")
                or "quiz" in target
            ):
                return "OPEN_QUIZ", 0.93
            if target in {"lesson", "science", "science lesson"}:
                return "OPEN_LESSON", 0.93

    if normalised.endswith(" quiz") or normalised.startswith("quiz in ") or normalised.endswith(" test"):
        return "OPEN_QUIZ", 0.95

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
