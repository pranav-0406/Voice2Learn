"""Small, opt-in Ollama client. It deliberately does not define an API route."""

from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import Settings


class OllamaUnavailableError(RuntimeError):
    """Raised when local Ollama is not configured or cannot be reached."""


class OllamaProvider:
    """Generate a response only when an explicitly configured local model is available."""

    def __init__(self, settings: Settings) -> None:
        self._base_url = settings.ollama_base_url
        self._model = settings.ollama_model
        self._timeout = settings.ollama_timeout_seconds

    @property
    def configured(self) -> bool:
        return bool(self._model)

    def answer(self, question: str) -> str:
        if not self._model:
            raise OllamaUnavailableError("Educational answers are not configured")
        payload = json.dumps(
            {
                "model": self._model,
                "prompt": question,
                "stream": False,
                "format": "json",
            }
        ).encode("utf-8")
        request = Request(
            f"{self._base_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self._timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as error:
            raise OllamaUnavailableError("Educational answers are temporarily unavailable") from error
        answer = body.get("response")
        if not isinstance(answer, str) or not answer.strip():
            raise OllamaUnavailableError("Educational answers are temporarily unavailable")
        return answer.strip()
