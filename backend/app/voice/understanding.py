"""Context-aware, structured voice understanding with optional local or cloud LLM fallback."""

from __future__ import annotations

import json
import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Protocol

from app.core.config import Settings, get_settings
from app.qa.ollama import OllamaProvider, OllamaUnavailableError
from app.qa.groq import GroqLLMProvider, LanguageModelUnavailableError
from app.voice.interpreter import Interpretation

logger = logging.getLogger(__name__)

ALLOWED_COMMANDS = {
    "OPEN_DASHBOARD", "OPEN_LESSON", "OPEN_QUIZ", "SHOW_PROGRESS", "GO_BACK",
    "START_LESSON", "SELECT_SUBJECT", "REPEAT", "READ_LESSON",
    "NEXT_SECTION",
    "READ_QUESTION", "SELECT_OPTION_A", "SELECT_OPTION_B", "SELECT_OPTION_C",
    "SELECT_OPTION_D", "NEXT_QUESTION", "SUBMIT_ANSWER", "STOP_SPEAKING",
    "STOP_LISTENING", "STOP", "CANCEL", "HELP", "CONFIRM",
    "HINT", "GIVE_HINT", "NEXT_CONCEPT", "PREV_CONCEPT",
}

QUIZ_ONLY_COMMANDS = {
    "SELECT_OPTION_A", "SELECT_OPTION_B", "SELECT_OPTION_C", "SELECT_OPTION_D",
    "SUBMIT_ANSWER", "NEXT_QUESTION", "HINT", "GIVE_HINT", "READ_QUESTION",
}

LESSON_ONLY_COMMANDS = {
    "NEXT_CONCEPT", "PREV_CONCEPT", "READ_LESSON",
}

NOISE_PHRASES = {
    "uh",
    "um",
    "hmm",
    "hm",
    "mm",
    "mm hmm",
    "uh huh",
    "okay",
    "ok",
    "yeah",
    "yep",
    "nope",
    "hello",
    "hi",
    "background noise",
}


def is_likely_noise(text: str, active_quiz: bool = False) -> bool:
    """Reject short conversational/filler transcripts before optional AI routing."""
    if active_quiz:
        return False
    cleaned = " ".join(text.casefold().split()).strip(" .,!?")
    if not cleaned:
        return True
    if cleaned in NOISE_PHRASES:
        return True
    words = cleaned.split()
    return len(words) <= 2 and all(word in {"uh", "um", "hmm", "hm", "mm", "okay", "ok", "yeah"} for word in words)


class LanguageModelProvider(Protocol):
    """Protocol for optional language model fallback engines."""

    @property
    def configured(self) -> bool: ...
    def answer(self, prompt: str) -> str: ...


class NullLLMProvider:
    """Safe no-op provider when no LLM is configured."""

    @property
    def configured(self) -> bool:
        return False

    def answer(self, prompt: str) -> str:
        raise LanguageModelUnavailableError("No language model provider configured")


def get_default_llm_provider(settings: Settings | None = None) -> LanguageModelProvider:
    """Select the first configured LLM provider (Ollama if configured, else Groq, else Null)."""
    cfg = settings or get_settings()
    ollama = OllamaProvider(cfg)
    if ollama.configured:
        return ollama
    groq_llm = GroqLLMProvider(cfg)
    if groq_llm.configured:
        return groq_llm
    return NullLLMProvider()


@dataclass(frozen=True)
class Understanding:
    interpretation: Interpretation
    category: str
    response: str | None = None
    clarification: str | None = None
    source: Any | None = None


@dataclass(frozen=True)
class IntentClassification:
    label: str
    confidence: float
    command: str | None = None


def _is_command_valid_in_context(command: str | None, context: dict[str, Any]) -> bool:
    """Validate that the requested command is legal in the current application screen state."""
    if command is None:
        return True
    if command not in ALLOWED_COMMANDS:
        return False

    active_quiz = bool(context.get("active_quiz"))
    screen = str(context.get("screen", "")).strip().casefold()
    is_quiz = active_quiz or "/quiz" in screen
    is_lesson = "/lesson" in screen or "/concept" in screen

    if command in QUIZ_ONLY_COMMANDS and not is_quiz:
        return False
    if command in LESSON_ONLY_COMMANDS and not is_lesson:
        return False
    return True


