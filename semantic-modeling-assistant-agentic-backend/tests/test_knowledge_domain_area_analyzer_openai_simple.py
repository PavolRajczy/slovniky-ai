#!/usr/bin/env python3
"""
Live test for KnowledgeDomainAreaAnalyzerAgent_Simple_OpenAI.

Loads a real e-Sbírka act and asks the LLM to split the knowledge domain into areas.
"""

import pytest

from agents.knowledge_domain_area_analyzers.knowledge_domain_area_analyzer_openai_simple import (
    KnowledgeDomainAreaAnalyzerAgent_Simple_OpenAI,
)
from live_support import LIVE_LEGAL_DOCUMENT_ID, create_live_knowledge_base_service, create_vehicle_domain


@pytest.mark.live
def test_analyzer_with_real_document():
    """Test the analyzer with a real e-Sbírka document."""
    kb_service = create_live_knowledge_base_service()
    analyzer = KnowledgeDomainAreaAnalyzerAgent_Simple_OpenAI(kb_service)

    documents = kb_service.load_legal_knowledge_documents([LIVE_LEGAL_DOCUMENT_ID])
    assert len(documents) > 0, "Should load at least one document"

    result_areas = analyzer.identify_domain_areas(
        knowledge_domain=create_vehicle_domain(),
        knowledge_document=documents[0],
    )

    assert isinstance(result_areas, list), "Should return a list of domain areas"
    assert len(result_areas) > 0, "Should identify at least one domain area"
