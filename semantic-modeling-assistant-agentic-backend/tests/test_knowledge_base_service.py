#!/usr/bin/env python3
"""
Unit tests for KnowledgeBaseService.

Tests the KnowledgeBaseService with real documents:
- ESEL legal document from data/esel/1000-01-1000-01-01
- Local document from data/local/silnicni-vozidla-expert-knowledge

These tests demonstrate the service working with actual document content
and the get_knowledge_document_outline_from_summaries functionality.

Note: These tests require an OpenAI API key to be set as OPENAI_API_KEY environment variable.
For testing without actual API calls, mock implementations are provided.
"""

import os
import sys
from typing import Optional
from unittest.mock import Mock, patch
import numpy as np

# Ensure src/ is importable when running as a script
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from knowledge_base.domain import KnowledgeDocument, KnowledgeDocumentElement
from knowledge_base.service import KnowledgeBaseService
from knowledge_base.document_loaders.document_loader_esel import ESELKnowledgeDocumentLoader
from knowledge_base.document_loaders.document_loader_local import LocalKnowledgeDocumentLoader
from knowledge_base.document_summarizers.document_summarizer_simple_openai import SimpleOpenAIKnowledgeDocumentSummarizer


# ------------------------
# Mock OpenAI for testing without API calls
# ------------------------

class MockOpenAIResponse:
    def __init__(self, text: str):
        self.choices = [Mock()]
        self.choices[0].message = Mock()
        self.choices[0].message.content = text


def mock_openai_chat_create(model, messages, **kwargs):
    """Mock OpenAI chat.completions.create method."""
    # Generate a simple summary based on the input
    user_message = messages[-1]['content'] if messages else ""
    if "summarize" in user_message.lower():
        summary = "This is a mock summary of the content."
    else:
        summary = "This is a mock response."
    
    return MockOpenAIResponse(summary)


# ------------------------
# Document Loading Functions
# ------------------------

def load_esel_document() -> Optional[KnowledgeDocument]:
    """Load the ESEL legal document."""
    try:
        sparql_endpoint = "https://opendata.eselpoint.cz/sparql"
        loader = ESELKnowledgeDocumentLoader(sparql_endpoint)
        
        document_id = "https://opendata.eselpoint.cz/esel-esb/eli/cz/sb/1000/01/1000-01-01"
        
        print(f"Loading ESEL document: {document_id}")
        document = loader.load_document(document_id)
        
        if document:
            print(f"✓ ESEL document loaded: {document.title}")
            print(f"  - ID: {document.id}")
            print(f"  - Element type: {document.elementType}")
            print(f"  - Child elements: {len(document.childElements)}")
            if document.content:
                print(f"  - Content length: {len(document.content)} characters")
            else:
                print("  - No direct content (structured document)")
        else:
            print("✗ Failed to load ESEL document")
        
        return document
    
    except Exception as e:
        print(f"✗ Error loading ESEL document: {e}")
        return None


def load_local_document() -> Optional[KnowledgeDocument]:
    """Load the local document."""
    try:
        loader = LocalKnowledgeDocumentLoader()
        
        document_id = "https://localhost/silnicni-vozidla-expert-knowledge.docx"
        
        print(f"Loading local document: {document_id}")
        document = loader.load_document(document_id)
        
        if document:
            print(f"✓ Local document loaded: {document.title}")
            print(f"  - ID: {document.id}")
            print(f"  - Element type: {document.elementType}")
            print(f"  - Child elements: {len(document.childElements)}")
            if document.content:
                print(f"  - Content length: {len(document.content)} characters")
            else:
                print("  - No direct content (structured document)")
        else:
            print("✗ Failed to load local document")
        
        return document
    
    except Exception as e:
        print(f"✗ Error loading local document: {e}")
        return None


# ------------------------
# Test Functions
# ------------------------

def test_knowledge_base_service_initialization():
    """Test KnowledgeBaseService initialization."""
    print("\n" + "=" * 60)
    print("Testing KnowledgeBaseService Initialization")
    print("=" * 60)
    
    try:
        # Create document loaders
        esel_loader = ESELKnowledgeDocumentLoader("https://opendata.eselpoint.cz/sparql")
        local_loader = LocalKnowledgeDocumentLoader()
        
        # Mock the summarizer to avoid API calls during initialization
        with patch('openai.OpenAI'):
            summarizer = Mock()
            
            # Create the service with ESEL loader
            service_esel = KnowledgeBaseService(esel_loader, summarizer)
            print("✓ Service initialized with ESEL loader")
            
            # Create the service with Local loader
            service_local = KnowledgeBaseService(local_loader, summarizer)
            print("✓ Service initialized with Local loader")
        
        return True
    
    except Exception as e:
        print(f"✗ Error initializing service: {e}")
        return False


