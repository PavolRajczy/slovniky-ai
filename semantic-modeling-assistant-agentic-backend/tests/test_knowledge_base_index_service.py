#!/usr/bin/env python3
"""
Unit tests for KnowledgeBaseIndexService (service.py)

Tests the service layer that provides a simplified interface over the KnowledgeDocumentIndexer
for managing a collection of knowledge documents, including:
- Adding documents (with index building/loading)
- Searching within specific documents
- Searching across the entire collection
- Document management operations
- Error handling and validation

Note: These tests use mocked indexer implementations to avoid external dependencies.
"""

import os
import sys
from unittest.mock import Mock, MagicMock
from typing import List

# Ensure src/ is importable when running as a script
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from knowledge_base.domain import KnowledgeDocument, KnowledgeDocumentElement
from knowledge_base_index.domain import SearchQuery, SearchResult, ChunkMatch
from knowledge_base_index.indexer import KnowledgeDocumentIndexer
from knowledge_base_index.service import KnowledgeBaseIndexService


# ------------------------
# Helper builders
# ------------------------

def create_test_knowledge_document(doc_id: str = "test-doc-1", title: str = "Test Document") -> KnowledgeDocument:
    """Create a simple test knowledge document."""
    element = KnowledgeDocumentElement(
        id=f"element-{doc_id}",
        title=f"Test Element {doc_id}",
        content=f"This is test content for document {doc_id}",
        contentSummary=f"Test content summary for {doc_id}",
        elementType="Section"
    )
    
    return KnowledgeDocument(
        id=doc_id,
        title=title,
        content=f"Document content for {doc_id}",
        contentSummary=f"Document summary for {doc_id}",
        childElements=[element]
    )


def create_test_search_results(element_id: str = "element1") -> List[SearchResult]:
    """Create mock search results for testing."""
    chunk_match = ChunkMatch(
        chunk_id="chunk1",
        text="This is a test content for indexing",
        relevance_score=0.95
    )
    
    result = SearchResult(
        element_id=element_id,
        overall_relevance_score=0.95,
        matching_chunks=[chunk_match]
    )
    
    return [result]


# ------------------------
# Mock Indexer
# ------------------------

class MockKnowledgeDocumentIndexer(KnowledgeDocumentIndexer):
    """Mock implementation of KnowledgeDocumentIndexer for testing."""
    
    def __init__(self):
        self.build_index_calls = []
        self.search_calls = []
        self.store_index_calls = []
        self.load_index_calls = []
        self.should_fail_build = False
        self.should_fail_search = False
        self.should_fail_store = False
        self.should_load_successfully = False
        self.search_results = create_test_search_results("default-element")
    
    def build_index(self, knowledge_document: KnowledgeDocument) -> None:
        self.build_index_calls.append(knowledge_document)
        if self.should_fail_build:
            raise Exception("Mock indexer build failure")
    
    def search(self, query: SearchQuery) -> List[SearchResult]:
        self.search_calls.append(query)
        if self.should_fail_search:
            raise Exception("Mock indexer search failure")
        return self.search_results
    
    def store_index(self, knowledge_document: KnowledgeDocument) -> None:
        self.store_index_calls.append(knowledge_document)
        if self.should_fail_store:
            raise Exception("Mock indexer store failure")
    
    def load_index(self, knowledge_document: KnowledgeDocument) -> bool:
        self.load_index_calls.append(knowledge_document)
        return self.should_load_successfully


def create_mock_indexer_factory():
    """Create a factory function that returns mock indexers."""
    indexers = []
    
    def factory():
        indexer = MockKnowledgeDocumentIndexer()
        indexers.append(indexer)
        return indexer
    
    factory.indexers = indexers
    return factory


# ------------------------
# Test functions
# ------------------------

def test_service_initialization_with_default_factory():
    """Test that service initializes with default indexer factory when no factory provided."""
    print("Testing service initialization with default factory...")
    
    service = KnowledgeBaseIndexService()
    
    # Should have initialized successfully
    assert service is not None
    
    print("✓ Service initialized with default factory")


def test_service_initialization_with_custom_factory():
    """Test that service initializes with provided custom indexer factory."""
    print("Testing service initialization with custom factory...")
    
    factory = create_mock_indexer_factory()
    service = KnowledgeBaseIndexService(indexer_factory=factory)
    
    # Service should be initialized
    assert service is not None
    
    print("✓ Service initialized with custom factory")


