"""Voice transcription and deterministic utterance interpretation endpoints."""

import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.schemas import (
    TranscriptionMetadata,
    TranscriptionResponse,
    VoiceInterpretRequest,
    VoiceInterpretResponse,
)
from app.core.config import get_settings
from app.stt.provider import (
    STTModelError,
    STTTranscriptionError,
    STTUnavailableError,
    SpeechToTextProvider,
    get_stt_provider,
)
from app.voice.interpreter import interpret_text
from app.voice.understanding import understand
from app.qa.ollama import OllamaProvider

router = APIRouter(prefix="/voice", tags=["voice"])

SUPPORTED_AUDIO_TYPES = {
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/webm": ".webm",
}


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    audio: UploadFile = File(...), provider: SpeechToTextProvider = Depends(get_stt_provider)
) -> TranscriptionResponse:
    """Transcribe a small WAV or WebM upload without retaining the audio."""
    content_type = (audio.content_type or "").split(";", maxsplit=1)[0].casefold().strip()
    suffix = SUPPORTED_AUDIO_TYPES.get(content_type)
    if suffix is None:
        await audio.close()
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Use WAV or WebM audio")

    settings = get_settings()
    audio_bytes = await audio.read(settings.stt_max_upload_bytes + 1)
    await audio.close()
    if len(audio_bytes) > settings.stt_max_upload_bytes:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Audio upload is too large")
    if not audio_bytes:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Audio upload is empty")

    temporary_path: Path | None = None
    try:
        with NamedTemporaryFile(suffix=suffix, delete=False) as temporary_file:
            temporary_file.write(audio_bytes)
            temporary_path = Path(temporary_file.name)
        result = provider.transcribe(temporary_path)
    except STTUnavailableError as error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Speech recognition is unavailable") from error
    except STTModelError as error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Speech recognition is unavailable") from error
    except STTTranscriptionError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Audio could not be transcribed. Try a short WAV or WebM recording.",
        ) from error
    finally:
        if temporary_path is not None:
            try:
                os.unlink(temporary_path)
            except FileNotFoundError:
                pass

    if not result.text.strip():
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No speech was detected")
    return TranscriptionResponse(
        text=result.text,
        metadata=TranscriptionMetadata(
            language=result.language,
            duration_seconds=result.duration_seconds,
            model=result.model,
            device=result.device,
        ),
    )


@router.post("/interpret", response_model=VoiceInterpretResponse)
def interpret_voice(payload: VoiceInterpretRequest) -> VoiceInterpretResponse:
    """Classify with fast rules first and optional structured local reasoning second."""
    interpretation = interpret_text(payload.text, payload.context.active_quiz)
    understanding = understand(
        payload.text,
        payload.context.model_dump(),
        interpretation,
        OllamaProvider(get_settings()),
    ) if interpretation.intent in {"unknown", "question"} else None
    if understanding:
        interpretation = understanding.interpretation
        category = understanding.category
        response = understanding.response
        clarification = understanding.clarification
    else:
        category = None
        response = None
        clarification = None
    return VoiceInterpretResponse(
        intent=interpretation.intent,
        confidence=interpretation.confidence,
        command=interpretation.command,
        answer=interpretation.answer,
        category=category,
        response=response,
        clarification=clarification,
    )
