"""Opening a project never waits for the AI model, even when its documents still miss summaries."""
import os
import sys
from types import SimpleNamespace
from unittest.mock import Mock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from design_project.service import DesignProjectService
from knowledge_base.domain import KnowledgeDocument
from knowledge_base.service import KnowledgeBaseService

LEGAL_ACT_URL = "https://opendata.eselpoint.gov.cz/esel-esb/eli/cz/sb/2001/56/2025-07-01"
EXPERT_DOCUMENT_ID = "expert-1"


def unsummarized_document(document_id: str) -> KnowledgeDocument:
    return KnowledgeDocument(id=document_id, title=document_id, content="Vozidlo", contentSummary=None)


def loader() -> Mock:
    loader = Mock()
    loader.load_document.side_effect = unsummarized_document
    return loader


def test_loading_a_project_does_not_summarize_its_documents():
    summarizer = Mock()
    knowledge_base_service = KnowledgeBaseService(loader(), loader(), summarizer)
    store = Mock()
    store.load_project.return_value = SimpleNamespace(
        legalKnowledgeBase=[SimpleNamespace(id=LEGAL_ACT_URL)],
        expertKnowledgeBase=[SimpleNamespace(id=EXPERT_DOCUMENT_ID)],
    )
    service = DesignProjectService(store, knowledge_base_service, Mock(), Mock(), Mock(), Mock(), Mock())

    service.load_project("project-1")

    summarizer.summarize_document.assert_not_called()
    legal, expert = store.set_project_knowledge.call_args.args[1:]
    assert [doc.id for doc in legal + expert] == [LEGAL_ACT_URL, EXPERT_DOCUMENT_ID]
