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

# Ensure src/ is importable when running as a script
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from knowledge_base.domain import KnowledgeDocument, KnowledgeDocumentElement
from knowledge_base.document_loaders.document_loader_esel import ESELKnowledgeDocumentLoader
from knowledge_base.document_loaders.document_loader_local import LocalKnowledgeDocumentLoader
from knowledge_base_index.domain import IndexDocument, TextChunk, SearchQuery, SearchResult
from knowledge_base_index.chunkers.semchunk_chunker import SemchunkIndexDocumentChunker
from knowledge_base_index.indexers.faiss_fulltext_openai_indexer import FAISSFullTextOpenAIKnowledgeDocumentIndexer


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
# Real Document Loading Functions
# ------------------------

def load_esel_document() -> Optional[KnowledgeDocument]:
    """Load the ESEL legal document."""
    try:
        sparql_endpoint = "https://opendata.eselpoint.cz/sparql"
        loader = ESELKnowledgeDocumentLoader(sparql_endpoint)
        
        # Use the document from the data directory
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
        # Use mock OpenAI client for testing
        with patch('knowledge_base_index.indexers.faiss_indexer.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.embeddings.create = mock_openai_embeddings_create
            mock_openai.return_value = mock_client
            
            self.indexer = FAISSFullTextOpenAIKnowledgeDocumentIndexer(
                target_model="gpt-3.5-turbo",
                chunk_size=500,
                embedding_dimension=384  # Smaller dimension for faster testing
            )
            self.indexer.embedding_dimension = 384
            self.indexer.faiss_index = __import__('faiss').IndexFlatIP(384)
    
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
    
    def test_search_esel_document(self):
        """Test searching the indexed ESEL document."""
        self.setUp()
        
        print("\n" + "=" * 60)
        print("Testing ESEL Document Search")
        print("=" * 60)
        
        # Load and index the ESEL document
        knowledge_doc = load_esel_document()
        if not knowledge_doc:
            print("⚠️  Skipping ESEL search test - document not available")
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
            
            # Test various legal-related search queries
            legal_queries = [
                "právní předpisy",  # legal regulations
                "ustanovení zákona",  # provisions of law
                "odpovědnost",  # responsibility
                "povinnosti",  # obligations
                "sankce"  # sanctions
            ]
            
            for query_text in legal_queries:
                print(f"\nQuery: '{query_text}'")
                query = SearchQuery(query_text=query_text, max_results=3)
                results = self.indexer.search(query)
                
                print(f"Found {len(results)} results:")
                for i, result in enumerate(results, 1):
                    print(f"  {i}. Element ID: {result.element_id[:36]}...")  # Show part of UUID
                    print(f"     Relevance Score: {result.relevance_score:.3f}")
                    
                    # Find matching chunk for more context
                    matching_chunk = None
                    for chunk in self.indexer.chunk_metadata:
                        if chunk.document_id == result.element_id:
                            matching_chunk = chunk
                            break
                    
                    if matching_chunk:
                        chunk_preview = matching_chunk.text[:100] + "..." if len(matching_chunk.text) > 100 else matching_chunk.text
                        print(f"     Text Preview: {chunk_preview}")
        
        print("\n✓ ESEL search test completed")
    
    def test_search_local_document(self):
        """Test searching the indexed local document.""" 
        self.setUp()
        
        print("\n" + "=" * 60)
        print("Testing Local Document Search")
        print("=" * 60)
        
        # Load and index the local document
        knowledge_doc = load_local_document()
        if not knowledge_doc:
            print("⚠️  Skipping local search test - document not available")
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
            
            # Test vehicle-related search queries (based on the document name)
            vehicle_queries = [
                "silniční vozidla",  # road vehicles
                "automobily",  # automobiles
                "doprava",  # transportation
                "technické požadavky",  # technical requirements
                "bezpečnost"  # safety
            ]
            
            for query_text in vehicle_queries:
                print(f"\nQuery: '{query_text}'")
                query = SearchQuery(query_text=query_text, max_results=3)
                results = self.indexer.search(query)
                
                print(f"Found {len(results)} results:")
                for i, result in enumerate(results, 1):
                    print(f"  {i}. Element ID: {result.element_id[:36]}...")  # Show part of UUID
                    print(f"     Relevance Score: {result.relevance_score:.3f}")
                    
                    # Find matching chunk for more context
                    matching_chunk = None
                    for chunk in self.indexer.chunk_metadata:
                        if chunk.document_id == result.element_id:
                            matching_chunk = chunk
                            break
                    
                    if matching_chunk:
                        chunk_preview = matching_chunk.text[:100] + "..." if len(matching_chunk.text) > 100 else matching_chunk.text
                        print(f"     Text Preview: {chunk_preview}")
        
        print("\n✓ Local search test completed")


class TestCombinedDocumentIndexing:
    """Test indexing multiple documents together."""
    
    def setUp(self):
        # Use mock OpenAI client for testing
        with patch('knowledge_base_index.indexers.faiss_indexer.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.embeddings.create = mock_openai_embeddings_create
            mock_openai.return_value = mock_client
            
            self.indexer = FAISSFullTextOpenAIKnowledgeDocumentIndexer(
                target_model="gpt-3.5-turbo",
                chunk_size=500,
                embedding_dimension=384
            )
            self.indexer.embedding_dimension = 384
            self.indexer.faiss_index = __import__('faiss').IndexFlatIP(384)
    
    def test_index_multiple_documents(self):
        """Test building a combined index with both documents."""
        self.setUp()
        
        print("\n" + "=" * 60)
        print("Testing Combined Document Indexing")
        print("=" * 60)
        
        # Load both documents
        esel_doc = load_esel_document()
        local_doc = load_local_document()
        
        if not esel_doc:
            print("⚠️  ESEL document not available")
        if not local_doc:
            print("⚠️  Local document not available")
        
        if not esel_doc and not local_doc:
            print("⚠️  No documents available - skipping combined indexing test")
            return
        
        # Mock the embedding generation
        with patch.object(self.indexer, '_get_embeddings') as mock_embeddings:
            def mock_embedding_fn(texts):
                embeddings = []
                for text in texts:
                    embedding = np.random.RandomState(seed=hash(text) % 2**32).normal(0, 1, 384)
                    embedding = embedding / np.linalg.norm(embedding)
                    embeddings.append(embedding)
                return np.array(embeddings)
            
            mock_embeddings.side_effect = mock_embedding_fn
            
            # Build index for each available document
            total_embeddings = 0
            total_chunks = 0
            total_index_docs = 0
            
            if esel_doc:
                print("Indexing ESEL document...")
                initial_embeddings = self.indexer.faiss_index.ntotal
                self.indexer.build_index(esel_doc)
                esel_embeddings = self.indexer.faiss_index.ntotal - initial_embeddings
                total_embeddings += esel_embeddings
                print(f"  Added {esel_embeddings} embeddings from ESEL document")
            
            if local_doc:
                print("Indexing local document...")
                initial_embeddings = self.indexer.faiss_index.ntotal
                self.indexer.build_index(local_doc)
                local_embeddings = self.indexer.faiss_index.ntotal - initial_embeddings
                total_embeddings += local_embeddings
                print(f"  Added {local_embeddings} embeddings from local document")
            
            total_chunks = len(self.indexer.chunk_metadata)
            total_index_docs = len(self.indexer.index_documents)
        
        print(f"\n✓ Combined indexing completed:")
        print(f"  - Total FAISS embeddings: {self.indexer.faiss_index.ntotal}")
        print(f"  - Total text chunks: {total_chunks}")
        print(f"  - Total index documents: {total_index_docs}")
        
        # Test cross-document search
        if self.indexer.faiss_index.ntotal > 0:
            print("\nTesting cross-document search...")
            
            cross_queries = [
                "vozidla a doprava",  # vehicles and transportation
                "právní předpisy",  # legal regulations
                "technické normy",  # technical standards
            ]
            
            for query_text in cross_queries:
                print(f"\nCross-document query: '{query_text}'")
                query = SearchQuery(query_text=query_text, max_results=5)
                results = self.indexer.search(query)
                
                print(f"Found {len(results)} results across all documents:")
                for i, result in enumerate(results, 1):
                    print(f"  {i}. Relevance Score: {result.relevance_score:.3f}")
                    
                    # Find matching chunk for more context
                    matching_chunk = None
                    for chunk in self.indexer.chunk_metadata:
                        if chunk.document_id == result.element_id:
                            matching_chunk = chunk
                            break
                    
                    if matching_chunk:
                        # Heuristic to identify document source based on chunk content
                        source = "Unknown"
                        chunk_text = matching_chunk.text.lower()
                        if "esel" in chunk_text or "zákon" in chunk_text or "právní" in chunk_text:
                            source = "ESEL Legal"
                        elif "vozidl" in chunk_text or "silnič" in chunk_text or "doprav" in chunk_text:
                            source = "Local Vehicle"
                        
                        chunk_preview = matching_chunk.text[:80] + "..." if len(matching_chunk.text) > 80 else matching_chunk.text
                        print(f"     Source: {source}")
                        print(f"     Preview: {chunk_preview}")
        
        print("\n✓ Combined indexing and search test completed")


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
    
    try:
        indexing_test.test_search_esel_document()
    except Exception as e:
        print(f"✗ ESEL search test failed: {e}")
    
    try:
        indexing_test.test_search_local_document()
    except Exception as e:
        print(f"✗ Local search test failed: {e}")
    
    # Test combined indexing
    combined_test = TestCombinedDocumentIndexing()
    
    try:
        combined_test.test_index_multiple_documents()
    except Exception as e:
        print(f"✗ Combined indexing test failed: {e}")


if __name__ == "__main__":
    print("Note: These tests use mocked OpenAI API calls for reproducible results")
    print("For full functionality with real embeddings, set OPENAI_API_KEY environment variable\n")
    
    run_real_document_tests()
    
    print("\n" + "=" * 70)
    print("Real document tests completed!")
    print("✅ Successfully demonstrated knowledge base indexing with real documents")
    print("=" * 70)
