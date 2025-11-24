#!/usr/bin/env python3
"""
Unit tests for IterationSuggesterAgent_Simple_OpenAI

This test verifies the functionality of the simple OpenAI-based iteration suggester agent.
It uses a test document from the ESEL knowledge base and validates the agent's ability to 
suggest design iterations for a design project focused on a specific knowledge domain area.
"""

import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from knowledge_base_index.indexers.faiss_summary_openai_indexer import FAISSSummaryOpenAIKnowledgeDocumentIndexer
from knowledge_base_index.service import KnowledgeBaseIndexService

# Ensure src/ is importable when running as a script
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from agents.iteration_suggesters.iteration_suggester_openai_simple import (
    IterationSuggesterAgent_Simple_OpenAI,
    IterationOutput,
    IterationsOutput
)
from design_project.domain import (
    DesignProject, DesignIteration, DesignIterationStatus, 
    KnowledgeDomain, KnowledgeDomainArea
)
from knowledge_base.domain import KnowledgeDocument
from knowledge_base.service import KnowledgeBaseService
from knowledge_base.document_loaders.document_loader_esel import ESELKnowledgeDocumentLoader
from knowledge_base.document_summarizers.document_summarizer_simple_openai import SimpleOpenAIKnowledgeDocumentSummarizer
from ontology.domain import Ontology


def test_suggester_with_real_document():
    """Test the iteration suggester with a real ESEL document and design project."""
    print("Testing iteration suggester with real document...")
    
    # Create ESEL document loader
    sparql_endpoint = "https://opendata.eselpoint.cz/sparql"
    document_loader = ESELKnowledgeDocumentLoader(sparql_endpoint, base_dir="data_test/knowledge_base/esel")
    
    # Create document summarizer (we'll mock its responses)
    document_summarizer = SimpleOpenAIKnowledgeDocumentSummarizer()
    
    # Create knowledge base service
    kb_service = KnowledgeBaseService(document_loader, document_summarizer)

    # Create knowledge base index service
    kb_index_service = KnowledgeBaseIndexService(indexer=FAISSSummaryOpenAIKnowledgeDocumentIndexer())

    # Create iteration suggester
    suggester = IterationSuggesterAgent_Simple_OpenAI(kb_service, kb_index_service)
    
    # Load the test document
    document_id = "https://opendata.eselpoint.cz/esel-esb/eli/cz/sb/2001/56/2025-07-01"
    documents = kb_service.load_knowledge_documents([document_id])
    
    assert len(documents) > 0, "Should load at least one document"
    test_document = documents[0]
    
    print(f"✓ Loaded document: {test_document.title}")
    print(f"  Document ID: {test_document.id}")
    print(f"  Child elements: {len(test_document.childElements)}")
    
    # Create a knowledge domain for testing
    knowledge_domain = KnowledgeDomain(
        label="Doména silničních vozidel a jejich provozu",
        description="Tato doména pokrývá znalosti týkající se různých typů silničních vozidel, jejich technických specifikací, registrace, a pravidel provozu na pozemních komunikacích.",
        areas=[]
    )
    
    # Create a focused knowledge domain area
    focused_area = KnowledgeDomainArea(
        id="area-registration",
        label="Registrace vozidel",
        description="Oblast zabývající se registračními postupy, požadavky a dokumenty pro silniční vozidla.",
        parent=knowledge_domain,
        keyConcepts=["registrace", "vozidlo", "technický průkaz", "státní poznávací značka"],
        modelingClasses=[],
        modelingAttributes=[],
        modelingRelationships=[],
        explainingKnowledgeResources=[]
    )
    
    # Create a simple ontology for testing
    test_ontology = Ontology(
        uri="https://example.org/test-ontology#",
        label="Test Vehicle Ontology",
        description="A test ontology for vehicle registration domain.",
        classes={},
        attributes={},
        relationships={}
    )
    
    # Create a design project for testing
    design_project = DesignProject(
        id="test-project-1",
        name="Test Vehicle Registration Project",
        finishedIterations=[],
        currentIteration=None,
        plannedIterations=[],
        patterns=[],
        legalKnowledgeBase=[],
        expertKnowledgeBase=[],
        keyKnowledgeDocument=test_document,
        modeledKnowledgeDomain=knowledge_domain,
        designedOntology=test_ontology
    )
    
    # Test the suggest_iterations method
    k = 7  # Request 7 iterations
    user_instruction = "Focus on the basic concepts and relationships in vehicle registration process."
    
    result_iterations = suggester.suggest_iterations(
        design_project=design_project,
        focused_area=focused_area,
        k=k,
        user_instruction=user_instruction
    )
        
    assert isinstance(result_iterations, list), "Should return a list of design iterations"
    print(f"✓ suggest_iterations executed successfully, returned {len(result_iterations)} iterations")
    
    # Verify the structure of returned iterations
    for i, iteration in enumerate(result_iterations):
        assert isinstance(iteration, DesignIteration), f"Iteration {i} should be a DesignIteration instance"
        assert iteration.name is not None and len(iteration.name) > 0, f"Iteration {i} should have a non-empty name"
        assert iteration.specification is not None and len(iteration.specification) > 0, f"Iteration {i} should have a non-empty specification"
        assert iteration.status == DesignIterationStatus.PLANNED, f"Iteration {i} should have PLANNED status"
        assert iteration.focusedArea == focused_area, f"Iteration {i} should reference the focused area"
        
        print(f"  Iteration {i+1}: {iteration.name}")
        print(f"    Specification: {iteration.specification}...")


def run_all_tests():
    """Run all tests for the iteration suggester agent."""
    print("=" * 60)
    print("Running tests for IterationSuggesterAgent_Simple_OpenAI")
    print("=" * 60)
    
    try:
        test_suggester_with_real_document()
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
