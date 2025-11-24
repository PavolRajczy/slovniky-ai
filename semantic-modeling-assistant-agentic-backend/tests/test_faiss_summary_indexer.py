#!/usr/bin/env python3

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from knowledge_base.domain import KnowledgeDocument, KnowledgeDocumentElement
from knowledge_base_index.indexers.faiss_summary_openai_indexer import FAISSSummaryOpenAIKnowledgeDocumentIndexer
from knowledge_base_index.indexers.faiss_fulltext_openai_indexer import FAISSFullTextOpenAIKnowledgeDocumentIndexer
from knowledge_base_index.domain import SearchQuery

def test_summary_indexer_basic_functionality():
    """
    Test the basic functionality of FAISSSummaryOpenAIKnowledgeDocumentIndexer.
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
        
        # Create a sample knowledge document with different content and contentSummary
        child_element = KnowledgeDocumentElement(
            id="child_1",
            title="Vehicle Regulations",
            content="According to the traffic law section 123.45.67, all motor vehicles must be registered with the appropriate authorities before use on public roads. This includes cars, trucks, motorcycles, and other motorized vehicles. The registration process involves submitting form VR-1234 along with proof of insurance, vehicle inspection certificate, and payment of registration fees. Failure to comply with these regulations may result in fines ranging from $100 to $500 and potential vehicle impoundment.",
            contentSummary="Vehicle registration requirements and penalties for non-compliance",
            elementType="Section"
        )
        
        child_element2 = KnowledgeDocumentElement(
            id="child_2", 
            title="Driver License Requirements",
            content="Chapter 8 of the motor vehicle code states that all drivers must possess a valid driver's license issued by the state motor vehicle department. The licensing process includes written examination covering traffic laws, road signs, and safe driving practices, followed by a practical driving test administered by certified examiners. Applicants must be at least 16 years old for a learner's permit and 18 years old for a full license. Medical clearance may be required for applicants over 65 years of age.",
            contentSummary="Driver licensing process and age requirements",
            elementType="Section"
        )
        
        knowledge_doc = KnowledgeDocument(
            id="test_doc_summary",
            title="Transportation Legal Framework",
            content="This comprehensive document covers all aspects of transportation law including vehicle regulations, driver requirements, and traffic enforcement procedures as established by the state legislature and department of motor vehicles.",
            contentSummary="Overview of transportation laws and regulations",
            childElements=[child_element, child_element2],
            elementType="KnowledgeDocument",
            cacheFilePath=str(cache_file_path)
        )
        
        # Set parent relationships
        child_element.parentElement = knowledge_doc
        child_element2.parentElement = knowledge_doc
        
        print("=== Testing Summary Indexer Basic Functionality ===")
        
        # Create summary indexer instance
        summary_indexer = FAISSSummaryOpenAIKnowledgeDocumentIndexer(
            chunk_size=100,
            embedding_model="text-embedding-3-small"
        )
        
        print("1. Building summary index...")
        summary_indexer.build_index(knowledge_doc)
        
        # Verify the index was built
        assert summary_indexer.faiss_index.ntotal > 0, "Summary index should have been built with chunks"
        assert len(summary_indexer.chunk_metadata) > 0, "Should have chunk metadata"
        assert len(summary_indexer.index_documents) > 0, "Should have index documents"
        
        summary_chunk_count = len(summary_indexer.chunk_metadata)
        print(f"   Built summary index with {summary_chunk_count} chunks")
        
        # Verify that index documents contain summary content, not full content
        for idx_doc in summary_indexer.index_documents.values():
            print(f"   Index document content: '{idx_doc.content[:50]}...'")
            # The content should be from contentSummary, not the full content
            assert "registration requirements" in idx_doc.content or "licensing process" in idx_doc.content or "transportation laws" in idx_doc.content, \
                "Index document should contain summary content"
        
        print("2. Testing search functionality on summaries...")
        query = SearchQuery(query_text="registration", max_results=5)
        results = summary_indexer.search(query)
        print(f"   Found {len(results)} search results for 'registration'")
        
        # Search should find the vehicle registration summary
        assert len(results) > 0, "Should find results when searching for 'registration'"
        
        query2 = SearchQuery(query_text="licensing", max_results=5)  
        results2 = summary_indexer.search(query2)
        print(f"   Found {len(results2)} search results for 'licensing'")
        
        print("3. Testing store and load functionality...")
        summary_indexer.store_index(knowledge_doc)
        
        # Verify files were created in the summary indexer directory
        index_dir = cache_dir / "indexes" / "faiss_summary_openai"
        assert index_dir.exists(), "Summary index directory should exist"
        assert (index_dir / "faiss.index").exists(), "FAISS index file should exist"
        assert (index_dir / "chunks.pkl").exists(), "Chunks metadata file should exist"
        assert (index_dir / "index_documents.json").exists(), "Index documents file should exist"
        assert (index_dir / "config.json").exists(), "Config file should exist"
        
        # Verify config contains summary indexer marker
        import json
        with open(index_dir / "config.json", 'r') as f:
            config = json.load(f)
        assert config.get('indexer_type') == 'summary', "Config should mark this as a summary indexer"
        
        print("   Summary index files created successfully")
        
        # Test loading
        new_summary_indexer = FAISSSummaryOpenAIKnowledgeDocumentIndexer(
            chunk_size=100,
            embedding_model="text-embedding-3-small"
        )
        
        load_success = new_summary_indexer.load_index(knowledge_doc)
        assert load_success, "Should successfully load summary index"
        
        assert new_summary_indexer.faiss_index.ntotal == summary_chunk_count, "Loaded index should have same chunk count"
        print("   Successfully loaded summary index from disk")
        
        print("=== Summary Indexer Test PASSED ===")

def test_comparison_fulltext_vs_summary():
    """
    Test to demonstrate the difference between full-text and summary indexers.
    """
    
    # Skip test if OpenAI API key is not available
    if not os.getenv('OPENAI_API_KEY'):
        print("SKIPPING COMPARISON TEST: OpenAI API key not found.")
        return
    
    print("\n=== Comparing Full-Text vs Summary Indexers ===")
    
    # Create test document with contrasting content vs summary
    child_element = KnowledgeDocumentElement(
        id="comparison_child",
        title="Complex Legal Text",
        content="Pursuant to subsection 42.1.3.7 of the Municipal Traffic Code as amended by ordinance 2023-TX-891, any person operating a motor vehicle within city limits during hours of darkness, defined as the period from thirty minutes after sunset until thirty minutes before sunrise, must ensure that all required lighting equipment is functional and properly maintained. This includes but is not limited to headlights, taillights, brake lights, turn signals, and hazard lights. Violations of this ordinance constitute a misdemeanor punishable by fine not exceeding two hundred fifty dollars ($250) and may result in points being assessed against the operator's driving record.",
        contentSummary="Nighttime vehicle lighting requirements",
        elementType="Section"  
    )
    
    root_doc = KnowledgeDocument(
        id="comparison_doc",
        title="Traffic Lighting Regulations", 
        content="Comprehensive municipal regulations governing vehicle lighting requirements during nighttime operation within city boundaries.",
        contentSummary="Vehicle lighting rules for nighttime driving",
        childElements=[child_element],
        elementType="KnowledgeDocument",
        cacheFilePath=str(Path(tempfile.gettempdir()) / "test_cache" / "comparison.cache")
    )
    
    child_element.parentElement = root_doc
    
    # Test full-text indexer
    fulltext_indexer = FAISSFullTextOpenAIKnowledgeDocumentIndexer(chunk_size=50)
    fulltext_indexer.build_index(root_doc)
    
    # Test summary indexer  
    summary_indexer = FAISSSummaryOpenAIKnowledgeDocumentIndexer(chunk_size=50)
    summary_indexer.build_index(root_doc)
    
    print(f"Full-text indexer created {len(fulltext_indexer.chunk_metadata)} chunks")
    print(f"Summary indexer created {len(summary_indexer.chunk_metadata)} chunks")
    
    # Show what content is actually indexed
    print("\nFull-text indexed content samples:")
    for i, chunk in enumerate(fulltext_indexer.chunk_metadata[:2]):
        print(f"  Chunk {i+1}: '{chunk.text[:60]}...'")
    
    print("\nSummary indexed content samples:")  
    for i, chunk in enumerate(summary_indexer.chunk_metadata[:2]):
        print(f"  Chunk {i+1}: '{chunk.text[:60]}...'")
    
    # Test searches that should work better on summaries
    summary_query = SearchQuery(query_text="lighting requirements", max_results=3)
    
    fulltext_results = fulltext_indexer.search(summary_query)
    summary_results = summary_indexer.search(summary_query)
    
    print(f"\nSearch for 'lighting requirements':")
    print(f"  Full-text indexer found {len(fulltext_results)} results")  
    print(f"  Summary indexer found {len(summary_results)} results")
    
    if fulltext_results:
        print(f"  Full-text top result score: {fulltext_results[0].overall_relevance_score:.3f}")
    if summary_results:
        print(f"  Summary top result score: {summary_results[0].overall_relevance_score:.3f}")
    
    print("\n=== Comparison Test Complete ===")

if __name__ == "__main__":
    test_summary_indexer_basic_functionality()
    test_comparison_fulltext_vs_summary()
    print("\nAll tests completed successfully!")
