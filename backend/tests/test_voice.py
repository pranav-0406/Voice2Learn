from pathlib import Path
import logging
import sys
import types

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.main import app
from app.stt.provider import (
    FasterWhisperProvider,
    STTModelError,
    STTTranscriptionError,
    STTUnavailableError,
    TranscriptionResult,
    get_stt_provider,
)
from app.voice.interpreter import Interpretation
from app.voice.understanding import (
    Understanding,
    _parse,
    understand,
    _is_command_valid_in_context,
    ALLOWED_COMMANDS,
    QUIZ_ONLY_COMMANDS,
    LESSON_ONLY_COMMANDS,
)
from app.qa.ollama import OllamaUnavailableError
from app.qa.groq import LanguageModelUnavailableError


class SuccessfulProvider:
    def __init__(self) -> None:
        self.received_path: Path | None = None

    def transcribe(self, audio_path: Path) -> TranscriptionResult:
        self.received_path = audio_path
        return TranscriptionResult(
            text="Water can be a liquid.",
            language="en",
            duration_seconds=1.25,
            model="small",
            device="cpu",
        )


class UnavailableProvider:
    def transcribe(self, audio_path: Path) -> TranscriptionResult:
        raise STTUnavailableError("not installed")


class BrokenModelProvider:
    def transcribe(self, audio_path: Path) -> TranscriptionResult:
        raise STTModelError("model error")


class BrokenAudioProvider:
    def transcribe(self, audio_path: Path) -> TranscriptionResult:
        raise STTTranscriptionError("audio decode error")


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("VOICE2LEARN_DATABASE_PATH", str(tmp_path / "voice-test.sqlite3"))
    # Prevent any live Groq or Ollama LLM calls in interpret endpoint tests.
    # STT (Groq Whisper) tests use their own separate fixture in test_groq_stt.py.
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("VOICE2LEARN_OLLAMA_MODEL", raising=False)
    get_settings.cache_clear()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    get_settings.cache_clear()


def test_interpret_recognises_a_clear_command(client) -> None:
    response = client.post("/api/voice/interpret", json={"text": "next question"})

    assert response.status_code == 200
    assert response.json()["intent"] == "command"
    assert response.json()["confidence"] == 1.0
    assert response.json()["command"] == "NEXT_QUESTION"
    assert response.json()["answer"] is None


def test_interpret_help_is_a_command_with_case_and_punctuation(client) -> None:
    response = client.post("/api/voice/interpret", json={"text": "HELP!"})

    assert response.status_code == 200
    assert response.json()["command"] == "HELP"
    assert response.json()["intent"] == "command"


@pytest.mark.parametrize(
    ("spoken", "command"),
    [
        ("open dashboard", "OPEN_DASHBOARD"),
        ("open science", "OPEN_LESSON"),
        ("start quiz", "OPEN_QUIZ"),
        ("show my progress", "SHOW_PROGRESS"),
        ("select option c", "SELECT_OPTION_C"),
        ("stop speaking", "STOP_SPEAKING"),
    ],
)
def test_interpret_maps_global_accessibility_commands(client, spoken: str, command: str) -> None:
    response = client.post("/api/voice/interpret", json={"text": spoken})

    assert response.status_code == 200
    assert response.json()["intent"] == "command"
    assert response.json()["command"] == command


@pytest.mark.parametrize(
    ("spoken", "command"),
    [
        ("could you open the quiz please", "OPEN_QUIZ"),
        ("take me to the dashboard", "OPEN_DASHBOARD"),
        ("please stop talking", "STOP_SPEAKING"),
        ("pick option b", "SELECT_OPTION_B"),
        ("open quizz", "OPEN_QUIZ"),
        ("what can I say", "HELP"),
    ],
)
def test_interpret_understands_safe_command_paraphrases(client, spoken: str, command: str) -> None:
    response = client.post("/api/voice/interpret", json={"text": spoken})

    assert response.status_code == 200
    assert response.json()["intent"] == "command"
    assert response.json()["command"] == command


@pytest.mark.parametrize("spoken", ["What is photosynthesis?", "why is the sky blue?", "how does matter change?"])
def test_interpret_keeps_educational_questions_out_of_command_matching(client, spoken: str) -> None:
    response = client.post("/api/voice/interpret", json={"text": spoken})

    assert response.status_code == 200
    assert response.json()["intent"] == "question"
    assert response.json()["command"] is None


