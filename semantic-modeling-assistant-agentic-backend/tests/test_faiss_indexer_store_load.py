#!/usr/bin/env python3

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from knowledge_base.domain import KnowledgeDocument, KnowledgeDocumentElement
from knowledge_base_index.indexers.faiss_fulltext_openai_indexer import FAISSFullTextOpenAIKnowledgeDocumentIndexer
from knowledge_base_index.domain import SearchQuery

def test_store_and_load_index():
    """
    Test the store_index and load_index functionality of FAISSFullTextOpenAIKnowledgeDocumentIndexer.
    """
    
    # Skip test if OpenAI API key is not available
    if not os.getenv('OPENAI_API_KEY'):
        print("SKIPPING TEST: OpenAI API key not found. Set OPENAI_API_KEY environment variable to run this test.")
        return
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        cache_dir = Path(temp_dir) / "cache"
        cache_dir.mkdir()
        cache_file_path = cache_dir / "document.cache"
        
        # Create a sample knowledge document
        child_element = KnowledgeDocumentElement(
            id="child_1",
            title="Sample Child Element",
            content="This is a sample child element content about vehicles and transportation.",
            contentSummary="Child element about vehicles",
            elementType="Section"
        )
        
        knowledge_doc = KnowledgeDocument(
            id="test_doc_1",
            title="Test Knowledge Document",
            content="This is a test knowledge document about transportation systems.",
            contentSummary="Test document about transportation",
            childElements=[child_element],
            elementType="KnowledgeDocument",
            cacheFilePath=str(cache_file_path)
        )
        
        # Set parent relationship
        child_element.parentElement = knowledge_doc
        
        print("=== Testing FAISS Indexer Store/Load Functionality ===")
        
        # Create indexer instance
        indexer = FAISSFullTextOpenAIKnowledgeDocumentIndexer(
            chunk_size=100,
            embedding_model="text-embedding-3-small"
        )
        
        print("1. Building initial index...")
        indexer.build_index(knowledge_doc)
        
        # Verify the index was built
        assert indexer.faiss_index.ntotal > 0, "Index should have been built with chunks"
        assert len(indexer.chunk_metadata) > 0, "Should have chunk metadata"
        assert len(indexer.index_documents) > 0, "Should have index documents"
        
        initial_chunk_count = len(indexer.chunk_metadata)
        print(f"   Built index with {initial_chunk_count} chunks")
        
        print("2. Testing search functionality...")
        query = SearchQuery(query_text="vehicle", max_results=5)
        results = indexer.search(query)
        print(f"   Found {len(results)} search results")
        
        print("3. Storing index to disk...")
        indexer.store_index(knowledge_doc)
        
        # Verify files were created
        index_dir = cache_dir / "indexes" / "faiss_fulltext_openai"
        assert index_dir.exists(), "Index directory should exist"
        assert (index_dir / "faiss.index").exists(), "FAISS index file should exist"
        assert (index_dir / "chunks.pkl").exists(), "Chunks metadata file should exist"
        assert (index_dir / "index_documents.json").exists(), "Index documents file should exist"
        assert (index_dir / "config.json").exists(), "Config file should exist"
        print("   Index files created successfully")
        
        print("4. Creating new indexer instance...")
        new_indexer = FAISSFullTextOpenAIKnowledgeDocumentIndexer(
            chunk_size=100,
            embedding_model="text-embedding-3-small"
        )
        
        # Verify the new indexer is empty
        assert new_indexer.faiss_index.ntotal == 0, "New indexer should be empty"
        assert len(new_indexer.chunk_metadata) == 0, "New indexer should have no metadata"
        
        print("5. Loading index from disk...")
        load_success = new_indexer.load_index(knowledge_doc)
        assert load_success, "Index loading should succeed"
        
        # Verify the loaded index matches the original
        assert new_indexer.faiss_index.ntotal == initial_chunk_count, f"Loaded index should have {initial_chunk_count} chunks"
        assert len(new_indexer.chunk_metadata) == initial_chunk_count, "Loaded metadata should match"
        assert len(new_indexer.index_documents) == len(indexer.index_documents), "Loaded index documents should match"
        print(f"   Loaded index with {len(new_indexer.chunk_metadata)} chunks")
        
        print("6. Testing search on loaded index...")
        loaded_results = new_indexer.search(query)
        assert len(loaded_results) == len(results), "Search results should match between original and loaded index"
        print(f"   Search returned {len(loaded_results)} results (same as original)")
        
        print("7. Testing build_or_load_index method...")
        third_indexer = FAISSFullTextOpenAIKnowledgeDocumentIndexer(
            chunk_size=100,
            embedding_model="text-embedding-3-small"
        )
        
        # This should load from cache since we stored it
        third_indexer.build_or_load_index(knowledge_doc)
        assert third_indexer.faiss_index.ntotal == initial_chunk_count, "build_or_load_index should load existing index"
        print("   build_or_load_index successfully loaded from cache")
        
        print("8. Testing load failure scenarios...")
        # Test with document without cacheFilePath
        doc_no_cache = KnowledgeDocument(
            id="no_cache",
            title="No Cache Document",
            content="Test document without cache path",
            contentSummary="Test document summary",
            elementType="KnowledgeDocument"
        )
        
        empty_indexer = FAISSFullTextOpenAIKnowledgeDocumentIndexer()
        load_result = empty_indexer.load_index(doc_no_cache)
        assert not load_result, "Loading should fail for document without cacheFilePath"
        print("   Correctly handled document without cacheFilePath")
        
        # Test with non-existent cache directory
        doc_bad_cache = KnowledgeDocument(
            id="bad_cache",
            title="Bad Cache Document",
            content="Test document with non-existent cache path",
            contentSummary="Test document summary",
            elementType="KnowledgeDocument",
            cacheFilePath="/nonexistent/path"
        )
        
        load_result = empty_indexer.load_index(doc_bad_cache)
        assert not load_result, "Loading should fail for non-existent cache directory"
        print("   Correctly handled non-existent cache directory")
        
        print("\n=== ALL TESTS PASSED ===")
        print("Store and load functionality is working correctly!")

if __name__ == "__main__":
    test_store_and_load_index()
