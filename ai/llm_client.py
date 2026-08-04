"""Swappable LLM client interface, plus a Gemini-backed implementation.

`LLMClient` is the entire seam between the rest of the system and whatever
model provider is behind it. `parser.py` only ever depends on this Protocol,
never on `GeminiClient` directly, so tests can substitute a fake with zero
network access and zero API key.
"""
import os
from typing import Protocol

from dotenv import load_dotenv

DEFAULT_MODEL_NAME = "gemini-flash-latest"


class LLMError(Exception):
    """Base class for all LLM-related failures."""


class LLMConfigError(LLMError):
    """Raised when the client cannot be configured (e.g. missing API key)."""


class LLMTimeoutError(LLMError):
    """Raised when the LLM request times out."""


class LLMRateLimitError(LLMError):
    """Raised when the provider reports a rate limit was exceeded."""


class LLMResponseError(LLMError):
    """Raised when the LLM returns an empty, blocked, or unusable response."""


class LLMClient(Protocol):
    def generate(self, prompt: str) -> str:
        ...


class GeminiClient:
    """Thin wrapper around the Gemini API. All SDK-specific errors are
    translated into the typed LLMError subclasses above so callers never
    need to know which SDK version is installed underneath."""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str = DEFAULT_MODEL_NAME,
        timeout_seconds: int = 20,
    ) -> None:
        if not api_key:
            raise LLMConfigError("GEMINI_API_KEY is missing or empty")
        self._api_key = api_key
        self._model_name = model_name
        self._timeout_seconds = timeout_seconds

    def generate(self, prompt: str) -> str:
        try:
            from google import genai
            from google.genai import errors as genai_errors
        except ImportError as exc:
            raise LLMConfigError(f"google-genai SDK is not installed: {exc}") from exc

        try:
            client = genai.Client(api_key=self._api_key)
            response = client.models.generate_content(
                model=self._model_name,
                contents=prompt,
            )
        except genai_errors.ClientError as exc:
            if getattr(exc, "code", None) == 429:
                raise LLMRateLimitError(str(exc)) from exc
            raise LLMResponseError(str(exc)) from exc
        except genai_errors.ServerError as exc:
            raise LLMResponseError(str(exc)) from exc
        except TimeoutError as exc:
            raise LLMTimeoutError(str(exc)) from exc
        except Exception as exc:
            raise LLMResponseError(str(exc)) from exc

        text = getattr(response, "text", None)
        if not text:
            raise LLMResponseError("empty response from model")
        return text


def get_default_llm_client() -> LLMClient:
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise LLMConfigError("GEMINI_API_KEY is not set in the environment")
    return GeminiClient(api_key=api_key)