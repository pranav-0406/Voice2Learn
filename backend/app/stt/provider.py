"""Lazy faster-whisper provider that keeps model loading out of app startup."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import logging
from pathlib import Path
from typing import Protocol

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


class STTUnavailableError(Exception):
    """Raised when optional speech recognition cannot be used."""


class STTModelError(Exception):
    """Raised when the configured local model cannot be loaded or used."""


class STTTranscriptionError(Exception):
    """Raised when an uploaded audio stream cannot be decoded or transcribed."""


class STTConfigurationError(STTUnavailableError):
    """Raised when speech recognition configuration is invalid or missing required keys."""


class STTAuthenticationError(Exception):
    """Raised when cloud speech recognition authentication fails (HTTP 401)."""


class STTRateLimitError(Exception):
    """Raised when cloud speech recognition rate limit is reached (HTTP 429)."""


class STTTimeoutError(STTUnavailableError):
    """Raised when cloud speech recognition API call times out."""


class STTProviderError(STTUnavailableError):
    """Raised when cloud speech recognition returns 5xx or connection fails."""


@dataclass(frozen=True)
class TranscriptionResult:
    text: str
    language: str | None
    duration_seconds: float | None
    model: str
    device: str


class SpeechToTextProvider(Protocol):
    def transcribe(self, audio_path: Path) -> TranscriptionResult: ...


class FasterWhisperProvider:
    """Loads faster-whisper only when the first transcription is requested."""

    def __init__(self, settings: Settings) -> None:
        self._model_size = settings.stt_model_size
        self._device = settings.stt_device
        self._compute_type = settings.stt_compute_type
        self._beam_size = settings.stt_beam_size
        self._vad_filter = settings.stt_vad_filter
        self._cpu_threads = settings.stt_cpu_threads
        self._prompt = settings.stt_prompt
        self._model: object | None = None

    def _get_model(self):
        if self._model is not None:
            return self._model
        try:
            from faster_whisper import WhisperModel
        except ImportError as error:
            logger.warning(
                "stt_dependency_unavailable model=%s device=%s compute_type=%s",
                self._model_size,
                self._device,
                self._compute_type,
                exc_info=True,
            )
            raise STTUnavailableError("Optional faster-whisper dependency is not installed") from error
        try:
            model_options = {
                "device": self._device,
                "compute_type": self._compute_type,
            }
            if self._cpu_threads:
                model_options["cpu_threads"] = self._cpu_threads
            self._model = WhisperModel(self._model_size, **model_options)
        except Exception as error:
            logger.exception(
                "stt_model_initialization_failed model=%s device=%s compute_type=%s",
                self._model_size,
                self._device,
                self._compute_type,
            )
            raise STTModelError("The configured speech model could not be initialized") from error
        return self._model

    def transcribe(self, audio_path: Path) -> TranscriptionResult:
        model = self._get_model()
        try:
            segments, info = model.transcribe(
                str(audio_path),
                beam_size=self._beam_size,
                vad_filter=self._vad_filter,
                condition_on_previous_text=False,
                initial_prompt=self._prompt,
            )
            text = " ".join(segment.text.strip() for segment in segments if segment.text.strip())
        except Exception as error:
            logger.exception(
                "stt_transcription_failed model=%s device=%s compute_type=%s",
                self._model_size,
                self._device,
                self._compute_type,
            )
            raise STTTranscriptionError("Audio could not be transcribed by the configured speech model") from error
        return TranscriptionResult(
            text=text,
            language=getattr(info, "language", None),
            duration_seconds=getattr(info, "duration", None),
            model=self._model_size,
            device=self._device,
        )


class GroqWhisperProvider:
    """Transcription provider backed by Groq Cloud Whisper API."""

    def __init__(self, settings: Settings) -> None:
        self._api_key = settings.groq_api_key
        self._model = settings.groq_stt_model
        self._prompt = settings.stt_prompt
        self._timeout = settings.groq_timeout_seconds
        self._client: object | None = None

    def _get_client(self):
        if not self._api_key:
            raise STTConfigurationError(
                "Groq speech-to-text is selected but GROQ_API_KEY is not configured."
            )
        if self._client is not None:
            return self._client
        try:
            from groq import Groq
        except ImportError as error:
            logger.warning("groq_dependency_unavailable", exc_info=True)
            raise STTUnavailableError("Optional groq dependency is not installed") from error

        try:
            self._client = Groq(api_key=self._api_key, timeout=self._timeout)
        except Exception as error:
            logger.exception("groq_client_initialization_failed")
            raise STTConfigurationError("Failed to initialize Groq client") from error
        return self._client

    def transcribe(self, audio_path: Path) -> TranscriptionResult:
        if not self._api_key:
            raise STTConfigurationError(
                "Groq speech-to-text is selected but GROQ_API_KEY is not configured."
            )

        if not audio_path.exists() or audio_path.stat().st_size == 0:
            return TranscriptionResult(
                text="",
                language="en",
                duration_seconds=0.0,
                model=self._model,
                device="cloud",
            )

        client = self._get_client()

        try:
            from groq import (
                APIConnectionError,
                APIStatusError,
                APITimeoutError,
                AuthenticationError,
                RateLimitError,
            )
        except ImportError:
            AuthenticationError = ()
            RateLimitError = ()
            APITimeoutError = ()
            APIConnectionError = ()
            APIStatusError = ()

        try:
            with open(audio_path, "rb") as audio_file:
                transcription = client.audio.transcriptions.create(
                    file=(audio_path.name, audio_file.read()),
                    model=self._model,
                    prompt=self._prompt,
                    response_format="verbose_json",
                    language="en",
                    temperature=0.0,
                )
        except AuthenticationError as error:
            logger.warning("groq_stt_authentication_failed model=%s", self._model)
            raise STTAuthenticationError(
                "Groq speech-to-text authentication failed. Please verify your GROQ_API_KEY."
            ) from error
        except RateLimitError as error:
            logger.warning("groq_stt_rate_limit_exceeded model=%s", self._model)
            raise STTRateLimitError(
                "Groq speech-to-text rate limit exceeded. Please wait a moment before trying again."
            ) from error
        except APITimeoutError as error:
            logger.warning("groq_stt_timeout model=%s", self._model)
            raise STTTimeoutError(
                "Groq speech-to-text request timed out. Please try again."
            ) from error
        except APIConnectionError as error:
            logger.warning("groq_stt_connection_error model=%s", self._model)
            raise STTProviderError(
                "Could not connect to Groq speech-to-text service. Check your internet connection."
            ) from error
        except APIStatusError as error:
            status_code = getattr(error, "status_code", 500)
            err_msg = getattr(error, "message", str(error))
            logger.warning("groq_stt_status_error status_code=%s model=%s: %s", status_code, self._model, err_msg)
            if status_code >= 500:
                raise STTProviderError(
                    "Groq speech-to-text service is temporarily unavailable."
                ) from error
            raise STTTranscriptionError(
                f"Audio could not be transcribed by Groq speech-to-text (status {status_code}): {err_msg}"
            ) from error
        except (
            STTUnavailableError,
            STTAuthenticationError,
            STTRateLimitError,
            STTTimeoutError,
            STTProviderError,
            STTConfigurationError,
        ):
            raise
        except Exception as error:
            logger.exception("groq_stt_transcription_failed model=%s", self._model)
            raise STTTranscriptionError(
                "Audio could not be transcribed by the configured speech model"
            ) from error

        text = getattr(transcription, "text", "") or ""
        duration = getattr(transcription, "duration", None)
        language = getattr(transcription, "language", None)

        return TranscriptionResult(
            text=text.strip(),
            language=language or "en",
            duration_seconds=duration,
            model=self._model,
            device="groq",
        )


class UnsupportedProvider:
    """Fallback provider when an unknown STT_PROVIDER is requested."""

    def __init__(self, provider_name: str) -> None:
        self._provider_name = provider_name

    def transcribe(self, audio_path: Path) -> TranscriptionResult:
        raise STTConfigurationError(
            f"Unsupported STT provider '{self._provider_name}'. Supported providers are 'local' and 'groq'."
        )


@lru_cache
def get_stt_provider() -> SpeechToTextProvider:
    """Return a provider instance according to settings without initializing heavy models."""
    settings = get_settings()
    provider_name = (settings.stt_provider or "local").strip().casefold()
    if provider_name == "groq":
        return GroqWhisperProvider(settings)
    elif provider_name == "local":
        return FasterWhisperProvider(settings)
    return UnsupportedProvider(settings.stt_provider)

