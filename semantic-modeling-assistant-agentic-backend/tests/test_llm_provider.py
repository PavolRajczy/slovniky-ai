"""Factory resolves the e-INFRA origin and model name without calling the API."""
import os
import sys
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from llm import provider


def test_chat_model_uses_configured_base_url_and_model(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://llm.ai.e-infra.cz/v1/")
    monkeypatch.setenv("OPENAI_MODEL", "kimi")

    with patch("llm.provider.ChatOpenAI") as mock_chat:
        mock_chat.return_value = Mock()
        provider.create_chat_model(provider.get_model())

    kwargs = mock_chat.call_args.kwargs
    assert kwargs["model"] == "kimi"
    assert kwargs["base_url"] == "https://llm.ai.e-infra.cz/v1"
    assert kwargs["api_key"] == "test-key"


def test_embeddings_use_qwen_on_the_same_origin(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://llm.ai.e-infra.cz/v1")
    monkeypatch.delenv("OPENAI_EMBEDDING_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_EMBEDDING_DIMENSION", raising=False)

    with patch("llm.provider.OpenAIEmbeddings") as mock_embeddings:
        mock_embeddings.return_value = Mock()
        provider.create_embeddings()

    kwargs = mock_embeddings.call_args.kwargs
    assert kwargs["model"] == "qwen3-embedding-4b"
    assert "dimensions" not in kwargs
    assert kwargs["base_url"] == "https://llm.ai.e-infra.cz/v1"
    assert kwargs["api_key"] == "test-key"


def test_parse_structured_uses_function_calling(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://llm.ai.e-infra.cz/v1")

    structured = Mock()
    structured.invoke.return_value = {"label": "Area"}
    chat = Mock()
    chat.with_structured_output.return_value = structured

    with patch("llm.provider.ChatOpenAI", return_value=chat):
        result = provider.parse_structured(
            [{"role": "user", "content": "plan"}],
            provider.BaseModel,
            "mini",
        )

    chat.with_structured_output.assert_called_once_with(
        provider.BaseModel,
        method="function_calling",
    )
    structured.invoke.assert_called_once()
    assert result == {"label": "Area"}


def test_batch_config_prefers_llm_model_name(monkeypatch):
    monkeypatch.setenv("LLM_MODEL_NAME", "deepseek")
    monkeypatch.setenv("OPENAI_MODEL", "mini")
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("LLM_CONFIG_FILE", raising=False)

    config = provider.resolve_llm_config()

    assert config.model_name == "deepseek"
    assert config.provider == provider.LLMProvider.OPENAI
