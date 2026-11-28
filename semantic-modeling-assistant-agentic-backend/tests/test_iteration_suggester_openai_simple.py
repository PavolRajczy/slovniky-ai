#!/usr/bin/env python3
"""
Live test for IterationSuggesterAgent_Simple_OpenAI.

Loads a real e-Sbírka act and asks the LLM to suggest design iterations for
one knowledge domain area.
"""

import pytest

from agents.iteration_suggesters.iteration_suggester_openai_simple import IterationSuggesterAgent_Simple_OpenAI
from design_project.domain import DesignIteration, DesignIterationStatus
from knowledge_base_index.indexers.faiss_summary_openai_indexer import FAISSSummaryOpenAIKnowledgeDocumentIndexer
from knowledge_base_index.service import KnowledgeBaseIndexService
from live_support import (
    LIVE_LEGAL_DOCUMENT_ID,
    create_live_knowledge_base_service,
    create_registration_area,
    create_vehicle_domain,
    create_vehicle_project,
)


@pytest.mark.live
def test_suggester_with_real_document():
    """Test the iteration suggester with a real e-Sbírka document and design project."""
    kb_service = create_live_knowledge_base_service()
    kb_index_service = KnowledgeBaseIndexService(indexer=FAISSSummaryOpenAIKnowledgeDocumentIndexer())
    suggester = IterationSuggesterAgent_Simple_OpenAI(kb_service, kb_index_service)

    documents = kb_service.load_legal_knowledge_documents([LIVE_LEGAL_DOCUMENT_ID])
    assert len(documents) > 0, "Should load at least one document"

    knowledge_domain = create_vehicle_domain()
    focused_area = create_registration_area(knowledge_domain)
    design_project = create_vehicle_project(documents[0], knowledge_domain)

    result_iterations = suggester.suggest_iterations(
        design_project=design_project,
        focused_area=focused_area,
        k=7,
        user_instruction="Focus on the basic concepts and relationships in vehicle registration process.",
    )

    assert isinstance(result_iterations, list), "Should return a list of design iterations"
    for i, iteration in enumerate(result_iterations):
        assert isinstance(iteration, DesignIteration), f"Iteration {i} should be a DesignIteration instance"
        assert iteration.name, f"Iteration {i} should have a non-empty name"
        assert iteration.specification, f"Iteration {i} should have a non-empty specification"
        assert iteration.status == DesignIterationStatus.PLANNED, f"Iteration {i} should have PLANNED status"
        assert iteration.focusedArea == focused_area, f"Iteration {i} should reference the focused area"
