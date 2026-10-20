"""Cloud LLM provider backed by Groq Chat Completions API."""

from __future__ import annotations

import logging
from typing import Any

from app.core.config import Settings

logger = logging.getLogger(__name__)


class LanguageModelUnavailableError(RuntimeError):
    """Raised when an educational language model is not configured or fails to respond."""


class GroqLLMProvider:
    """Generate structured educational answers and classifications using Groq."""

    def __init__(self, settings: Settings) -> None:
        self._api_key = settings.groq_api_key
        self._model = settings.groq_llm_model
        self._timeout = settings.groq_timeout_seconds
        self._client: Any = None

    @property
    def configured(self) -> bool:
        return bool(self._api_key)

    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client
        if not self._api_key:
            raise LanguageModelUnavailableError("Groq API key is not configured")
        try:
            from groq import Groq
        except ImportError as error:
            logger.warning("groq_dependency_unavailable", exc_info=True)
            raise LanguageModelUnavailableError("groq library is not installed") from error

        try:
            self._client = Groq(api_key=self._api_key, timeout=self._timeout)
        except Exception as error:
            logger.exception("groq_client_init_failed")
            raise LanguageModelUnavailableError("Failed to initialize Groq client") from error
        return self._client

    def answer(self, prompt: str) -> str:
        if not self.configured:
            raise LanguageModelUnavailableError("Groq API key is not configured")

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
            APIConnectionError = APIStatusError = APITimeoutError = AuthenticationError = RateLimitError = Exception  # type: ignore

        try:
            chat_completion = client.chat.completions.create(
                model=self._model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a concise English-only educational voice assistant for Tamil Nadu Class 6 students. Return valid JSON only.",
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
            )
        except AuthenticationError as error:
            logger.warning("groq_llm_authentication_failed", exc_info=True)
            raise LanguageModelUnavailableError("Groq authentication failed") from error
        except RateLimitError as error:
            logger.warning("groq_llm_rate_limit_reached", exc_info=True)
            raise LanguageModelUnavailableError("Groq rate limit reached") from error
        except APITimeoutError as error:
            logger.warning("groq_llm_timeout", exc_info=True)
            raise LanguageModelUnavailableError("Groq request timed out") from error
        except (APIConnectionError, APIStatusError) as error:
            logger.warning("groq_llm_provider_error", exc_info=True)
            raise LanguageModelUnavailableError("Groq provider service unavailable") from error
        except Exception as error:
            logger.exception("groq_llm_unexpected_error")
            raise LanguageModelUnavailableError("Unexpected Groq LLM failure") from error

        if not chat_completion.choices:
            raise LanguageModelUnavailableError("No choices returned from Groq LLM")

        content = chat_completion.choices[0].message.content
        if not content or not content.strip():
            raise LanguageModelUnavailableError("Empty response from Groq LLM")

        return content.strip()