def test_structured_provider_result_is_validated_without_allowing_arbitrary_actions() -> None:
    fallback = Interpretation(intent="unknown", confidence=0.2)
    valid = _parse(
        '{"category":"application","command":"OPEN_QUIZ","confidence":0.91,"response":null,"clarification":null}',
        fallback,
    )
    invalid = _parse(
        '{"category":"application","command":"RUN_CODE","confidence":0.99}',
        fallback,
    )
    malformed = _parse("[]", fallback)

    assert isinstance(valid, Understanding)
    assert valid.interpretation.command == "OPEN_QUIZ"
    assert invalid is None
    assert malformed is None


def test_structured_provider_allows_every_frontend_supported_command() -> None:
    parsed = _parse(
        '{"category":"application","command":"NEXT_SECTION","confidence":0.9}',
        Interpretation(intent="unknown", confidence=0.2),
    )

    assert parsed is not None
    assert parsed.interpretation.command == "NEXT_SECTION"


def test_malformed_structured_learning_response_degrades_to_clarification() -> None:
    class MalformedProvider:
        configured = True

        def answer(self, question: str) -> str:
            return "Matter is anything that has mass and takes up space."

    result = understand(
        "What is matter?",
        {"screen": "/lesson/science-matter-basics", "lesson_topic": "matter"},
        Interpretation(intent="question", confidence=0.9),
        MalformedProvider(),
    )

    # When the model returns invalid JSON for a question, the fallback preserves the question
    # intent (category="learning") so the voice layer can still prompt for clarification.
    assert result.category == "learning"
    assert result.interpretation.command is None
    assert result.clarification


def test_provider_failure_degrades_to_clarification() -> None:
    class BrokenProvider:
        configured = True

        def answer(self, question: str) -> str:
            raise OllamaUnavailableError("provider unavailable")

    fallback = Interpretation(intent="unknown", confidence=0.2)

    result = understand("I am bored", {"screen": "/dashboard"}, fallback, BrokenProvider())

    assert result.category == "clarification"
    assert result.interpretation.command is None


def test_groq_llm_provider_failure_degrades_to_clarification() -> None:
    """M07: LanguageModelUnavailableError from GroqLLMProvider must degrade gracefully."""
    class BrokenGroqProvider:
        configured = True

        def answer(self, question: str) -> str:
            raise LanguageModelUnavailableError("groq rate limit")

    fallback = Interpretation(intent="unknown", confidence=0.2)
    result = understand("something unclear", {"screen": "/dashboard"}, fallback, BrokenGroqProvider())

    assert result.category == "clarification"
    assert result.interpretation.command is None
    assert result.clarification is not None


def test_null_provider_returns_unsupported_for_unknown_intent() -> None:
    """M07: When no provider is configured, unknown intent yields unsupported without crashing."""
    from app.voice.understanding import NullLLMProvider
    fallback = Interpretation(intent="unknown", confidence=0.2)
    result = understand("random words here", {"screen": "/quiz"}, fallback, NullLLMProvider())

    assert result.category == "unsupported"
    assert result.interpretation.command is None


def test_null_provider_returns_learning_for_question_intent() -> None:
    """M07: When no provider is configured, question intent yields learning category."""
    from app.voice.understanding import NullLLMProvider
    fallback = Interpretation(intent="question", confidence=0.9)
    result = understand("What is photosynthesis?", {"screen": "/concept/1"}, fallback, NullLLMProvider())

    assert result.category == "learning"
    assert result.interpretation.command is None


@pytest.mark.parametrize(
    ("spoken", "model_json", "category", "command"),
    [
        (
            "I'm bored; let's do something.",
            '{"category":"application","command":"OPEN_QUIZ","confidence":0.88,"response":null,"clarification":null}',
            "application",
            "OPEN_QUIZ",
        ),
        (
            "Explain that like I am younger.",
            '{"category":"follow_up","command":null,"confidence":0.86,"response":"I can explain it more simply.","clarification":null}',
            "follow_up",
            None,
        ),
    ],
)
def test_structured_provider_handles_unseen_natural_requests(
    spoken: str, model_json: str, category: str, command: str | None
) -> None:
    class FakeProvider:
        configured = True

        def answer(self, question: str) -> str:
            assert spoken in question
            return model_json

    result = understand(
        spoken,
        {"screen": "/dashboard", "recent_turns": ["Tell me about matter"]},
        Interpretation(intent="unknown", confidence=0.2),
        FakeProvider(),
    )

    assert result.category == category
    assert result.interpretation.command == command


