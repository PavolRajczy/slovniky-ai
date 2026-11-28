"""Searching the knowledge base reports an unresponsive embedding model instead of returning no results."""
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from knowledge_base.domain import KnowledgeDocument
from knowledge_base_index.service import KnowledgeBaseIndexService
from llm.provider import AIServiceUnavailableError


class UnresponsiveEmbeddingIndexer:
    def load_index(self, document):
        return True

    def search(self, *args, **kwargs):
        raise AIServiceUnavailableError("nemotron-3-5-embed-8b", TimeoutError("Request timed out."))


@pytest.fixture
def service() -> KnowledgeBaseIndexService:
    service = KnowledgeBaseIndexService(indexer_factory=UnresponsiveEmbeddingIndexer)
    service.add_document(KnowledgeDocument(id="doc", title="Doc", content="Vozidlo", contentSummary=None))
    return service


def test_search_reports_an_unresponsive_embedding_model(service):
    with pytest.raises(AIServiceUnavailableError):
        service.search("vozidlo")


def test_relative_search_reports_an_unresponsive_embedding_model(service):
    with pytest.raises(AIServiceUnavailableError):
        service.search_relative("vozidlo", 0.15)


def test_document_search_reports_an_unresponsive_embedding_model(service):
    with pytest.raises(AIServiceUnavailableError):
        service.search_in_document("doc", "vozidlo")
