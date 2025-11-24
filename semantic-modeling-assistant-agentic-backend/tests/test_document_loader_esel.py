#!/usr/bin/env python3
"""
Simple test script to verify the EselKnowledgeDocumentLoader implementation.
"""

import sys
import os
from pathlib import Path

# Add the src directory to the path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from knowledge_base.document_loaders.document_loader_esel import ESELKnowledgeDocumentLoader
from knowledge_base.domain import KnowledgeDocument

def test_loader_initialization():
    """Test that the loader can be initialized."""
    print("Testing loader initialization...")
    
    sparql_endpoint = "https://opendata.eselpoint.cz/sparql"
    loader = ESELKnowledgeDocumentLoader(sparql_endpoint, base_dir="data_test/knowledge_base/esel")
    
    assert loader.sparql_endpoint == sparql_endpoint
    print("✓ Loader initialization successful")

def test_load_document_without_cache():
    """Test loading a real document from the SPARQL endpoint when cache is empty."""
    print("Testing loading document without cache...")
    
    sparql_endpoint = "https://opendata.eselpoint.cz/sparql"
    loader = ESELKnowledgeDocumentLoader(sparql_endpoint, base_dir="data_test/knowledge_base/esel")
    
    # Test document ID provided by the user
    document_id = "https://opendata.eselpoint.cz/esel-esb/eli/cz/sb/2001/56/2025-07-01"
    
    # Ensure cache files are not present - delete them if they exist
    document_cache_dir = loader._get_document_cache_dir(document_id)
    cache_filename = loader._extract_cache_filename(document_id)
    # Remove .json extension to get base name for split cache
    cache_base_path = document_cache_dir / Path(cache_filename).stem
    
    # Import CacheManager to get split cache paths
    from knowledge_base.utils.cache_manager import CacheManager
    content_path, metadata_path = CacheManager.get_split_cache_paths(cache_base_path)
    
    if content_path.exists():
        print(f"  - Removing existing content cache file: {content_path}")
        content_path.unlink()
    if metadata_path.exists():
        print(f"  - Removing existing metadata cache file: {metadata_path}")
        metadata_path.unlink()
    
    # Verify cache files don't exist
    assert not content_path.exists(), f"Content cache file should not exist: {content_path}"
    assert not metadata_path.exists(), f"Metadata cache file should not exist: {metadata_path}"
    print(f"  - Verified cache files are not present: {cache_filename}")
    
    print(f"Loading document from SPARQL endpoint: {document_id}")
    document = loader.load_document(document_id)
    
    # Verify that the document was loaded
    assert document is not None, "Document should not be None"
    assert isinstance(document, KnowledgeDocument), "Document should be a KnowledgeDocument instance"
    
    # Verify basic properties
    assert document.id == document_id, f"Document ID should match: expected {document_id}, got {document.id}"
    print(f"  - Actual element type: {document.elementType}")
    # The document should be a KnowledgeDocument instance, but element type might be more specific
    assert document.elementType in ["KnowledgeDocument", "LegalAct"], f"Element type should be KnowledgeDocument or LegalAct, got {document.elementType}"
    
    # Verify that cache files were created after loading
    assert content_path.exists(), f"Content cache file should have been created: {content_path}"
    print(f"  - Verified content cache file was created: {content_path.name}")
    # Metadata file may or may not exist initially since documents start without ontology metadata
    print(f"  - Metadata cache file exists: {metadata_path.exists()}")
    
    # Print some basic information about the loaded document
    print(f"✓ Document loaded successfully from SPARQL endpoint")
    print(f"  - ID: {document.id}")
    print(f"  - Title: {document.title if document.title else '(no title)'}")
    print(f"  - Element Type: {document.elementType}")
    print(f"  - Number of child elements: {len(document.childElements)}")
    
    if document.content:
        content_preview = document.content[:200] + "..." if len(document.content) > 200 else document.content
        print(f"  - Content preview: {content_preview}")
    else:
        print(f"  - Content: (no direct content - structured document)")
    
    # Verify that we have some structure in the document
    print(f"  - Child elements found: {len(document.childElements)}")
    if document.childElements:
        print(f"  - Document structure:")
        for i, child in enumerate(document.childElements[:5]):  # Show first 5 children
            print(f"    [{i+1}] {child.elementType}: {child.title}")
        if len(document.childElements) > 5:
            print(f"    ... and {len(document.childElements) - 5} more")
    
    # Additional verification that this is a real, structured legal document
    assert len(document.childElements) > 0, "Document should have child elements"
    print(f"✓ Document structure verification passed - found {len(document.childElements)} parts")

