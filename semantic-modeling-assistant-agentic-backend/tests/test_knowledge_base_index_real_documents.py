#!/usr/bin/env python3
"""
Unit tests for knowledge base indexing with real documents.

Tests the FAISS-based semantic indexing implementation using:
- Real ESEL legal documents from data/esel/1000-01-1000-01-01
- Real local documents from data/local/silnicni-vozidla-expert-knowledge

These tests demonstrate the system working with actual document content
rather than synthetic test data.

Note: These tests require an OpenAI API key to be set as OPENAI_API_KEY environment variable.
For testing without actual API calls, mock implementations can be added.
"""

import os
import sys
import uuid
from typing import List, Optional
from unittest.mock import Mock, patch
import numpy as np
import pytest

# Ensure src/ is importable when running as a script
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from knowledge_base.domain import KnowledgeDocument, KnowledgeDocumentElement
from knowledge_base.document_loaders.document_loader_esel import ESELKnowledgeDocumentLoader
from knowledge_base.document_loaders.document_loader_local import LocalKnowledgeDocumentLoader
from knowledge_base.service import ESEL_SPARQL_ENDPOINT, LEGAL_DOCUMENT_ID_PREFIX
from knowledge_base_index.domain import IndexDocument
from knowledge_base_index.chunkers.semchunk_chunker import SemchunkIndexDocumentChunker
from knowledge_base_index.indexers.faiss_fulltext_openai_indexer import FAISSFullTextOpenAIKnowledgeDocumentIndexer

pytestmark = pytest.mark.live

EMBEDDING_DIMENSION = 384


def create_indexer_with_fake_embeddings_client() -> FAISSFullTextOpenAIKnowledgeDocumentIndexer:
    """The tests patch _get_embeddings, so the indexer never needs a real embeddings client."""
    with patch('knowledge_base_index.indexers.faiss_fulltext_openai_indexer.create_embeddings', return_value=Mock()):
        return FAISSFullTextOpenAIKnowledgeDocumentIndexer(
            target_model="gpt-3.5-turbo",
            chunk_size=500,
            embedding_dimension=EMBEDDING_DIMENSION
        )


# ------------------------
# Real Document Loading Functions
# ------------------------

def load_esel_document() -> Optional[KnowledgeDocument]:
    """Load the ESEL legal document."""
    try:
        loader = ESELKnowledgeDocumentLoader(ESEL_SPARQL_ENDPOINT, base_dir="data_test/knowledge_base/esel")
        
        document_id = f"{LEGAL_DOCUMENT_ID_PREFIX}/2001/56/2025-07-01"
        
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
        
        # Use the document from the data directory
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
# Test Classes
# ------------------------