def test_interpret_endpoint_uses_structured_provider_with_context(client, monkeypatch) -> None:
    monkeypatch.setenv("VOICE2LEARN_OLLAMA_MODEL", "test-model")
    get_settings.cache_clear()

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return (
                b'{"response":"{\\"category\\":\\"learning\\",'
                b'\\"command\\":null,\\"confidence\\":0.95,'
                b'\\"response\\":\\"Matter is anything that has mass and takes up space.\\",'
                b'\\"clarification\\":null}"}'
            )

    captured: dict[str, bytes] = {}

    def fake_urlopen(request, timeout):
        captured["body"] = request.data
        return FakeResponse()

    monkeypatch.setattr("app.qa.ollama.urlopen", fake_urlopen)
    response = client.post(
        "/api/voice/interpret",
        json={
            "text": "What is matter?",
            "context": {
                "screen": "/lesson/science-matter-basics",
                "lesson_topic": "matter",
                "recent_turns": ["learner: explain solids"],
            },
        },
    )

    assert response.status_code == 200
    assert response.json()["category"] == "learning"
    assert response.json()["intent"] == "question"
    assert "mass" in response.json()["response"]
    assert b"Matter Around Us" in captured["body"]
    assert b'"format": "json"' in captured["body"]


def test_interpret_uses_quiz_answer_only_in_active_quiz_context(client) -> None:
    active = client.post(
        "/api/voice/interpret", json={"text": "solid", "context": {"active_quiz": True}}
    )
    inactive = client.post("/api/voice/interpret", json={"text": "solid"})

    assert active.json()["intent"] == "quiz_answer"
    assert active.json()["answer"] == "solid"
    assert inactive.json()["intent"] == "unknown"


def test_interpret_recognises_questions_and_ambiguous_input(client) -> None:
    question = client.post("/api/voice/interpret", json={"text": "What is matter?"})
    ambiguous = client.post("/api/voice/interpret", json={"text": "maybe"})
    invalid = client.post("/api/voice/interpret", json={})

    assert question.json()["intent"] == "question"
    assert ambiguous.json()["intent"] == "unknown"
    assert invalid.status_code == 422


def test_transcription_returns_mocked_text_and_removes_temporary_audio(client) -> None:
    provider = SuccessfulProvider()
    app.dependency_overrides[get_stt_provider] = lambda: provider

    response = client.post(
        "/api/voice/transcribe",
        files={"audio": ("sample.wav", b"RIFF test audio", "audio/wav")},
    )

    assert response.status_code == 200
    assert response.json()["text"] == "Water can be a liquid."
    assert response.json()["metadata"] == {
        "language": "en",
        "duration_seconds": 1.25,
        "model": "small",
        "device": "cpu",
    }
    assert provider.received_path is not None
    assert not provider.received_path.exists()


def test_transcription_rejects_invalid_uploads_without_loading_provider(client) -> None:
    unsupported = client.post(
        "/api/voice/transcribe",
        files={"audio": ("notes.txt", b"not audio", "text/plain")},
    )
    empty = client.post(
        "/api/voice/transcribe",
        files={"audio": ("empty.webm", b"", "audio/webm")},
    )

    assert unsupported.status_code == 415
    assert empty.status_code == 422


def test_transcription_enforces_configured_upload_limit(client, monkeypatch) -> None:
    monkeypatch.setenv("VOICE2LEARN_STT_MAX_UPLOAD_BYTES", "4")
    get_settings.cache_clear()

    response = client.post(
        "/api/voice/transcribe",
        files={"audio": ("sample.webm", b"12345", "audio/webm; codecs=opus")},
    )

    assert response.status_code == 413