def _classifier_prompt(text: str, context: dict[str, Any]) -> str:
    classifier_context = {
        "transcript": text,
        "active_quiz": bool(context.get("active_quiz")),
        "screen": context.get("screen", "unknown"),
        "question": context.get("question"),
        "lesson_topic": context.get("lesson_topic"),
    }
    return f"""Classify one voice transcript for Voice2Learn.
Return JSON only with exactly these keys: label, confidence, command.
label must be one of: command, quiz_answer, educational_question, unrelated_speech, uncertain.
confidence must be a number from 0 to 1.
command must be one of the allowed command IDs or null. Never execute anything.
Do not assume quizzes are multiple choice: single letters, numbers, subject terms,
and short free-text phrases are valid quiz answers when a quiz is active.
Unrelated conversation, TV dialogue, or chatter is unrelated_speech.
Allowed commands: {", ".join(sorted(ALLOWED_COMMANDS))}.
Input context: {json.dumps(classifier_context, separators=(",", ":"))}"""


def _call_provider_with_timeout(provider: LanguageModelProvider, prompt: str, timeout: int) -> str:
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(provider.answer, prompt)
    try:
        return future.result(timeout=timeout)
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


def classify_intent(
    text: str,
    context: dict[str, Any],
    provider: LanguageModelProvider | None,
    timeout: int,
) -> IntentClassification | None:
    """Run the opt-in classifier and fail closed for every invalid result."""
    if not text.strip() or provider is None:
        return None
    try:
        if not provider.configured:
            return None
        raw = _call_provider_with_timeout(provider, _classifier_prompt(text, context), timeout)
        data = json.loads(raw.strip())
        if not isinstance(data, dict):
            return None
        label = data.get("label")
        confidence = data.get("confidence")
        command = data.get("command")
        if label not in {"command", "quiz_answer", "educational_question", "unrelated_speech", "uncertain"}:
            return None
        if not isinstance(confidence, (int, float)) or isinstance(confidence, bool) or not 0 <= confidence <= 1:
            return None
        if command is not None and (
            not isinstance(command, str)
            or command not in ALLOWED_COMMANDS
            or not _is_command_valid_in_context(command, context)
        ):
            return None
        return IntentClassification(label=label, confidence=float(confidence), command=command)
    except Exception:
        return None


def resolve_with_classifier(
    text: str,
    context: dict[str, Any],
    deterministic: Interpretation,
    provider: LanguageModelProvider | None,
    timeout: int,
    assistant: Any | None = None,
) -> Understanding:
    """Verify deterministic quiz answers and commands without executing actions."""
    if deterministic.intent == "quiz_answer":
        result = classify_intent(text, context, provider, timeout)
        if result is not None and result.label == "unrelated_speech" and result.confidence >= 0.7:
            return Understanding(
                Interpretation(intent="noise", confidence=0.0),
                "noise",
            )
        if result is None or result.confidence < 0.7 or result.label == "uncertain":
            return Understanding(
                Interpretation(intent="unknown", confidence=0.0),
                "clarification",
                clarification="I didn't catch that as an answer. Could you say it again?",
            )
        if result.label == "quiz_answer" and context.get("active_quiz") is True:
            return Understanding(deterministic, "application")
        if result.label == "educational_question" and result.confidence >= 0.7:
            return understand(
                text,
                context,
                Interpretation(intent="question", confidence=0.9),
                provider,
                assistant=assistant,
            )
        if result.label == "command" and result.confidence >= 0.7 and result.command:
            return Understanding(
                Interpretation(intent="command", confidence=result.confidence, command=result.command),
                "application",
            )
        return Understanding(
            Interpretation(intent="unknown", confidence=0.0),
            "clarification",
            clarification="I didn't catch that as an answer. Could you say it again?",
        )

    if deterministic.intent != "command":
        return Understanding(deterministic, "unsupported")

    if not _is_command_valid_in_context(deterministic.command, context):
        return Understanding(
            Interpretation(intent="unknown", confidence=0.0),
            "clarification",
            clarification="That command is not available on this screen. Say 'help' for available actions.",
        )

    result = classify_intent(text, context, provider, timeout)
    if result is None or result.confidence < 0.7 or result.label in {"uncertain", "unrelated_speech"}:
        return Understanding(deterministic, "application")
    if result.label == "command" and result.command == deterministic.command:
        return Understanding(deterministic, "application")
    if result.label == "command" and result.command and result.command != deterministic.command:
        return Understanding(
            Interpretation(intent="unknown", confidence=0.0),
            "clarification",
            clarification=f"Did you mean {deterministic.command.replace('_', ' ').lower()} or {result.command.replace('_', ' ').lower()}?",
        )
    return Understanding(deterministic, "application")


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