def test_load_knowledge_documents():
    """Test loading knowledge documents through the service."""
    print("\n" + "=" * 60)
    print("Testing Knowledge Document Loading")
    print("=" * 60)
    
    try:
        # Create document loaders
        esel_loader = ESELKnowledgeDocumentLoader("https://opendata.eselpoint.cz/sparql")
        local_loader = LocalKnowledgeDocumentLoader()
        
        # Mock the summarizer
        with patch('openai.OpenAI'):
            summarizer = Mock()
            
            # Test with ESEL document
            print("\nTesting ESEL document loading...")
            service_esel = KnowledgeBaseService(esel_loader, summarizer)
            esel_documents = service_esel.load_knowledge_documents([
                "https://opendata.eselpoint.cz/esel-esb/eli/cz/sb/1000/01/1000-01-01"
            ])
            
            if esel_documents and len(esel_documents) > 0:
                print("✓ ESEL document loaded through service")
                print(f"  - Loaded {len(esel_documents)} document(s)")
            else:
                print("⚠️  ESEL document not available through service")
            
            # Test with Local document
            print("\nTesting Local document loading...")
            service_local = KnowledgeBaseService(local_loader, summarizer)
            local_documents = service_local.load_knowledge_documents([
                "https://localhost/silnicni-vozidla-expert-knowledge.docx"
            ])
            
            if local_documents and len(local_documents) > 0:
                print("✓ Local document loaded through service")
                print(f"  - Loaded {len(local_documents)} document(s)")
            else:
                print("⚠️  Local document not available through service")
        
        return True
    
    except Exception as e:
        print(f"✗ Error loading documents through service: {e}")
        return False


