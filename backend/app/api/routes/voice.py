"""Voice transcription and deterministic utterance interpretation endpoints."""

import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from starlette.concurrency import run_in_threadpool

from app.api.dependencies import get_curriculum_assistant
from app.api.schemas import (
    CurriculumSourceMetadata,
    TranscriptionMetadata,
    TranscriptionResponse,
    VoiceInterpretRequest,
    VoiceInterpretResponse,
)
from app.core.config import get_settings
from app.stt.provider import (
    STTAuthenticationError,
    STTConfigurationError,
    STTModelError,
    STTProviderError,
    STTRateLimitError,
    STTTimeoutError,
    STTTranscriptionError,
    STTUnavailableError,
    SpeechToTextProvider,
    get_stt_provider,
)
from app.voice.interpreter import Interpretation, QUIZ_ANSWER_EXCLUSIONS, _normalise, interpret_text
from app.voice.understanding import (
    get_default_llm_provider,
    resolve_with_classifier,
    understand,
)

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
        result = await run_in_threadpool(provider.transcribe, temporary_path)
    except STTConfigurationError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error
    except STTAuthenticationError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Speech recognition provider authentication failed.",
        ) from error
    except STTRateLimitError as error:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Speech recognition rate limit reached. Please try again shortly.",
        ) from error
    except STTTimeoutError as error:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Speech recognition request timed out.",
        ) from error
    except STTProviderError as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error
    except STTUnavailableError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Speech recognition is unavailable",
        ) from error
    except STTModelError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Speech recognition is unavailable",
        ) from error
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

    print(f"\n{'='*70}", flush=True)
    print(f"🎙️  [SPEECH TRANSCRIBED AS TEXT]: \"{result.text.strip()}\"", flush=True)
    print(f"{'='*70}", flush=True)

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
def interpret_voice(
    payload: VoiceInterpretRequest,
    assistant: Any = Depends(get_curriculum_assistant),
) -> VoiceInterpretResponse:
    """Classify with fast rules first and optional structured local reasoning second."""
    interpretation = interpret_text(payload.text, payload.context.active_quiz)
    settings = get_settings()
    classifier_interpretation = interpretation
    normalized_text = _normalise(payload.text)
    if (
        settings.ai_classifier_enabled
        and payload.context.active_quiz
        and interpretation.intent == "unknown"
        and payload.text.strip()
        and len(normalized_text) < 2
        and normalized_text not in QUIZ_ANSWER_EXCLUSIONS
    ):
        classifier_interpretation = Interpretation(
            intent="quiz_answer",
            confidence=0.8,
            answer=" ".join(payload.text.strip().split()),
        )
    if settings.ai_classifier_enabled and not payload.text.strip():
        understanding = None
    elif settings.ai_classifier_enabled and classifier_interpretation.intent in {"quiz_answer", "command"}:
        understanding = resolve_with_classifier(
            payload.text,
            payload.context.model_dump(),
            classifier_interpretation,
            get_default_llm_provider(settings),
            settings.ai_classifier_timeout_seconds,
            assistant=assistant,
        )
    else:
        understanding = understand(
            payload.text,
            payload.context.model_dump(),
            interpretation,
            get_default_llm_provider(settings),
            assistant=assistant,
        ) if interpretation.intent in {"unknown", "question"} else None
    if understanding:
        interpretation = understanding.interpretation
        category = understanding.category
        response = understanding.response
        clarification = understanding.clarification
        source_meta = None
        if understanding.source:
            source_meta = CurriculumSourceMetadata(
                subject_id=understanding.source.subject_id,
                subject_name=understanding.source.subject_name,
                chapter_id=understanding.source.chapter_id,
                chapter_title=understanding.source.chapter_title,
                concept_id=understanding.source.concept_id,
                concept_title=understanding.source.concept_title,
            )
    else:
        category = None
        response = None
        clarification = None
        source_meta = None

    if interpretation.command:
        print(f"👉  [WEBSITE ACTION DISPATCHED]: Command -> {interpretation.command} (Confidence: {interpretation.confidence:.2f})", flush=True)
    elif interpretation.intent == "question" and response:
        print(f"📖  [WEBSITE CURRICULUM ANSWER]: \"{response}\"", flush=True)
    elif clarification:
        print(f"💬  [WEBSITE RESPONSE TO USER]: \"{clarification}\"", flush=True)

    return VoiceInterpretResponse(
        intent=interpretation.intent,
        confidence=interpretation.confidence,
        command=interpretation.command,
        answer=interpretation.answer,
        category=category,
        response=response,
        clarification=clarification,
        source=source_meta,
    )