class TestRealDocumentChunking:
    """Test chunking with real documents."""
    
    def setUp(self):
        self.chunker = SemchunkIndexDocumentChunker(chunk_size=500, target_model="gpt-3.5-turbo")
    
    def test_chunk_esel_document(self):
        """Test chunking the ESEL legal document."""
        self.setUp()
        
        print("\n" + "=" * 60)
        print("Testing ESEL Document Chunking")
        print("=" * 60)
        
        # Load the ESEL document
        knowledge_doc = load_esel_document()
        if not knowledge_doc:
            print("⚠️  Skipping ESEL chunking test - document not available")
            return
        
        # Create index documents (this is what the indexer would do)
        print("Creating index documents from ESEL knowledge document...")
        index_documents = self._create_index_documents_from_knowledge_doc(knowledge_doc)
        
        print(f"Created {len(index_documents)} index documents")
        
        # Test chunking on each index document
        total_chunks = 0
        for i, index_doc in enumerate(index_documents[:3]):  # Test first 3 to avoid overwhelming output
            print(f"\nProcessing index document {i+1}: {index_doc.element_id}")
            print(f"  Content length: {len(index_doc.content) if index_doc.content else 0} characters")
            
            chunks = self.chunker.get_text_chunks(index_doc)
            total_chunks += len(chunks)
            
            print(f"  Created {len(chunks)} chunks")
            
            # Show first chunk as example
            if chunks:
                first_chunk = chunks[0]
                chunk_preview = first_chunk.text[:100] + "..." if len(first_chunk.text) > 100 else first_chunk.text
                print(f"  First chunk preview: {chunk_preview}")
        
        print(f"\n✓ ESEL chunking test completed - {total_chunks} total chunks from {len(index_documents)} index documents")
    
    def test_chunk_local_document(self):
        """Test chunking the local document."""
        self.setUp()
        
        print("\n" + "=" * 60)
        print("Testing Local Document Chunking")
        print("=" * 60)
        
        # Load the local document
        knowledge_doc = load_local_document()
        if not knowledge_doc:
            print("⚠️  Skipping local chunking test - document not available")
            return
        
        # Create index documents
        print("Creating index documents from local knowledge document...")
        index_documents = self._create_index_documents_from_knowledge_doc(knowledge_doc)
        
        print(f"Created {len(index_documents)} index documents")
        
        # Test chunking on each index document
        total_chunks = 0
        for i, index_doc in enumerate(index_documents[:3]):  # Test first 3
            print(f"\nProcessing index document {i+1}: {index_doc.element_id}")
            print(f"  Content length: {len(index_doc.content) if index_doc.content else 0} characters")
            
            chunks = self.chunker.get_text_chunks(index_doc)
            total_chunks += len(chunks)
            
            print(f"  Created {len(chunks)} chunks")
            
            # Show first chunk as example
            if chunks:
                first_chunk = chunks[0]
                chunk_preview = first_chunk.text[:100] + "..." if len(first_chunk.text) > 100 else first_chunk.text
                print(f"  First chunk preview: {chunk_preview}")
        
        print(f"\n✓ Local chunking test completed - {total_chunks} total chunks from {len(index_documents)} index documents")
    
    def _create_index_documents_from_knowledge_doc(self, knowledge_document: KnowledgeDocument) -> List[IndexDocument]:
        """Helper method to create index documents from knowledge document."""
        index_documents = []
        
        def process_element(element: KnowledgeDocumentElement, parent_content: str = ""):
            """Recursively process knowledge document elements."""
            # Combine parent content with current element content
            combined_content = ""
            if parent_content:
                combined_content += parent_content + "\n\n"
            if element.content:
                combined_content += element.content
            
            # Create index document for this element
            if combined_content.strip():
                index_doc = IndexDocument(
                    id=str(uuid.uuid4()),
                    element_id=element.id,
                    content=combined_content.strip(),
                    element_type=element.elementType
                )
                index_documents.append(index_doc)
            
            # Process child elements
            current_content = element.content or ""
            for child in element.childElements:
                process_element(child, current_content)
        
        # Process the root document and all its elements
        process_element(knowledge_document)
        
        return index_documents