@patch('openai.OpenAI')
def test_knowledge_document_outline_from_summaries(mock_openai_class):
    """Test generating knowledge document outline from summaries."""
    print("\n" + "=" * 60)
    print("Testing Knowledge Document Outline Generation")
    print("=" * 60)
    
    try:
        # Mock the OpenAI client and its chat.completions.create method
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.return_value = MockOpenAIResponse("This is a mock summary.")
        
        # Create document loaders
        esel_loader = ESELKnowledgeDocumentLoader("https://opendata.eselpoint.cz/sparql")
        local_loader = LocalKnowledgeDocumentLoader()
        
        # Create a mock summarizer that actually sets contentSummary
        summarizer = Mock()
        def mock_summarize(document):
            # Set mock summaries for the document and its elements
            document.contentSummary = f"Summary of {document.title or document.id}"
            for element in document.childElements:
                mock_summarize_element(element)
        
        def mock_summarize_element(element):
            element.contentSummary = f"Summary of element {element.id}"
            for child in element.childElements:
                mock_summarize_element(child)
        
        summarizer.summarize_document = mock_summarize
        
        # Test with ESEL document
        print("\nTesting ESEL document outline...")
        esel_document = load_esel_document()
        if esel_document:
            service_esel = KnowledgeBaseService(esel_loader, summarizer)
            
            # First summarize the document to populate contentSummary fields
            summarizer.summarize_document(esel_document)
            
            outline = service_esel.get_knowledge_document_outline_from_summaries(esel_document)
            print("✓ ESEL document outline generated")
            print("Outline preview (first 500 chars):")
            print(outline[:500] + ("..." if len(outline) > 500 else ""))
            
            # Validate outline structure
            assert "<document>" in outline
            assert "<id>" in outline
            assert "<summary>" in outline
            assert esel_document.id in outline
            assert "</document>" in outline
            
            # Check for hierarchical sections if there are child elements
            if esel_document.childElements:
                assert "<section>" in outline
                assert "</section>" in outline
                print(f"✓ Found hierarchical sections for {len(esel_document.childElements)} child elements")
        else:
            print("⚠️  Skipping ESEL document outline test - document not available")
        
        # Test with Local document
        print("\nTesting Local document outline...")
        local_document = load_local_document()
        if local_document:
            service_local = KnowledgeBaseService(local_loader, summarizer)
            
            # First summarize the document to populate contentSummary fields
            summarizer.summarize_document(local_document)
            
            outline = service_local.get_knowledge_document_outline_from_summaries(local_document)
            print("✓ Local document outline generated")
            print("Outline preview (first 500 chars):")
            print(outline[:500] + ("..." if len(outline) > 500 else ""))
            
            # Validate outline structure
            assert "<document>" in outline
            assert "<id>" in outline
            assert "<summary>" in outline
            assert local_document.id in outline
            assert "</document>" in outline
            
            # Check for hierarchical sections if there are child elements
            if local_document.childElements:
                assert "<section>" in outline
                assert "</section>" in outline
                print(f"✓ Found hierarchical sections for {len(local_document.childElements)} child elements")
        else:
            print("⚠️  Skipping Local document outline test - document not available")
        
        return True
    
    except Exception as e:
        print(f"✗ Error generating document outline: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_outline_with_deep_hierarchy():
    """Test outline generation with a mock document having deep hierarchy."""
    print("\n" + "=" * 60)
    print("Testing Outline Generation with Deep Hierarchy")
    print("=" * 60)
    
    try:
        # Create a mock document with nested structure using realistic IDs
        doc_id = "https://example.com/documents/test-doc"
        
        child2 = KnowledgeDocumentElement(
            id=f"{doc_id}#child2",
            title="Child 2",
            content="Content of child 2",
            contentSummary="Summary of child 2"
        )
        
        grandchild = KnowledgeDocumentElement(
            id=f"{doc_id}/section1/grandchild1",
            title="Grandchild 1",
            content="Content of grandchild 1",
            contentSummary="Summary of grandchild 1"
        )
        
        child1 = KnowledgeDocumentElement(
            id=f"{doc_id}/section1",
            title="Child 1",
            content="Content of child 1",
            contentSummary="Summary of child 1",
            childElements=[grandchild]
        )
        grandchild.parentElement = child1
        
        mock_document = KnowledgeDocument(
            id=doc_id,
            title="Test Document",
            content="Content of test document",
            contentSummary="Summary of test document",
            childElements=[child1, child2]
        )
        child1.parentElement = mock_document
        child2.parentElement = mock_document
        
        # Create service with mock loaders
        mock_loader = Mock()
        mock_summarizer = Mock()
        service = KnowledgeBaseService(mock_loader, mock_summarizer)
        
        # Generate outline
        outline = service.get_knowledge_document_outline_from_summaries(mock_document)
        
        print("✓ Deep hierarchy outline generated")
        print("Complete outline:")
        print(outline)
        
        # Validate structure
        assert outline.count("<section>") == 3  # child1, child2, grandchild1
        assert outline.count("</section>") == 3
        assert "Summary of test document" in outline
        assert "Summary of child 1" in outline
        assert "Summary of child 2" in outline
        assert "Summary of grandchild 1" in outline
        
        # Check that document ID is absolute but children are relative
        assert f"<id>{doc_id}</id>" in outline  # Document ID should be absolute
        assert "<id>section1</id>" in outline  # Child ID should be relative
        assert "<id>child2</id>" in outline   # Child ID should be relative
        assert "<id>section1/grandchild1</id>" in outline  # Grandchild ID should be relative
        
        # Check that absolute IDs are NOT in child sections
        assert f"<id>{doc_id}/section1</id>" not in outline
        assert f"<id>{doc_id}#child2</id>" not in outline
        
        # Check nesting - grandchild should be inside child1's section
        child1_start = outline.find('<section>\n\t\t<id>section1</id>')
        child1_end = outline.find('</section>', child1_start)
        child1_section = outline[child1_start:child1_end]
        assert "section1/grandchild1" in child1_section
        
        print("✓ All structure validations passed")
        print("✓ Relative ID generation working correctly")
        
        return True
    
    except Exception as e:
        print(f"✗ Error testing deep hierarchy: {e}")
        import traceback
        traceback.print_exc()
        return False


# ------------------------
# Main Test Runner
# ------------------------

if __name__ == "__main__":
    print("Running Knowledge Base Service tests...")
    
    tests = [
        test_knowledge_base_service_initialization,
        test_load_knowledge_documents,
        test_knowledge_document_outline_from_summaries,
        test_outline_with_deep_hierarchy
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with error: {e}")
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed}/{total} tests passed")
    if passed == total:
        print("✓ All tests passed!")
    else:
        print(f"✗ {total - passed} test(s) failed")
    print("=" * 60)