@pytest.mark.parametrize("provider", [UnavailableProvider(), BrokenModelProvider()])
def test_transcription_handles_unavailable_or_broken_stt_provider(client, provider) -> None:
    app.dependency_overrides[get_stt_provider] = lambda: provider

    response = client.post(
        "/api/voice/transcribe",
        files={"audio": ("sample.wav", b"RIFF test audio", "audio/wav")},
    )

    assert response.status_code == 503
    assert response.json() == {"detail": "Speech recognition is unavailable"}


def test_transcription_reports_unreadable_audio_without_claiming_stt_is_unavailable(client) -> None:
    app.dependency_overrides[get_stt_provider] = lambda: BrokenAudioProvider()

    response = client.post(
        "/api/voice/transcribe",
        files={"audio": ("sample.wav", b"RIFF invalid audio", "audio/wav")},
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "Audio could not be transcribed. Try a short WAV or WebM recording."}


def test_provider_logs_dependency_and_model_initialization_failure_categories(monkeypatch, caplog) -> None:
    caplog.set_level(logging.WARNING, logger="app.stt.provider")
    monkeypatch.setitem(sys.modules, "faster_whisper", None)

    with pytest.raises(STTUnavailableError):
        FasterWhisperProvider(Settings())._get_model()

    assert "stt_dependency_unavailable" in caplog.text

    fake_module = types.ModuleType("faster_whisper")

    class FailingWhisperModel:
        def __init__(self, *args, **kwargs) -> None:
            raise RuntimeError("simulated model initialization failure")

    fake_module.WhisperModel = FailingWhisperModel
    monkeypatch.setitem(sys.modules, "faster_whisper", fake_module)

    with pytest.raises(STTModelError):
        FasterWhisperProvider(Settings())._get_model()

    assert "stt_model_initialization_failed" in caplog.text


@pytest.mark.parametrize(
    ("spoken", "expected_command"),
    [
        ("need a hint", "HINT"),
        ("give me a clue", "HINT"),
        ("help me with this question", "HINT"),
        ("can you give me a hint please", "HINT"),
        ("next concept", "NEXT_CONCEPT"),
        ("next idea", "NEXT_CONCEPT"),
        ("next point", "NEXT_CONCEPT"),
        ("previous concept", "PREV_CONCEPT"),
        ("previous idea", "PREV_CONCEPT"),
        ("last point", "PREV_CONCEPT"),
        ("take me home", "OPEN_DASHBOARD"),
        ("go to home screen", "OPEN_DASHBOARD"),
        ("back to main menu", "OPEN_DASHBOARD"),
        ("let's study science", "OPEN_LESSON"),
        ("read it to me", "READ_LESSON"),
        ("narrate lesson", "READ_LESSON"),
        ("read this aloud please", "READ_LESSON"),
        ("let's practice", "OPEN_QUIZ"),
        ("test my knowledge", "OPEN_QUIZ"),
        ("quiz me", "OPEN_QUIZ"),
        ("pick a", "SELECT_OPTION_A"),
        ("choose option c please", "SELECT_OPTION_C"),
        ("i pick option d", "SELECT_OPTION_D"),
        ("lock in my answer", "SUBMIT_ANSWER"),
        ("final answer", "SUBMIT_ANSWER"),
        ("submit this", "SUBMIT_ANSWER"),
        ("how many points do i have", "SHOW_PROGRESS"),
        ("view my stats", "SHOW_PROGRESS"),
        ("say that again", "REPEAT"),
        ("pardon", "REPEAT"),
        ("hush", "STOP_SPEAKING"),
        ("pause voice", "STOP_LISTENING"),
        ("how do i use this", "HELP"),
        ("instructions please", "HELP"),
    ],
)
def test_interpret_m07_english_natural_language_commands(
    client, spoken: str, expected_command: str
) -> None:
    """M07: Fast deterministic intent parsing of natural conversational English commands."""
    response = client.post("/api/voice/interpret", json={"text": spoken})

    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "command"
    assert data["command"] == expected_command


# ─── M07: New conversational command variants ─────────────────────────────────

