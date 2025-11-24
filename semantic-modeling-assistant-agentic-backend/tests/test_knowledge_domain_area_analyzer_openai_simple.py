#!/usr/bin/env python3
"""
Unit tests for KnowledgeDomainAreaAnalyzerAgent_Simple_OpenAI

This test verifies the functionality of the simple OpenAI-based knowledge domain area analyzer agent.
It uses a test document from the ESEL knowledge base and validates the agent's ability to 
identify knowledge domain areas within a knowledge domain.
"""

import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Ensure src/ is importable when running as a script
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from agents.knowledge_domain_area_analyzers.knowledge_domain_area_analyzer_openai_simple import (
    KnowledgeDomainAreaAnalyzerAgent_Simple_OpenAI,
    KnowledgeDomainAreaOutput,
    KnowledgeDomainOutput
)
from design_project.domain import KnowledgeDomain, KnowledgeDomainArea
from knowledge_base.domain import KnowledgeDocument
from knowledge_base.service import KnowledgeBaseService
from knowledge_base.document_loaders.document_loader_esel import ESELKnowledgeDocumentLoader
from knowledge_base.document_summarizers.document_summarizer_simple_openai import SimpleOpenAIKnowledgeDocumentSummarizer


def test_analyzer_with_real_document():
    """Test the analyzer with a real ESEL document."""
    print("Testing analyzer with real document...")
    
    # Create ESEL document loader
    sparql_endpoint = "https://opendata.eselpoint.cz/sparql"
    document_loader = ESELKnowledgeDocumentLoader(sparql_endpoint, base_dir="data_test/knowledge_base/esel")
    
    # Create document summarizer (we'll mock its responses)
    document_summarizer = SimpleOpenAIKnowledgeDocumentSummarizer()
    
    # Create knowledge base service
    kb_service = KnowledgeBaseService(document_loader, document_summarizer)
    
    # Create analyzer
    analyzer = KnowledgeDomainAreaAnalyzerAgent_Simple_OpenAI(kb_service)
    
    # Create a knowledge domain for testing
    knowledge_domain = KnowledgeDomain(
        label="Doména silničních vozidel a jejich provozu",
        description="Tato doména pokrývá znalosti týkající se různých typů silničních vozidel, jejich technických specifikací, registrace, a pravidel provozu na pozemních komunikacích.",
        areas=[]
    )
    
    # Load the test document
    document_id = "https://opendata.eselpoint.cz/esel-esb/eli/cz/sb/2001/56/2025-07-01"
    documents = kb_service.load_knowledge_documents([document_id])
    
    assert len(documents) > 0, "Should load at least one document"
    test_document = documents[0]
    
    print(f"✓ Loaded document: {test_document.title}")
    print(f"  Document ID: {test_document.id}")
    print(f"  Child elements: {len(test_document.childElements)}")
    
    result_areas = analyzer.identify_domain_areas(
        knowledge_domain=knowledge_domain,
        knowledge_document=test_document
    )
        
    assert isinstance(result_areas, list), "Should return a list of domain areas"
    print(f"✓ identify_domain_areas executed successfully, returned {len(result_areas)} areas")


def run_all_tests():
    """Run all tests for the knowledge domain area analyzer."""
    print("=" * 60)
    print("Running tests for KnowledgeDomainAreaAnalyzerAgent_Simple_OpenAI")
    print("=" * 60)
    
    try:
        test_analyzer_with_real_document()
        print()
        
        print("=" * 60)
        print("All tests completed successfully! ✓")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
