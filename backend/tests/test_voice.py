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
from app.voice.understanding import Understanding, _parse, understand
from app.qa.ollama import OllamaUnavailableError


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

    assert result.category == "clarification"
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
    assert b"/lesson/science-matter-basics" in captured["body"]
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