@pytest.mark.parametrize(
    ("spoken", "expected_command"),
    [
        ("explain this again", "REPEAT"),
        ("can you explain that again", "REPEAT"),
        ("say it again", "REPEAT"),
        ("once more", "REPEAT"),
        ("could you give me a clue", "HINT"),
        ("could you give me a hint", "HINT"),
        ("can i get a hint", "HINT"),
        ("hint please", "HINT"),
        ("clue please", "HINT"),
        ("what does option a say", "READ_QUESTION"),
        ("what does option c say", "READ_QUESTION"),
        ("read the choices", "READ_QUESTION"),
        ("read the options", "READ_QUESTION"),
    ],
)
def test_interpret_m07_new_conversational_variants(
    client, spoken: str, expected_command: str
) -> None:
    """M07: Additional conversational English variants resolve deterministically."""
    response = client.post("/api/voice/interpret", json={"text": spoken})
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "command"
    assert data["command"] == expected_command


# ─── M07: Context validation ──────────────────────────────────────────────────

def test_context_allows_quiz_command_in_quiz_screen() -> None:
    """M07: Quiz-only commands are valid when active_quiz=True."""
    assert _is_command_valid_in_context("HINT", {"active_quiz": True, "screen": "/quiz"}) is True
    assert _is_command_valid_in_context("SUBMIT_ANSWER", {"active_quiz": True, "screen": "/quiz"}) is True
    assert _is_command_valid_in_context("SELECT_OPTION_A", {"active_quiz": True, "screen": "/quiz"}) is True


def test_context_rejects_quiz_commands_outside_quiz() -> None:
    """M07: Quiz-only commands are rejected when not in quiz context."""
    assert _is_command_valid_in_context("HINT", {"active_quiz": False, "screen": "/dashboard"}) is False
    assert _is_command_valid_in_context("SUBMIT_ANSWER", {"active_quiz": False, "screen": "/concept/1"}) is False
    assert _is_command_valid_in_context("SELECT_OPTION_B", {"active_quiz": False, "screen": "/lesson/sci"}) is False


def test_context_allows_lesson_commands_in_lesson_screen() -> None:
    """M07: Lesson-only commands are valid on lesson/concept screens."""
    assert _is_command_valid_in_context("NEXT_CONCEPT", {"active_quiz": False, "screen": "/concept/5"}) is True
    assert _is_command_valid_in_context("PREV_CONCEPT", {"active_quiz": False, "screen": "/lesson/sci"}) is True
    assert _is_command_valid_in_context("READ_LESSON", {"active_quiz": False, "screen": "/concept/1"}) is True


def test_context_rejects_lesson_commands_outside_lesson() -> None:
    """M07: Lesson-only commands are rejected outside lesson/concept screens."""
    assert _is_command_valid_in_context("NEXT_CONCEPT", {"active_quiz": False, "screen": "/dashboard"}) is False
    assert _is_command_valid_in_context("READ_LESSON", {"active_quiz": True, "screen": "/quiz"}) is False


def test_context_allows_global_commands_everywhere() -> None:
    """M07: Global commands (navigation, help, stop) are always valid."""
    for cmd in ["OPEN_DASHBOARD", "OPEN_QUIZ", "GO_BACK", "HELP", "STOP_SPEAKING", "STOP_LISTENING", "CANCEL"]:
        assert _is_command_valid_in_context(cmd, {"active_quiz": False, "screen": "/dashboard"}) is True
        assert _is_command_valid_in_context(cmd, {"active_quiz": True, "screen": "/quiz"}) is True


def test_context_rejects_commands_not_in_allowlist() -> None:
    """M07: Commands not in ALLOWED_COMMANDS are always rejected."""
    assert _is_command_valid_in_context("RUN_ARBITRARY_CODE", {"screen": "/quiz", "active_quiz": True}) is False
    assert _is_command_valid_in_context("OPEN_SHELL", {"screen": "/", "active_quiz": False}) is False


def test_llm_command_blocked_by_context_in_parse() -> None:
    """M07: _parse disallows quiz commands if context shows non-quiz screen."""
    fallback = Interpretation(intent="unknown", confidence=0.2)
    context = {"active_quiz": False, "screen": "/dashboard"}
    result = _parse(
        '{"category":"application","command":"SUBMIT_ANSWER","confidence":0.95,"response":null,"clarification":null}',
        fallback,
        context,
    )
    # Command is blocked — result may be a clarification or None
    if result is not None:
        assert result.interpretation.command is None
        assert result.category == "clarification"


