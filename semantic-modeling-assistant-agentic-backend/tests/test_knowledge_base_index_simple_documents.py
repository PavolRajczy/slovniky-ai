#!/usr/bin/env python3
"""
Unit tests for knowledge base indexing functionality.

Tests the FAISS-based semantic indexing implementation including:
- IndexDocument creation from KnowledgeDocument
- Text chunking using semchunk
- Embedding generation and FAISS indexing
- Semantic search functionality

Note: These tests require an OpenAI API key to be set as OPENAI_API_KEY environment variable.
For testing without actual API calls, mock implementations can be added.
"""

import os
import sys
import uuid
from typing import List
from unittest.mock import Mock, patch
import numpy as np

# Ensure src/ is importable when running as a script
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from knowledge_base.domain import KnowledgeDocument, KnowledgeDocumentElement
from knowledge_base_index.domain import IndexDocument, TextChunk, SearchQuery, SearchResult, ChunkMatch
from knowledge_base_index.chunkers.semchunk_chunker import SemchunkIndexDocumentChunker
from knowledge_base_index.indexers.faiss_fulltext_openai_indexer import FAISSFullTextOpenAIKnowledgeDocumentIndexer


# ------------------------
# Helper builders
# ------------------------

def create_test_knowledge_document() -> KnowledgeDocument:
    """Create a test knowledge document with hierarchical structure."""
    
    # Create child elements
    section1 = KnowledgeDocumentElement(
        id="section1",
        title="Vehicle Classification",
        content="Vehicles can be classified into different categories based on their usage and design. Motor vehicles are self-propelled transportation devices.",
        contentSummary="Overview of vehicle classification systems",
        elementType="Section"
    )
    
    subsection1_1 = KnowledgeDocumentElement(
        id="subsection1_1", 
        title="Passenger Vehicles",
        content="Passenger vehicles are designed primarily for transporting people. They include cars, motorcycles, and bicycles.",
        contentSummary="Types of passenger vehicles",
        elementType="Subsection",
        parentElement=section1
    )
    
    subsection1_2 = KnowledgeDocumentElement(
        id="subsection1_2",
        title="Commercial Vehicles", 
        content="Commercial vehicles are used for business purposes, including trucks, buses, and delivery vans. They have different regulatory requirements.",
        contentSummary="Commercial vehicle categories and regulations",
        elementType="Subsection",
        parentElement=section1
    )
    
    section1.childElements = [subsection1_1, subsection1_2]
    
    # Create main document
    doc = KnowledgeDocument(
        id="vehicle_doc",
        title="Vehicle Knowledge Document",
        content="This document provides comprehensive information about vehicles, their classification, and regulatory frameworks.",
        contentSummary="Comprehensive guide to vehicle knowledge",
        elementType="KnowledgeDocument",
        childElements=[section1]
    )
    
    return doc


def create_simple_knowledge_document() -> KnowledgeDocument:
    """Create a simple knowledge document for basic testing."""
    return KnowledgeDocument(
        id="simple_doc",
        title="Simple Document",
        content="This is a simple document with some basic content for testing purposes.",
        contentSummary="A simple test document",
        elementType="KnowledgeDocument"
    )


# ------------------------
# Mock OpenAI for testing without API calls
# ------------------------

class MockEmbeddingResponse:
    def __init__(self, dimension=1536):
        self.data = []
        self.dimension = dimension
    
    def add_embedding(self, text: str):
        # Create a deterministic "embedding" based on text hash
        embedding = np.random.RandomState(seed=hash(text) % 2**32).normal(0, 1, self.dimension)
        embedding = embedding / np.linalg.norm(embedding)  # Normalize
        mock_item = Mock()
        mock_item.embedding = embedding.tolist()
        self.data.append(mock_item)
        return self


def mock_openai_embeddings_create(model, input):
    """Mock OpenAI embeddings.create method."""
    response = MockEmbeddingResponse()
    for text in input:
        response.add_embedding(text)
    return response