def test_add_document_builds_new_index():
    """Test adding a document when no index exists (builds new index)."""
    print("Testing adding document that builds new index...")
    
    factory = create_mock_indexer_factory()
    service = KnowledgeBaseIndexService(indexer_factory=factory)
    
    knowledge_doc = create_test_knowledge_document("doc1")
    service.add_document(knowledge_doc)
    
    # Verify an indexer was created
    assert len(factory.indexers) == 1
    indexer = factory.indexers[0]
    
    # Verify load was attempted first
    assert len(indexer.load_index_calls) == 1
    assert indexer.load_index_calls[0] is knowledge_doc
    
    # Verify build and store were called (since load returned False)
    assert len(indexer.build_index_calls) == 1
    assert indexer.build_index_calls[0] is knowledge_doc
    assert len(indexer.store_index_calls) == 1
    assert indexer.store_index_calls[0] is knowledge_doc
    
    # Verify document is accessible for search (by trying a search)
    results = service.search("test")
    # Should not fail, indicating the document was properly added
    
    print("✓ Document added with new index built and stored")


def test_add_document_loads_existing_index():
    """Test adding a document when an index already exists (loads existing index)."""
    print("Testing adding document that loads existing index...")
    
    factory = create_mock_indexer_factory()
    service = KnowledgeBaseIndexService(indexer_factory=factory)
    
    knowledge_doc = create_test_knowledge_document("doc1")
    
    # Configure mock to return True for load (indicating existing index found)
    factory.indexers = []  # Reset
    
    def factory_with_load():
        indexer = MockKnowledgeDocumentIndexer()
        indexer.should_load_successfully = True
        factory.indexers.append(indexer)
        return indexer
    
    service = KnowledgeBaseIndexService(indexer_factory=factory_with_load)
    service.add_document(knowledge_doc)
    
    # Verify an indexer was created
    assert len(factory.indexers) == 1
    indexer = factory.indexers[0]
    
    # Verify load was called and succeeded
    assert len(indexer.load_index_calls) == 1
    assert indexer.load_index_calls[0] is knowledge_doc
    
    # Verify build and store were NOT called (since load succeeded)
    assert len(indexer.build_index_calls) == 0
    assert len(indexer.store_index_calls) == 0
    
    # Verify document is accessible for search (by trying a search)
    results = service.search("test")
    # Should not fail, indicating the document was properly added
    
    print("✓ Document added with existing index loaded")


def test_add_document_failure():
    """Test add document failure handling."""
    print("Testing add document failure handling...")
    
    factory = create_mock_indexer_factory()
    service = KnowledgeBaseIndexService(indexer_factory=factory)
    
    knowledge_doc = create_test_knowledge_document("doc1")
    
    # Configure mock to fail build
    def failing_factory():
        indexer = MockKnowledgeDocumentIndexer()
        indexer.should_fail_build = True
        factory.indexers.append(indexer)
        return indexer
    
    service = KnowledgeBaseIndexService(indexer_factory=failing_factory)
    
    try:
        service.add_document(knowledge_doc)
        assert False, "Expected exception was not raised"
    except Exception as e:
        assert "Failed to add document" in str(e)
        assert "doc1" in str(e)
    
    # Verify document was not added to collection by checking if search works
    try:
        results = service.search("test")
        # If no documents are added, search should return empty results
        assert len(results) == 0
    except Exception:
        # If search fails due to no documents, that's also acceptable
        pass
    
    print("✓ Add document failure handled correctly")


def test_search_in_document_success():
    """Test successful search in a specific document."""
    print("Testing successful search in document...")
    
    factory = create_mock_indexer_factory()
    service = KnowledgeBaseIndexService(indexer_factory=factory)
    
    knowledge_doc = create_test_knowledge_document("doc1")
    service.add_document(knowledge_doc)
    
    indexer = factory.indexers[0]
    # Update the search results to match the expected element ID
    indexer.search_results = create_test_search_results("element-doc1")
    
    results = service.search_in_document("doc1", "test query")
    
    # Verify the indexer was called with correct parameters
    search_calls = [call for call in indexer.search_calls if call.query_text == "test query"]
    assert len(search_calls) == 1
    query = search_calls[0]
    assert query.query_text == "test query"
    assert query.max_results == 10
    assert query.include_summaries == False
    
    # Verify results
    assert len(results) == 1
    assert results[0].element_id == "element-doc1"
    
    print("✓ Search in document completed successfully")


def test_search_in_document_not_found():
    """Test search in document that doesn't exist."""
    print("Testing search in non-existent document...")
    
    factory = create_mock_indexer_factory()
    service = KnowledgeBaseIndexService(indexer_factory=factory)
    
    try:
        service.search_in_document("nonexistent", "test query")
        assert False, "Expected exception was not raised"
    except Exception as e:
        assert "Document 'nonexistent' not found" in str(e)
    
    print("✓ Search in non-existent document handled correctly")


