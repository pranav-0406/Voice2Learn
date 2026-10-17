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
    assert response.json() == {
        "intent": "command",
        "confidence": 1.0,
        "command": "NEXT_QUESTION",
        "answer": None,
    }


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
