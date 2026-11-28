"""Summarizing stops with an error when the model does not answer, and keeps what was already summarized."""
import os
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from knowledge_base.document_summarizers.document_summarizer_simple_openai import SimpleOpenAIKnowledgeDocumentSummarizer
from knowledge_base.domain import KnowledgeDocument, KnowledgeDocumentElement
from llm.provider import AIServiceUnavailableError

SUMMARIZER = "knowledge_base.document_summarizers.document_summarizer_simple_openai"


def document_with_three_sections() -> KnowledgeDocument:
    sections = [
        KnowledgeDocumentElement(id=f"doc/{index}", title=f"Section {index}", content=f"Text {index}", contentSummary=None)
        for index in range(3)
    ]
    return KnowledgeDocument(id="doc", title="Doc", content=None, contentSummary=None, childElements=sections, cacheFilePath="doc.json")


def section_summaries(document: KnowledgeDocument) -> list:
    return [section.contentSummary for section in document.childElements]


@pytest.fixture
def summarizer(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    return SimpleOpenAIKnowledgeDocumentSummarizer(model="mini")


@patch(f"{SUMMARIZER}.CacheManager")
@patch(f"{SUMMARIZER}.invoke_chat")
def test_summarizing_stops_and_saves_progress_when_the_model_does_not_answer(invoke_chat, cache_manager, summarizer):
    invoke_chat.side_effect = ["Summary 0", AIServiceUnavailableError("mini", TimeoutError("Request timed out."))]
    document = document_with_three_sections()

    with pytest.raises(AIServiceUnavailableError):
        summarizer.summarize_document(document)

    assert section_summaries(document) == ["Summary 0", None, None]
    assert invoke_chat.call_count == 2
    cache_manager.update_split_cache.assert_called_once()


@patch(f"{SUMMARIZER}.CacheManager")
@patch(f"{SUMMARIZER}.invoke_chat")
def test_summarizing_skips_a_section_the_model_answers_badly(invoke_chat, cache_manager, summarizer):
    invoke_chat.side_effect = ["Summary 0", ValueError("Unexpected response."), "Summary 2", "Document summary"]
    document = document_with_three_sections()

    summarizer.summarize_document(document)

    assert section_summaries(document) == ["Summary 0", None, "Summary 2"]
    assert document.contentSummary == "Document summary"