def test_search_in_collection_success():
    """Test successful search across multiple documents in collection."""
    print("Testing successful search in collection...")
    
    factory = create_mock_indexer_factory()
    service = KnowledgeBaseIndexService(indexer_factory=factory)
    
    # Add multiple documents
    doc1 = create_test_knowledge_document("doc1")
    doc2 = create_test_knowledge_document("doc2")
    service.add_document(doc1)
    service.add_document(doc2)
    
    # Configure different results for each indexer
    factory.indexers[0].search_results = create_test_search_results("element-doc1")
    factory.indexers[1].search_results = create_test_search_results("element-doc2")
    
    results = service.search_in_collection("test query", max_results=5)
    
    # Verify both indexers were called
    assert len(factory.indexers) == 2
    for indexer in factory.indexers:
        search_calls = [call for call in indexer.search_calls if call.query_text == "test query"]
        assert len(search_calls) == 1
        query = search_calls[0]
        assert query.max_results == 5
    
    # Verify results from both documents are returned
    assert len(results) == 2
    element_ids = [r.element_id for r in results]
    assert "element-doc1" in element_ids
    assert "element-doc2" in element_ids
    
    print("✓ Search in collection completed successfully")


def test_search_backward_compatibility():
    """Test that the search method works for backward compatibility."""
    print("Testing backward compatibility search method...")
    
    factory = create_mock_indexer_factory()
    service = KnowledgeBaseIndexService(indexer_factory=factory)
    
    doc1 = create_test_knowledge_document("doc1")
    service.add_document(doc1)
    
    # Update the mock indexer to return results with element ID that exists in the document
    indexer = factory.indexers[0]
    indexer.search_results = create_test_search_results("element-doc1")
    
    results = service.search("test query")
    
    # Verify the indexer was called
    assert len(factory.indexers) == 1
    search_calls = [call for call in indexer.search_calls if call.query_text == "test query"]
    assert len(search_calls) == 1
    
    # Verify results
    assert len(results) == 1
    
    print("✓ Backward compatibility search works")


def test_search_with_empty_query():
    """Test search with empty query returns empty results."""
    print("Testing search with empty query...")
    
    factory = create_mock_indexer_factory()
    service = KnowledgeBaseIndexService(indexer_factory=factory)
    
    doc1 = create_test_knowledge_document("doc1")
    service.add_document(doc1)
    
    # Test various empty query scenarios
    assert service.search_in_document("doc1", "") == []
    assert service.search_in_document("doc1", "   ") == []
    assert service.search_in_collection("") == []
    assert service.search("   ") == []
    
    # Verify indexers were never called for search
    for indexer in factory.indexers:
        search_calls = [call for call in indexer.search_calls if call.query_text.strip() == ""]
        assert len(search_calls) == 0
    
    print("✓ Empty query handled correctly")


def test_document_management_operations():
    """Test document management operations (has_document, remove_document, get_document_ids)."""
    print("Testing document management operations...")
    
    factory = create_mock_indexer_factory()
    service = KnowledgeBaseIndexService(indexer_factory=factory)
    
    # Initially empty
    assert service.get_document_ids() == []
    assert not service.has_document("doc1")
    
    # Add documents
    doc1 = create_test_knowledge_document("doc1")
    doc2 = create_test_knowledge_document("doc2")
    service.add_document(doc1)
    service.add_document(doc2)
    
    # Check state
    assert set(service.get_document_ids()) == {"doc1", "doc2"}
    assert service.has_document("doc1")
    assert service.has_document("doc2")
    assert not service.has_document("doc3")
    
    # Remove one document
    assert service.remove_document("doc1") == True
    assert service.remove_document("nonexistent") == False
    
    # Check final state
    assert service.get_document_ids() == ["doc2"]
    assert not service.has_document("doc1")
    assert service.has_document("doc2")
    
    print("✓ Document management operations work correctly")


def test_build_index_for_existing_document():
    """Test building index for a document that's already in the collection."""
    print("Testing build index for existing document...")
    
    factory = create_mock_indexer_factory()
    service = KnowledgeBaseIndexService(indexer_factory=factory)
    
    doc1 = create_test_knowledge_document("doc1")
    service.add_document(doc1)
    
    # Clear previous calls
    indexer = factory.indexers[0]
    indexer.build_index_calls.clear()
    
    # Build index again
    service.build_index(doc1)
    
    # Verify build was called on existing indexer
    assert len(indexer.build_index_calls) == 1
    assert indexer.build_index_calls[0] is doc1
    
    print("✓ Build index for existing document works")


def test_backward_compatibility_with_single_indexer():
    """Test backward compatibility when passing a single indexer to constructor."""
    print("Testing backward compatibility with single indexer...")
    
    mock_indexer = MockKnowledgeDocumentIndexer()
    service = KnowledgeBaseIndexService(indexer=mock_indexer)
    
    # Test that it works like the old interface
    doc1 = create_test_knowledge_document("doc1")
    service.build_index(doc1)
    
    # The same indexer should be used
    assert len(mock_indexer.build_index_calls) == 1
    assert mock_indexer.build_index_calls[0] is doc1
    
    # Test search
    mock_indexer.search_results = create_test_search_results("element-doc1")
    results = service.search("test query")
    
    assert len(mock_indexer.search_calls) == 1
    assert len(results) == 1
    
    print("✓ Backward compatibility with single indexer works")


