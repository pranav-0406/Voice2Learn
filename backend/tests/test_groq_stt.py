from dataclasses import dataclass
from pathlib import Path
from unittest.mock import MagicMock
import httpx
import pytest
from fastapi.testclient import TestClient

import groq
from app.core.config import Settings, get_settings
from app.main import app
from app.stt.provider import (
    FasterWhisperProvider,
    GroqWhisperProvider,
    STTAuthenticationError,
    STTConfigurationError,
    STTProviderError,
    STTRateLimitError,
    STTTimeoutError,
    get_stt_provider,
)


@dataclass
class FakeTranscriptionVerbose:
    text: str
    duration: float = 1.45
    language: str = "en"


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("VOICE2LEARN_DATABASE_PATH", str(tmp_path / "groq-test.sqlite3"))
    get_settings.cache_clear()
    get_stt_provider.cache_clear()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    get_settings.cache_clear()
    get_stt_provider.cache_clear()


def test_settings_stt_provider_defaults_to_local(monkeypatch) -> None:
    monkeypatch.delenv("VOICE2LEARN_STT_PROVIDER", raising=False)
    monkeypatch.delenv("STT_PROVIDER", raising=False)
    get_settings.cache_clear()
    settings = get_settings()

    assert settings.stt_provider == "local"
    assert settings.groq_stt_model == "whisper-large-v3-turbo"


def test_settings_stt_provider_reads_groq_and_api_key(monkeypatch) -> None:
    monkeypatch.setenv("STT_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test_key_123")
    monkeypatch.setenv("GROQ_STT_MODEL", "whisper-large-v3")
    monkeypatch.setenv("GROQ_TIMEOUT_SECONDS", "45")
    monkeypatch.setenv("VOICE2LEARN_STT_PROMPT", "science, states of matter")
    get_settings.cache_clear()
    settings = get_settings()

    assert settings.stt_provider == "groq"
    assert settings.groq_api_key == "gsk_test_key_123"
    assert settings.groq_stt_model == "whisper-large-v3"
    assert settings.groq_timeout_seconds == 45
    assert settings.stt_prompt == "science, states of matter"


