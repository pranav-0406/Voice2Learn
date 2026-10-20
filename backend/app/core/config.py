"""Environment-backed settings for the Voice2Learn backend."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

# pyrefly: ignore[missing-import]
from dotenv import load_dotenv
# Load .env file automatically
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

DEFAULT_CORS_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
)

DEFAULT_STT_PROMPT = (
    "Tamil Nadu, Samacheer Kalvi, Chennai, Madurai, Thanjavur, Kaveri, Chola, Pandya, "
    "Pallava, Sangam, Indus Valley, Harappa, states of matter, solid, liquid, gas, "
    "photosynthesis, evaporation, condensation, sublimation, measurement, gravitation, "
    "geometry, fraction, integer, ratio, proportion, option A, option B, option C, option D, "
    "hint, submit, next, repeat, lesson, quiz, progress"
)


@dataclass(frozen=True)
class Settings:
    """Runtime settings that are safe to use in request handling."""

    cors_origins: tuple[str, ...] = DEFAULT_CORS_ORIGINS
    database_path: Path = Path("data/voice2learn.sqlite3")
    stt_provider: str = "local"
    stt_model_size: str = "small"
    stt_device: str = "cpu"
    stt_compute_type: str = "int8"
    stt_beam_size: int = 1
    stt_vad_filter: bool = True
    stt_cpu_threads: int = 0
    stt_max_upload_bytes: int = 10 * 1024 * 1024
    stt_prompt: str = DEFAULT_STT_PROMPT
    groq_api_key: str | None = None
    groq_stt_model: str = "whisper-large-v3-turbo"
    groq_llm_model: str = "openai/gpt-oss-20b"
    groq_agent_model: str = "openai/gpt-oss-120b"
    groq_timeout_seconds: int = 30
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str | None = None
    ollama_timeout_seconds: int = 30
    secret_key: str = "voice2learn-development-secret-key-class6"


def _cors_origins_from_environment() -> tuple[str, ...]:
    """Read comma-separated CORS origins, retaining safe local defaults."""
    raw_origins = os.getenv("VOICE2LEARN_CORS_ORIGINS")
    if not raw_origins:
        return DEFAULT_CORS_ORIGINS

    origins = tuple(origin.strip().rstrip("/") for origin in raw_origins.split(",") if origin.strip())
    return origins or DEFAULT_CORS_ORIGINS


def _database_path_from_environment() -> Path:
    """Return the configured SQLite path or the backend-local development path."""
    configured_path = os.getenv("VOICE2LEARN_DATABASE_PATH")
    if configured_path:
        return Path(configured_path).expanduser()
    return Path(__file__).resolve().parents[2] / "data" / "voice2learn.sqlite3"


def _stt_provider_from_environment() -> str:
    raw = os.getenv("VOICE2LEARN_STT_PROVIDER") or os.getenv("STT_PROVIDER", "local")
    return raw.strip().casefold() if raw else "local"


def _groq_api_key_from_environment() -> str | None:
    raw = os.getenv("GROQ_API_KEY") or os.getenv("VOICE2LEARN_GROQ_API_KEY")
    return raw.strip() if raw and raw.strip() else None


def _groq_stt_model_from_environment() -> str:
    raw = os.getenv("GROQ_STT_MODEL") or os.getenv("VOICE2LEARN_GROQ_STT_MODEL", "whisper-large-v3-turbo")
    return raw.strip() if raw and raw.strip() else "whisper-large-v3-turbo"


def _groq_llm_model_from_environment() -> str:
    raw = os.getenv("GROQ_LLM_MODEL") or os.getenv("VOICE2LEARN_GROQ_LLM_MODEL", "openai/gpt-oss-20b")
    return raw.strip() if raw and raw.strip() else "openai/gpt-oss-20b"


def _groq_agent_model_from_environment() -> str:
    raw = os.getenv("AGENT_MODEL") or os.getenv("GROQ_AGENT_MODEL") or os.getenv("VOICE2LEARN_AGENT_MODEL")
    return raw.strip() if raw and raw.strip() else "openai/gpt-oss-120b"


def _stt_prompt_from_environment() -> str:
    raw = os.getenv("VOICE2LEARN_STT_PROMPT") or os.getenv("GROQ_STT_PROMPT")
    if raw is not None and raw.strip():
        return raw.strip()
    return DEFAULT_STT_PROMPT


def _positive_integer_from_environment(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        return default
    return value if value > 0 else default


def _boolean_from_environment(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.casefold() in {"1", "true", "yes", "on"}


@lru_cache
def get_settings() -> Settings:
    return Settings(
        cors_origins=_cors_origins_from_environment(),
        database_path=_database_path_from_environment(),
        stt_provider=_stt_provider_from_environment(),
        stt_model_size=os.getenv("VOICE2LEARN_STT_MODEL", "small"),
        stt_device=os.getenv("VOICE2LEARN_STT_DEVICE", "cpu"),
        stt_compute_type=os.getenv("VOICE2LEARN_STT_COMPUTE_TYPE", "int8"),
        stt_beam_size=_positive_integer_from_environment("VOICE2LEARN_STT_BEAM_SIZE", 1),
        stt_vad_filter=_boolean_from_environment("VOICE2LEARN_STT_VAD_FILTER", True),
        stt_cpu_threads=_positive_integer_from_environment("VOICE2LEARN_STT_CPU_THREADS", 0),
        stt_max_upload_bytes=_positive_integer_from_environment(
            "VOICE2LEARN_STT_MAX_UPLOAD_BYTES", 10 * 1024 * 1024
        ),
        stt_prompt=_stt_prompt_from_environment(),
        groq_api_key=_groq_api_key_from_environment(),
        groq_stt_model=_groq_stt_model_from_environment(),
        groq_llm_model=_groq_llm_model_from_environment(),
        groq_agent_model=_groq_agent_model_from_environment(),
        groq_timeout_seconds=_positive_integer_from_environment(
            "GROQ_TIMEOUT_SECONDS",
            _positive_integer_from_environment("VOICE2LEARN_GROQ_TIMEOUT_SECONDS", 30),
        ),
        ollama_base_url=os.getenv("VOICE2LEARN_OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/"),
        ollama_model=os.getenv("VOICE2LEARN_OLLAMA_MODEL") or None,
        ollama_timeout_seconds=_positive_integer_from_environment(
            "VOICE2LEARN_OLLAMA_TIMEOUT_SECONDS", 30
        ),
        secret_key=os.getenv("VOICE2LEARN_SECRET_KEY", "voice2learn-development-secret-key-class6"),
    )


