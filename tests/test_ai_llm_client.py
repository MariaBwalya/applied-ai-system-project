import pytest

from ai.llm_client import GeminiClient, LLMConfigError, get_default_llm_client


def test_gemini_client_raises_config_error_without_api_key():
    with pytest.raises(LLMConfigError):
        GeminiClient(api_key=None)


def test_gemini_client_raises_config_error_with_empty_api_key():
    with pytest.raises(LLMConfigError):
        GeminiClient(api_key="")


def test_get_default_llm_client_raises_config_error_when_env_var_missing(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setattr("ai.llm_client.load_dotenv", lambda *args, **kwargs: None)
    with pytest.raises(LLMConfigError):
        get_default_llm_client()