def test_get_stt_provider_returns_groq_provider_when_configured(monkeypatch) -> None:
    monkeypatch.setenv("STT_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "gsk_test_key")
    get_settings.cache_clear()
    get_stt_provider.cache_clear()

    provider = get_stt_provider()
    assert isinstance(provider, GroqWhisperProvider)


def test_get_stt_provider_returns_local_provider_when_configured(monkeypatch) -> None:
    monkeypatch.setenv("STT_PROVIDER", "local")
    get_settings.cache_clear()
    get_stt_provider.cache_clear()

    provider = get_stt_provider()
    assert isinstance(provider, FasterWhisperProvider)


def test_get_stt_provider_unsupported_provider_raises_configuration_error(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("STT_PROVIDER", "unknown_cloud")
    get_settings.cache_clear()
    get_stt_provider.cache_clear()

    provider = get_stt_provider()
    dummy_file = tmp_path / "test.wav"
    dummy_file.write_bytes(b"test")

    with pytest.raises(STTConfigurationError) as exc_info:
        provider.transcribe(dummy_file)
    assert "Unsupported STT provider" in str(exc_info.value)


def test_groq_missing_api_key_returns_503_configuration_error(client, monkeypatch) -> None:
    monkeypatch.setenv("STT_PROVIDER", "groq")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("VOICE2LEARN_GROQ_API_KEY", raising=False)
    get_settings.cache_clear()
    get_stt_provider.cache_clear()

    response = client.post(
        "/api/voice/transcribe",
        files={"audio": ("sample.wav", b"RIFF dummy audio data", "audio/wav")},
    )

    assert response.status_code == 503
    assert "GROQ_API_KEY is not configured" in response.json()["detail"]


def test_groq_successful_transcription(client, monkeypatch) -> None:
    monkeypatch.setenv("STT_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "gsk_valid_mock_key")
    get_settings.cache_clear()
    get_stt_provider.cache_clear()

    mock_client = MagicMock()
    mock_client.audio.transcriptions.create.return_value = FakeTranscriptionVerbose(
        text="A liquid flows and takes the shape of its container.",
        duration=2.1,
        language="en",
    )

    monkeypatch.setattr("groq.Groq", lambda **kwargs: mock_client)

    response = client.post(
        "/api/voice/transcribe",
        files={"audio": ("sample.webm", b"GBL_audio_content", "audio/webm")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["text"] == "A liquid flows and takes the shape of its container."
    assert data["metadata"]["language"] == "en"
    assert data["metadata"]["duration_seconds"] == 2.1
    assert data["metadata"]["model"] == "whisper-large-v3-turbo"
    assert data["metadata"]["device"] == "groq"

    # Verify parameters passed to Groq API
    assert mock_client.audio.transcriptions.create.called
    call_kwargs = mock_client.audio.transcriptions.create.call_args[1]
    assert call_kwargs["model"] == "whisper-large-v3-turbo"
    assert call_kwargs["language"] == "en"
    assert call_kwargs["temperature"] == 0.0
    assert call_kwargs["response_format"] == "verbose_json"
    assert "states of matter" in call_kwargs["prompt"]


def test_groq_respects_custom_model_and_prompt(client, monkeypatch) -> None:
    monkeypatch.setenv("STT_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "gsk_valid_mock_key")
    monkeypatch.setenv("GROQ_STT_MODEL", "whisper-large-v3")
    monkeypatch.setenv("VOICE2LEARN_STT_PROMPT", "evaporation, gas, steam")
    get_settings.cache_clear()
    get_stt_provider.cache_clear()

    mock_client = MagicMock()
    mock_client.audio.transcriptions.create.return_value = FakeTranscriptionVerbose(
        text="Steam is water in the gas state.",
        duration=1.8,
        language="en",
    )
    monkeypatch.setattr("groq.Groq", lambda **kwargs: mock_client)

    response = client.post(
        "/api/voice/transcribe",
        files={"audio": ("sample.wav", b"RIFF sample audio", "audio/wav")},
    )

    assert response.status_code == 200
    assert response.json()["metadata"]["model"] == "whisper-large-v3"
    call_kwargs = mock_client.audio.transcriptions.create.call_args[1]
    assert call_kwargs["model"] == "whisper-large-v3"
    assert call_kwargs["prompt"] == "evaporation, gas, steam"


def test_groq_authentication_failure_returns_502_without_leaking_key(client, monkeypatch) -> None:
    secret_key = "gsk_super_secret_value_xyz"
    monkeypatch.setenv("STT_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", secret_key)
    get_settings.cache_clear()
    get_stt_provider.cache_clear()

    mock_client = MagicMock()
    req = httpx.Request("POST", "https://api.groq.com/openai/v1/audio/transcriptions")
    auth_err = groq.AuthenticationError("Invalid API key provided", response=httpx.Response(401, request=req), body=None)
    mock_client.audio.transcriptions.create.side_effect = auth_err

    monkeypatch.setattr("groq.Groq", lambda **kwargs: mock_client)

    response = client.post(
        "/api/voice/transcribe",
        files={"audio": ("sample.wav", b"RIFF sample audio", "audio/wav")},
    )

    assert response.status_code == 502
    assert "Speech recognition provider authentication failed" in response.json()["detail"]
    # Ensure the secret key is NOT leaked
    assert secret_key not in response.text


def test_groq_rate_limiting_returns_429(client, monkeypatch) -> None:
    monkeypatch.setenv("STT_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "gsk_valid_mock_key")
    get_settings.cache_clear()
    get_stt_provider.cache_clear()

    mock_client = MagicMock()
    req = httpx.Request("POST", "https://api.groq.com/openai/v1/audio/transcriptions")
    mock_client.audio.transcriptions.create.side_effect = groq.RateLimitError(
        "Rate limit reached", response=httpx.Response(429, request=req), body=None
    )
    monkeypatch.setattr("groq.Groq", lambda **kwargs: mock_client)

    response = client.post(
        "/api/voice/transcribe",
        files={"audio": ("sample.wav", b"RIFF sample audio", "audio/wav")},
    )

    assert response.status_code == 429
    assert "rate limit reached" in response.json()["detail"].lower()


def test_groq_timeout_returns_504(client, monkeypatch) -> None:
    monkeypatch.setenv("STT_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "gsk_valid_mock_key")
    get_settings.cache_clear()
    get_stt_provider.cache_clear()

    mock_client = MagicMock()
    req = httpx.Request("POST", "https://api.groq.com/openai/v1/audio/transcriptions")
    mock_client.audio.transcriptions.create.side_effect = groq.APITimeoutError(request=req)
    monkeypatch.setattr("groq.Groq", lambda **kwargs: mock_client)

    response = client.post(
        "/api/voice/transcribe",
        files={"audio": ("sample.wav", b"RIFF sample audio", "audio/wav")},
    )

    assert response.status_code == 504
    assert "timed out" in response.json()["detail"].lower()


def test_groq_connection_network_error_returns_502(client, monkeypatch) -> None:
    monkeypatch.setenv("STT_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "gsk_valid_mock_key")
    get_settings.cache_clear()
    get_stt_provider.cache_clear()

    mock_client = MagicMock()
    req = httpx.Request("POST", "https://api.groq.com/openai/v1/audio/transcriptions")
    mock_client.audio.transcriptions.create.side_effect = groq.APIConnectionError(request=req)
    monkeypatch.setattr("groq.Groq", lambda **kwargs: mock_client)

    response = client.post(
        "/api/voice/transcribe",
        files={"audio": ("sample.wav", b"RIFF sample audio", "audio/wav")},
    )

    assert response.status_code == 502
    assert "Could not connect to Groq" in response.json()["detail"]


def test_groq_server_500_error_returns_502(client, monkeypatch) -> None:
    monkeypatch.setenv("STT_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "gsk_valid_mock_key")
    get_settings.cache_clear()
    get_stt_provider.cache_clear()

    mock_client = MagicMock()
    req = httpx.Request("POST", "https://api.groq.com/openai/v1/audio/transcriptions")
    mock_client.audio.transcriptions.create.side_effect = groq.APIStatusError(
        "Internal server error", response=httpx.Response(500, request=req), body=None
    )
    monkeypatch.setattr("groq.Groq", lambda **kwargs: mock_client)

    response = client.post(
        "/api/voice/transcribe",
        files={"audio": ("sample.wav", b"RIFF sample audio", "audio/wav")},
    )

    assert response.status_code == 502
    assert "temporarily unavailable" in response.json()["detail"]


def test_groq_empty_transcription_returns_422(client, monkeypatch) -> None:
    monkeypatch.setenv("STT_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "gsk_valid_mock_key")
    get_settings.cache_clear()
    get_stt_provider.cache_clear()

    mock_client = MagicMock()
    mock_client.audio.transcriptions.create.return_value = FakeTranscriptionVerbose(
        text="   ",
        duration=0.5,
        language="en",
    )
    monkeypatch.setattr("groq.Groq", lambda **kwargs: mock_client)

    response = client.post(
        "/api/voice/transcribe",
        files={"audio": ("sample.wav", b"RIFF sample audio", "audio/wav")},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "No speech was detected"


def test_groq_invalid_audio_upload_rejected_without_calling_provider(client, monkeypatch) -> None:
    monkeypatch.setenv("STT_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "gsk_valid_mock_key")
    get_settings.cache_clear()
    get_stt_provider.cache_clear()

    mock_client = MagicMock()
    monkeypatch.setattr("groq.Groq", lambda **kwargs: mock_client)

    unsupported = client.post(
        "/api/voice/transcribe",
        files={"audio": ("document.pdf", b"%PDF-1.4", "application/pdf")},
    )
    empty = client.post(
        "/api/voice/transcribe",
        files={"audio": ("empty.wav", b"", "audio/wav")},
    )

    assert unsupported.status_code == 415
    assert empty.status_code == 422
    assert not mock_client.audio.transcriptions.create.called


def test_stt_default_prompt_contains_tamil_nadu_and_curriculum_terms(monkeypatch) -> None:
    """M06: Default STT prompt biases Whisper toward authentic TN curriculum terms."""
    monkeypatch.delenv("VOICE2LEARN_STT_PROMPT", raising=False)
    monkeypatch.delenv("GROQ_STT_PROMPT", raising=False)
    get_settings.cache_clear()
    settings = get_settings()

    prompt = settings.stt_prompt
    assert "Tamil Nadu" in prompt
    assert "Samacheer Kalvi" in prompt
    assert "Chola" in prompt
    assert "photosynthesis" in prompt
    assert "fraction" in prompt
    assert "option A" in prompt