def test_build_index_for_new_document():
    """Test building index for a document that's not yet in the collection."""
    print("Testing build index for new document...")
    
    factory = create_mock_indexer_factory()
    service = KnowledgeBaseIndexService(indexer_factory=factory)
    
    doc1 = create_test_knowledge_document("doc1")
    service.build_index(doc1)
    
    # Verify new indexer was created and build was called
    assert len(factory.indexers) == 1
    indexer = factory.indexers[0]
    assert len(indexer.build_index_calls) == 1
    assert indexer.build_index_calls[0] is doc1
    
    # Document should be in collection
    assert service.has_document("doc1")
    
    print("✓ Build index for new document works")


def test_search_with_offset():
    """Test search with offset parameter to skip top results."""
    print("Testing search with offset parameter...")
    
    factory = create_mock_indexer_factory()
    service = KnowledgeBaseIndexService(indexer_factory=factory)
    
    # Create multiple test results with different relevance scores
    def create_multiple_search_results(base_element_id: str, count: int) -> List[SearchResult]:
        results = []
        for i in range(count):
            chunk_match = ChunkMatch(
                chunk_id=f"chunk-{i}",
                text=f"Test content {i}",
                relevance_score=1.0 - (i * 0.1)  # Decreasing relevance scores
            )
            result = SearchResult(
                element_id=f"{base_element_id}-{i}",
                overall_relevance_score=1.0 - (i * 0.1),
                matching_chunks=[chunk_match]
            )
            results.append(result)
        return results
    
    # Create a document with multiple child elements to match the search results
    def create_test_knowledge_document_with_multiple_elements(doc_id: str) -> KnowledgeDocument:
        child_elements = []
        for i in range(10):  # Create 10 child elements
            element = KnowledgeDocumentElement(
                id=f"element-{i}",
                title=f"Test Element {i}",
                content=f"This is test content for element {i}",
                contentSummary=f"Test content summary for element {i}",
                elementType="Section"
            )
            child_elements.append(element)
        
        return KnowledgeDocument(
            id=doc_id,
            title="Test Document with Multiple Elements",
            content=f"Document content for {doc_id}",
            contentSummary=f"Document summary for {doc_id}",
            childElements=child_elements
        )
    
    # Add a document with multiple elements
    doc1 = create_test_knowledge_document_with_multiple_elements("doc1")
    service.add_document(doc1)
    
    indexer = factory.indexers[0]
    indexer.search_results = create_multiple_search_results("element", 10)
    
    # Test with offset=0 (no skipping)
    results_no_offset = service.search("test query", max_results=3, offset=0)
    assert len(results_no_offset) == 3
    assert results_no_offset[0].id == "element-0"
    assert results_no_offset[1].id == "element-1"
    assert results_no_offset[2].id == "element-2"
    
    # Test with offset=2 (skip first 2 results)
    results_with_offset = service.search("test query", max_results=3, offset=2)
    assert len(results_with_offset) == 3
    assert results_with_offset[0].id == "element-2"
    assert results_with_offset[1].id == "element-3"
    assert results_with_offset[2].id == "element-4"
    
    # Test with offset=5 and max_results=2
    results_offset_5 = service.search("test query", max_results=2, offset=5)
    assert len(results_offset_5) == 2
    assert results_offset_5[0].id == "element-5"
    assert results_offset_5[1].id == "element-6"
    
    # Test with large offset that exceeds available results
    results_large_offset = service.search("test query", max_results=5, offset=15)
    assert len(results_large_offset) == 0
    
    # Test with negative offset (should be treated as 0)
    results_negative_offset = service.search("test query", max_results=2, offset=-1)
    assert len(results_negative_offset) == 2
    assert results_negative_offset[0].id == "element-0"
    assert results_negative_offset[1].id == "element-1"
    
    print("✓ Search with offset parameter works correctly")


# ------------------------
# Main test runner
# ------------------------

def main():
    """Run all tests."""
    print("Running Knowledge Base Index Service tests...\n")
    
    try:
        test_service_initialization_with_default_factory()
        test_service_initialization_with_custom_factory()
        test_add_document_builds_new_index()
        test_add_document_loads_existing_index()
        test_add_document_failure()
        test_search_backward_compatibility()
        test_search_with_empty_query()
        test_search_with_offset()
        test_backward_compatibility_with_single_indexer()
        
        print(f"\n✓ All tests passed!")
        
    except Exception as e:
        print(f"\n✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