def _parse(value: str, fallback: Interpretation, context: dict[str, Any] | None = None) -> Understanding | None:
    value = value.strip()
    if value.startswith("```") and value.endswith("```"):
        value = value.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    ctx = context or {}
    try:
        data = json.loads(value)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None

    category = data.get("category")
    command = data.get("command")
    confidence = data.get("confidence")

    if category not in {"application", "learning", "follow_up", "clarification", "unsupported", "noise"}:
        return None
    if command is not None and command not in ALLOWED_COMMANDS:
        return None
    if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
        return None

    # Contextual safety validation: prevent model from executing commands invalid on current screen
    if command is not None and not _is_command_valid_in_context(command, ctx):
        logger.info("llm_command_disallowed_by_context command=%s context=%s", command, context)
        command = None
        category = "clarification"
        return Understanding(
            interpretation=Interpretation(intent="unknown", confidence=0.0),
            category="clarification",
            clarification="That command is not available on this screen. Say 'help' for available actions.",
        )

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

def understand(
    text: str,
    context: dict[str, Any],
    fallback: Interpretation,
    provider: LanguageModelProvider | None = None,
    assistant: Any | None = None,
) -> Understanding:
    """Use the configured language model fallback only after deterministic handling misses."""
    active_provider = provider if provider is not None else get_default_llm_provider()

    if fallback.intent == "unknown" and is_likely_noise(text, bool(context.get("active_quiz"))):
        return Understanding(
            interpretation=Interpretation(intent="noise", confidence=0.0),
            category="noise",
        )

    # M09: If an educational question is received and a CurriculumAssistant is available,
    # ground the response strictly in retrieved curriculum evidence.
    if assistant is not None and fallback.intent == "question":
        ans = assistant.answer_question(text, context, provider=active_provider)
        return Understanding(
            interpretation=Interpretation(
                intent="question",
                confidence=0.9 if ans.supported else 0.4,
                command=None,
                answer=None,
            ),
            category="learning",
            response=ans.answer,
            clarification=ans.clarification,
            source=ans.source,
        )

    if not active_provider.configured:
        return Understanding(fallback, "learning" if fallback.intent == "question" else "unsupported")

    try:
        raw_output = active_provider.answer(_prompt(text, context))
        result = _parse(raw_output, fallback, context)
    except (OllamaUnavailableError, LanguageModelUnavailableError) as error:
        logger.info("llm_provider_unavailable error=%s", error)
        result = None
    except Exception as error:
        logger.exception("llm_provider_unexpected_failure")
        result = None

    return result or Understanding(
        # Preserve question intent from the fallback so callers can still speak a clarification.
        Interpretation(
            intent=fallback.intent if fallback.intent == "question" else "unknown",
            confidence=0.0,
        ),
        "learning" if fallback.intent == "question" else "clarification",
        clarification="I'm not sure what you want to do. Could you say that another way?",
    )
