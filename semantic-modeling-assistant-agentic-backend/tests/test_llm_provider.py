"""Factory resolves the e-INFRA origin and model name without calling the API."""
import os
import sys
from unittest.mock import Mock, patch

import httpx
import pytest
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic import BaseModel

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from llm import provider


class Answer(BaseModel):
    text: str


def unresponsive_server(requests: list) -> httpx.Client:
    """An HTTP client whose every request ends with the error e-INFRA returns for a dropped vLLM backend."""
    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            500,
            json={"error": {"message": "Hosted_vllmException - Server disconnected"}},
            headers={"retry-after-ms": "1"},
        )
    return httpx.Client(transport=httpx.MockTransport(handler))


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


def test_embeddings_give_up_on_a_stalled_request(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    with patch("llm.provider.OpenAIEmbeddings") as mock_embeddings:
        mock_embeddings.return_value = Mock()
        provider.create_embeddings()

    kwargs = mock_embeddings.call_args.kwargs
    assert kwargs["request_timeout"] > 0


def test_chat_model_gives_up_on_a_stalled_request(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    with patch("llm.provider.ChatOpenAI") as mock_chat:
        mock_chat.return_value = Mock()
        provider.create_chat_model("mini")

    assert mock_chat.call_args.kwargs["timeout"] > 0


@pytest.mark.parametrize("call", [
    lambda: provider.invoke_chat([{"role": "user", "content": "hi"}], "mini"),
    lambda: provider.parse_structured([{"role": "user", "content": "hi"}], Answer, "mini"),
])
def test_chat_call_reports_an_unresponsive_model_after_three_attempts(monkeypatch, call):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://llm.example/v1")
    requests = []
    client = unresponsive_server(requests)

    with patch("llm.provider.ChatOpenAI", side_effect=lambda **kwargs: ChatOpenAI(**kwargs, http_client=client)):
        with pytest.raises(provider.AIServiceUnavailableError) as raised:
            call()

    assert len(requests) == 3
    assert "'mini' did not respond after 3 attempts" in str(raised.value)


def test_embedding_call_reports_an_unresponsive_model_after_three_attempts(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://llm.example/v1")
    requests = []
    client = unresponsive_server(requests)

    with patch("llm.provider.OpenAIEmbeddings", side_effect=lambda **kwargs: OpenAIEmbeddings(**kwargs, http_client=client)):
        embeddings = provider.create_embeddings("nemotron-3-5-embed-8b")
        with pytest.raises(provider.AIServiceUnavailableError):
            with provider.ai_service_call("nemotron-3-5-embed-8b"):
                embeddings.embed_documents(["vozidlo"])

    assert len(requests) == 3


def test_ai_service_call_keeps_errors_that_are_not_about_availability():
    with pytest.raises(ValueError):
        with provider.ai_service_call("mini"):
            raise ValueError("The model returned an invalid object.")


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
