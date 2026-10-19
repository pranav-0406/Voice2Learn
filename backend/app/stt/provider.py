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


@lru_cache
def get_stt_provider() -> SpeechToTextProvider:
    """Return a provider instance without initializing a model."""
    return FasterWhisperProvider(get_settings())