# ─── M07: Allowed/disallowed command set integrity ────────────────────────────

def test_quiz_only_commands_are_subset_of_allowed_commands() -> None:
    assert QUIZ_ONLY_COMMANDS.issubset(ALLOWED_COMMANDS)


def test_lesson_only_commands_are_subset_of_allowed_commands() -> None:
    assert LESSON_ONLY_COMMANDS.issubset(ALLOWED_COMMANDS)


# ─── M07: Groq LLM provider unit tests ───────────────────────────────────────

def test_groq_llm_provider_not_configured_without_key() -> None:
    """M07: GroqLLMProvider.configured is False when no API key."""
    from app.qa.groq import GroqLLMProvider
    provider = GroqLLMProvider(Settings(groq_api_key=None))
    assert provider.configured is False


def test_groq_llm_provider_raises_when_unconfigured() -> None:
    """M07: Calling answer() when not configured raises LanguageModelUnavailableError."""
    from app.qa.groq import GroqLLMProvider
    provider = GroqLLMProvider(Settings(groq_api_key=None))
    with pytest.raises(LanguageModelUnavailableError):
        provider.answer("test")


# ─── M07: get_default_llm_provider selection ─────────────────────────────────

def test_get_default_provider_prefers_ollama_when_configured(monkeypatch) -> None:
    """M07: Ollama is used first when its model is configured."""
    from app.voice.understanding import get_default_llm_provider
    from app.qa.ollama import OllamaProvider
    monkeypatch.setenv("VOICE2LEARN_OLLAMA_MODEL", "mistral")
    get_settings.cache_clear()
    provider = get_default_llm_provider(get_settings())
    assert isinstance(provider, OllamaProvider)
    get_settings.cache_clear()


def test_get_default_provider_falls_back_to_groq_when_ollama_unconfigured(monkeypatch) -> None:
    """M07: GroqLLMProvider is used when Ollama is unconfigured but GROQ_API_KEY is present."""
    from app.voice.understanding import get_default_llm_provider
    from app.qa.groq import GroqLLMProvider
    monkeypatch.delenv("VOICE2LEARN_OLLAMA_MODEL", raising=False)
    monkeypatch.setenv("GROQ_API_KEY", "test-key-abc123")
    get_settings.cache_clear()
    provider = get_default_llm_provider(get_settings())
    assert isinstance(provider, GroqLLMProvider)
    get_settings.cache_clear()


def test_get_default_provider_returns_null_when_nothing_configured(monkeypatch) -> None:
    """M07: NullLLMProvider is returned when neither Ollama nor Groq is configured."""
    from app.voice.understanding import get_default_llm_provider, NullLLMProvider
    monkeypatch.delenv("VOICE2LEARN_OLLAMA_MODEL", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_APIKEY", raising=False)
    get_settings.cache_clear()
    provider = get_default_llm_provider(get_settings())
    assert isinstance(provider, NullLLMProvider)
    get_settings.cache_clear()


# ─── M07: Regression tests ────────────────────────────────────────────────────

def test_interpret_still_recognises_core_commands_after_m07_extension(client) -> None:
    """Regression: M07 extensions must not break original commands."""
    cases = [
        ("next question", "NEXT_QUESTION"),
        ("open dashboard", "OPEN_DASHBOARD"),
        ("stop speaking", "STOP_SPEAKING"),
        ("submit answer", "SUBMIT_ANSWER"),
        ("show my progress", "SHOW_PROGRESS"),
        ("go back", "GO_BACK"),
    ]
    for spoken, expected in cases:
        resp = client.post("/api/voice/interpret", json={"text": spoken})
        assert resp.status_code == 200
        assert resp.json()["command"] == expected, f"Failed for '{spoken}'"


def test_educational_questions_remain_non_executable_after_m07(client) -> None:
    """Regression M07: Questions must not produce executable commands."""
    questions = [
        "What is photosynthesis?",
        "How does the water cycle work?",
        "Why do objects fall?",
        "What is the capital of Tamil Nadu?",
    ]
    for q in questions:
        resp = client.post("/api/voice/interpret", json={"text": q})
        assert resp.json()["command"] is None, f"Question '{q}' should not produce a command"
        assert resp.json()["intent"] == "question"