# ------------------------
# Test Classes
# ------------------------

class TestSemchunkIndexDocumentChunker:
    """Test the semchunk-based document chunker."""
    
    def setUp(self):
        self.chunker = SemchunkIndexDocumentChunker(chunk_size=200, target_model="gpt-4.1")

    def test_chunk_simple_document(self):
        """Test chunking a simple index document."""
        self.setUp()
        
        index_doc = IndexDocument(
            id="test_doc",
            element_id="element1", 
            content="This is a test document with some content. It has multiple sentences. Each sentence provides different information.",
            element_type="Document"
        )
        
        chunks = self.chunker.get_text_chunks(index_doc)
        
        assert len(chunks) > 0, "Should create at least one chunk"
        assert all(chunk.document_id == index_doc.id for chunk in chunks), "All chunks should reference the source document"
        assert all(chunk.chunk_id is not None for chunk in chunks), "All chunks should have unique IDs"
        assert all(isinstance(chunk.start_offset, int) for chunk in chunks), "All chunks should have valid start offsets"
        assert all(isinstance(chunk.end_offset, int) for chunk in chunks), "All chunks should have valid end offsets"
        
        print(f"Created {len(chunks)} chunks from test document")
        for i, chunk in enumerate(chunks):
            print(f"Chunk {i+1}: {chunk.text[:50]}...")
    
    def test_chunk_empty_document(self):
        """Test chunking an empty index document."""
        self.setUp()
        
        index_doc = IndexDocument(
            id="empty_doc",
            element_id="element1",
            content="",
            element_type="Document"
        )
        
        chunks = self.chunker.get_text_chunks(index_doc)
        assert len(chunks) == 0, "Empty document should produce no chunks"
    
    def test_chunk_none_content(self):
        """Test chunking a document with None content."""
        self.setUp()
        
        index_doc = IndexDocument(
            id="none_doc",
            element_id="element1",
            content=None,
            element_type="Document"
        )
        
        chunks = self.chunker.get_text_chunks(index_doc)
        assert len(chunks) == 0, "Document with None content should produce no chunks"