def test_load_document_from_cache():
    """Test loading a document from cache when cache file exists."""
    print("Testing loading document from cache...")
    
    sparql_endpoint = "https://opendata.eselpoint.cz/sparql"
    loader = ESELKnowledgeDocumentLoader(sparql_endpoint, base_dir="data_test/knowledge_base/esel")
    
    # Test document ID provided by the user
    document_id = "https://opendata.eselpoint.cz/esel-esb/eli/cz/sb/2001/56/2025-07-01"
    
    # Verify cache files exist (should have been created by previous test)
    document_cache_dir = loader._get_document_cache_dir(document_id)
    cache_filename = loader._extract_cache_filename(document_id)
    # Remove .json extension to get base name for split cache
    cache_base_path = document_cache_dir / Path(cache_filename).stem
    
    # Import CacheManager to get split cache paths
    from knowledge_base.utils.cache_manager import CacheManager
    content_path, metadata_path = CacheManager.get_split_cache_paths(cache_base_path)
    
    assert content_path.exists(), f"Content cache file should exist from previous test: {content_path}"
    print(f"  - Verified content cache file exists: {content_path.name}")
    
    # Get cache file modification time to verify it's not updated during load
    content_mtime_before = content_path.stat().st_mtime
    
    print(f"Loading document from cache: {document_id}")
    document = loader.load_document(document_id)
    
    # Verify that the document was loaded
    assert document is not None, "Document should not be None"
    assert isinstance(document, KnowledgeDocument), "Document should be a KnowledgeDocument instance"
    
    # Verify basic properties
    assert document.id == document_id, f"Document ID should match: expected {document_id}, got {document.id}"
    print(f"  - Actual element type: {document.elementType}")
    # The document should be a KnowledgeDocument instance, but element type might be more specific
    assert document.elementType in ["KnowledgeDocument", "LegalAct"], f"Element type should be KnowledgeDocument or LegalAct, got {document.elementType}"
    
    # Verify cache file was not modified (loaded from cache, not from SPARQL)
    content_mtime_after = content_path.stat().st_mtime
    assert content_mtime_before == content_mtime_after, "Content cache file should not have been modified when loading from cache"
    print(f"  - Verified document was loaded from cache (content file not modified)")
    
    # Print some basic information about the loaded document
    print(f"✓ Document loaded successfully from cache")
    print(f"  - ID: {document.id}")
    print(f"  - Title: {document.title if document.title else '(no title)'}")
    print(f"  - Element Type: {document.elementType}")
    print(f"  - Number of child elements: {len(document.childElements)}")
    
    if document.content:
        content_preview = document.content[:200] + "..." if len(document.content) > 200 else document.content
        print(f"  - Content preview: {content_preview}")
    else:
        print(f"  - Content: (no direct content - structured document)")
    
    # Verify that we have some structure in the document
    print(f"  - Child elements found: {len(document.childElements)}")
    if document.childElements:
        print(f"  - Document structure:")
        for i, child in enumerate(document.childElements[:5]):  # Show first 5 children
            print(f"    [{i+1}] {child.elementType}: {child.title}")
        if len(document.childElements) > 5:
            print(f"    ... and {len(document.childElements) - 5} more")
    
    # Additional verification that this is a real, structured legal document
    assert len(document.childElements) > 0, "Document should have child elements"
    print(f"✓ Document structure verification passed - found {len(document.childElements)} parts")

def run_tests():
    """Run all tests."""
    print("Running ESELKnowledgeDocumentLoader tests...")
    print("=" * 50)
    
    try:
        test_loader_initialization()
        test_load_document_without_cache()
        test_load_document_from_cache()
        
        print("=" * 50)
        print("🎉 All tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    run_tests()