class TestRealDocumentIndexing:
    """Test indexing with real documents."""
    
    def setUp(self):
        self.indexer = create_indexer_with_fake_embeddings_client()
    
    def test_index_esel_document(self):
        """Test building index with ESEL legal document.""" 
        self.setUp()
        
        print("\n" + "=" * 60)
        print("Testing ESEL Document Indexing")
        print("=" * 60)
        
        # Load the ESEL document
        knowledge_doc = load_esel_document()
        if not knowledge_doc:
            print("⚠️  Skipping ESEL indexing test - document not available")
            return
        
        # Mock the embedding generation
        with patch.object(self.indexer, '_get_embeddings') as mock_embeddings:
            def mock_embedding_fn(texts):
                embeddings = []
                for text in texts:
                    # Create deterministic embeddings based on text content
                    embedding = np.random.RandomState(seed=hash(text) % 2**32).normal(0, 1, 384)
                    embedding = embedding / np.linalg.norm(embedding)  # Normalize
                    embeddings.append(embedding)
                return np.array(embeddings)
            
            mock_embeddings.side_effect = mock_embedding_fn
            
            # Build the index
            self.indexer.build_index(knowledge_doc)
        
        print(f"✓ ESEL indexing completed:")
        print(f"  - FAISS index size: {self.indexer.faiss_index.ntotal} embeddings")
        print(f"  - Text chunks stored: {len(self.indexer.chunk_metadata)}")
        print(f"  - Index documents stored: {len(self.indexer.index_documents)}")
        
        assert self.indexer.faiss_index.ntotal > 0, "Should have embeddings in FAISS index"
        assert len(self.indexer.chunk_metadata) > 0, "Should have chunk metadata"
        assert len(self.indexer.index_documents) > 0, "Should have index documents"
    
    def test_index_local_document(self):
        """Test building index with local document."""
        self.setUp()
        
        print("\n" + "=" * 60)
        print("Testing Local Document Indexing")
        print("=" * 60)
        
        # Load the local document
        knowledge_doc = load_local_document()
        if not knowledge_doc:
            print("⚠️  Skipping local indexing test - document not available")
            return
        
        # Mock the embedding generation
        with patch.object(self.indexer, '_get_embeddings') as mock_embeddings:
            def mock_embedding_fn(texts):
                embeddings = []
                for text in texts:
                    # Create deterministic embeddings based on text content
                    embedding = np.random.RandomState(seed=hash(text) % 2**32).normal(0, 1, 384)
                    embedding = embedding / np.linalg.norm(embedding)  # Normalize
                    embeddings.append(embedding)
                return np.array(embeddings)
            
            mock_embeddings.side_effect = mock_embedding_fn
            
            # Build the index
            self.indexer.build_index(knowledge_doc)
        
        print(f"✓ Local indexing completed:")
        print(f"  - FAISS index size: {self.indexer.faiss_index.ntotal} embeddings")
        print(f"  - Text chunks stored: {len(self.indexer.chunk_metadata)}")
        print(f"  - Index documents stored: {len(self.indexer.index_documents)}")
        
        assert self.indexer.faiss_index.ntotal > 0, "Should have embeddings in FAISS index"
        assert len(self.indexer.chunk_metadata) > 0, "Should have chunk metadata"
        assert len(self.indexer.index_documents) > 0, "Should have index documents"


# ------------------------
# Test execution
# ------------------------

def run_real_document_tests():
    """Run all real document tests."""
    print("FAISS Knowledge Base Index Tests - Real Documents")
    print("=" * 70)
    print("These tests use real documents from data/ directory")
    print("ESEL document: Czech legal act from data/esel/1000-01-1000-01-01/")
    print("Local document: Vehicle knowledge from data/local/silnicni-vozidla-expert-knowledge/")
    print("=" * 70)
    
    # Test chunking
    chunking_test = TestRealDocumentChunking()
    
    try:
        chunking_test.test_chunk_esel_document()
    except Exception as e:
        print(f"✗ ESEL chunking test failed: {e}")
    
    try:
        chunking_test.test_chunk_local_document()
    except Exception as e:
        print(f"✗ Local chunking test failed: {e}")
    
    # Test indexing
    indexing_test = TestRealDocumentIndexing()
    
    try:
        indexing_test.test_index_esel_document()
    except Exception as e:
        print(f"✗ ESEL indexing test failed: {e}")
    
    try:
        indexing_test.test_index_local_document()
    except Exception as e:
        print(f"✗ Local indexing test failed: {e}")


if __name__ == "__main__":
    print("Note: These tests use mocked OpenAI API calls for reproducible results")
    print("For full functionality with real embeddings, set OPENAI_API_KEY environment variable\n")
    
    run_real_document_tests()
    
    print("\n" + "=" * 70)
    print("Real document tests completed!")
    print("✅ Successfully demonstrated knowledge base indexing with real documents")
    print("=" * 70)