class TestFAISSKnowledgeDocumentIndexer:
    """Test the FAISS-based knowledge document indexer."""
    
    def setUp(self):
        # Use mock OpenAI client for testing
        with patch('knowledge_base_index.indexers.faiss_indexer.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.embeddings.create = mock_openai_embeddings_create
            mock_openai.return_value = mock_client
            
            self.indexer = FAISSFullTextOpenAIKnowledgeDocumentIndexer(
                target_model="gpt-4.1",
                chunk_size=200,
                embedding_model="text-embedding-3-small",
                embedding_dimension=384,# Smaller dimension for faster testing
                
            )
            self.indexer.embedding_dimension = 384
            self.indexer.faiss_index = __import__('faiss').IndexFlatIP(384)
    
    def test_create_index_documents(self):
        """Test creation of IndexDocument objects from KnowledgeDocument."""
        self.setUp()
        
        knowledge_doc = create_test_knowledge_document()
        
        # Access the private method for testing
        index_docs = self.indexer._create_index_documents(knowledge_doc)
        
        assert len(index_docs) > 0, "Should create index documents from knowledge document"
        
        # Verify index documents have required fields
        for index_doc in index_docs:
            assert index_doc.id is not None, "Index document should have ID"
            assert index_doc.element_id is not None, "Index document should have element ID"
            assert index_doc.content is not None, "Index document should have content"
            assert index_doc.element_type is not None, "Index document should have element type"
        
        print(f"Created {len(index_docs)} index documents")
        for i, doc in enumerate(index_docs):
            print(f"IndexDoc {i+1}: {doc.element_type} - {doc.element_id}")
            print(f"  Content: {doc.content[:100]}...")
    
    def test_build_index_simple(self):
        """Test building index with a simple knowledge document."""
        self.setUp()
        
        knowledge_doc = create_simple_knowledge_document()
        
        # Mock the embedding generation
        with patch.object(self.indexer, '_get_embeddings') as mock_embeddings:
            mock_embeddings.return_value = np.random.random((1, 384))
            
            self.indexer.build_index(knowledge_doc)
        
        assert self.indexer.faiss_index.ntotal > 0, "FAISS index should contain embeddings"
        assert len(self.indexer.chunk_metadata) > 0, "Should have chunk metadata"
        assert len(self.indexer.index_documents) > 0, "Should have index documents"
        
        print(f"Built index with {self.indexer.faiss_index.ntotal} embeddings")
        print(f"Stored {len(self.indexer.chunk_metadata)} text chunks")
        print(f"Stored {len(self.indexer.index_documents)} index documents")
    
    def test_build_index_complex(self):
        """Test building index with a complex hierarchical knowledge document.""" 
        self.setUp()
        
        knowledge_doc = create_test_knowledge_document()
        
        # Mock the embedding generation
        with patch.object(self.indexer, '_get_embeddings') as mock_embeddings:
            # Return different embeddings for each batch
            def mock_embedding_fn(texts):
                return np.random.random((len(texts), 384))
            mock_embeddings.side_effect = mock_embedding_fn
            
            self.indexer.build_index(knowledge_doc)
        
        assert self.indexer.faiss_index.ntotal > 0, "FAISS index should contain embeddings"
        assert len(self.indexer.chunk_metadata) > 0, "Should have chunk metadata"
        assert len(self.indexer.index_documents) > 0, "Should have index documents"
        
        print(f"Built complex index with {self.indexer.faiss_index.ntotal} embeddings")
        print(f"Stored {len(self.indexer.chunk_metadata)} text chunks")
        print(f"Stored {len(self.indexer.index_documents)} index documents")
    
    def test_search_functionality(self):
        """Test search functionality with mock data.""" 
        self.setUp()
        
        knowledge_doc = create_test_knowledge_document()
        
        # Mock the embedding generation for both indexing and search
        with patch.object(self.indexer, '_get_embeddings') as mock_embeddings:
            # For indexing - return different embeddings for each text
            def mock_embedding_fn(texts):
                embeddings = []
                for i, text in enumerate(texts):
                    # Create deterministic embeddings based on text content
                    embedding = np.random.RandomState(seed=hash(text) % 2**32).normal(0, 1, 384)
                    embedding = embedding / np.linalg.norm(embedding)  # Normalize
                    embeddings.append(embedding)
                return np.array(embeddings)
            
            mock_embeddings.side_effect = mock_embedding_fn
            
            # Build the index
            self.indexer.build_index(knowledge_doc)
            
            # Test search
            query = SearchQuery(
                query_text="passenger vehicles cars",
                max_results=5
            )
            
            results = self.indexer.search(query)
            
            assert isinstance(results, list), "Search should return a list"
            assert len(results) <= query.max_results, "Should not exceed max_results"
            
            # Verify result structure
            for result in results:
                assert isinstance(result.element_id, str), "Result should have element_id"
                assert isinstance(result.overall_relevance_score, float), "Result should have overall_relevance_score"
                assert isinstance(result.matching_chunks, list), "Result should have matching_chunks list"
                assert len(result.matching_chunks) > 0, "Result should have at least one matching chunk"
                
                # Verify chunk match structure
                for chunk_match in result.matching_chunks:
                    assert isinstance(chunk_match.chunk_id, str), "ChunkMatch should have chunk_id"
                    assert isinstance(chunk_match.text, str), "ChunkMatch should have text"
                    assert isinstance(chunk_match.relevance_score, float), "ChunkMatch should have relevance_score"
            
            print(f"Search returned {len(results)} results")
            for i, result in enumerate(results):
                chunk_count = len(result.matching_chunks)
                print(f"Result {i+1}: {result.element_id} (score: {result.overall_relevance_score:.3f}, {chunk_count} chunks)")
    
    def test_empty_knowledge_document(self):
        """Test handling of empty knowledge document."""
        self.setUp()
        
        empty_doc = KnowledgeDocument(
            id="empty",
            title="Empty Document",
            content="",
            contentSummary="Empty test document",
            elementType="KnowledgeDocument"
        )
        
        with patch.object(self.indexer, '_get_embeddings') as mock_embeddings:
            mock_embeddings.return_value = np.array([]).reshape(0, 384)
            
            self.indexer.build_index(empty_doc)
        
        # Should handle empty content gracefully
        assert self.indexer.faiss_index.ntotal == 0, "Empty document should not add embeddings"
        
        # Search should return empty results
        query = SearchQuery(query_text="test", max_results=5)
        results = self.indexer.search(query)
        assert len(results) == 0, "Search on empty index should return no results"


# ------------------------
# Test execution
# ------------------------

def run_chunker_tests():
    """Run chunker tests."""
    print("=" * 50)
    print("Testing SemchunkIndexDocumentChunker")
    print("=" * 50)
    
    test_class = TestSemchunkIndexDocumentChunker()
    
    try:
        test_class.test_chunk_simple_document()
        print("✓ test_chunk_simple_document passed")
    except Exception as e:
        print(f"✗ test_chunk_simple_document failed: {e}")
    
    try:
        test_class.test_chunk_empty_document()
        print("✓ test_chunk_empty_document passed")
    except Exception as e:
        print(f"✗ test_chunk_empty_document failed: {e}")
    
    try:
        test_class.test_chunk_none_content()
        print("✓ test_chunk_none_content passed")
    except Exception as e:
        print(f"✗ test_chunk_none_content failed: {e}")


def run_indexer_tests():
    """Run indexer tests."""
    print("\n" + "=" * 50)
    print("Testing FAISSKnowledgeDocumentIndexer")
    print("=" * 50)
    
    test_class = TestFAISSKnowledgeDocumentIndexer()
    
    try:
        test_class.test_create_index_documents()
        print("✓ test_create_index_documents passed")
    except Exception as e:
        print(f"✗ test_create_index_documents failed: {e}")
    
    try:
        test_class.test_build_index_simple()
        print("✓ test_build_index_simple passed")
    except Exception as e:
        print(f"✗ test_build_index_simple failed: {e}")
    
    try:
        test_class.test_build_index_complex()
        print("✓ test_build_index_complex passed")
    except Exception as e:
        print(f"✗ test_build_index_complex failed: {e}")
    
    try:
        test_class.test_search_functionality()
        print("✓ test_search_functionality passed")
    except Exception as e:
        print(f"✗ test_search_functionality failed: {e}")
    
    try:
        test_class.test_empty_knowledge_document()
        print("✓ test_empty_knowledge_document passed")
    except Exception as e:
        print(f"✗ test_empty_knowledge_document failed: {e}")


def run_integration_test():
    """Run a simple integration test."""
    print("\n" + "=" * 50)
    print("Integration Test")
    print("=" * 50)
    
    try:
        # Test the full flow without OpenAI API calls
        chunker = SemchunkIndexDocumentChunker(chunk_size=200, target_model="gpt-4.1")
        
        # Create test data
        knowledge_doc = create_test_knowledge_document()
        
        print("✓ Integration test setup completed")
        print("  Note: Full integration test requires OpenAI API key")
        
    except Exception as e:
        print(f"✗ Integration test failed: {e}")


if __name__ == "__main__":
    print("Running Knowledge Base Index Tests")
    print("Note: These tests use mocked OpenAI API calls")
    
    run_chunker_tests()
    run_indexer_tests()
    run_integration_test()
    
    print("\n" + "=" * 50)
    print("Tests completed!")
    print("For full functionality testing with real embeddings, set OPENAI_API_KEY environment variable")
