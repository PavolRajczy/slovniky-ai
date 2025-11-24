#!/usr/bin/env python3
"""
Test script for LocalKnowledgeDocumentLoader
"""

import sys
import os
from pathlib import Path

# Add the src directory to the path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from knowledge_base.document_loaders.document_loader_local import LocalKnowledgeDocumentLoader


def test_local_document_loader():
    """Test the LocalKnowledgeDocumentLoader with a sample document."""
    
    print("Testing LocalKnowledgeDocumentLoader...")
    
    # Initialize the loader
    loader = LocalKnowledgeDocumentLoader(base_dir="data_test/knowledge_base/local")
    
    # Test document ID
    document_id = "https://localhost/silnicni-vozidla-expert-knowledge.docx"
    
    try:
        # Load the document
        print(f"Loading document: {document_id}")
        doc = loader.load_document(document_id)
        
        if doc:
            print("✅ Document loaded successfully!")
            print(f"Document ID: {doc.id}")
            print(f"Document Title: {doc.title}")
            print(f"Document Type: {doc.elementType}")
            print(f"Content length: {len(doc.content) if doc.content else 0} characters")
            print("\nFirst 200 characters of content:")
            print(doc.content[:200] if doc.content else "No content")
            print("...")
            return True
        else:
            print("❌ Document loading returned None")
            return False
            
    except Exception as e:
        print(f"❌ Error loading document: {e}")
        return False


def test_invalid_document_id():
    """Test the loader with invalid document ID format."""
    
    print("\nTesting invalid document ID format...")
    
    loader = LocalKnowledgeDocumentLoader(base_dir="data_test/knowledge_base/local")
    invalid_id = "invalid-format"
    
    try:
        doc = loader.load_document(invalid_id)
        print("❌ Should have raised ValueError for invalid format")
        return False
    except ValueError as e:
        print(f"✅ Correctly raised ValueError: {e}")
        return True
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_nonexistent_file():
    """Test the loader with a non-existent file."""
    
    print("\nTesting non-existent file...")
    
    loader = LocalKnowledgeDocumentLoader(base_dir="data_test/knowledge_base/local")
    missing_file_id = "https://localhost/nonexistent-file.txt"
    
    try:
        doc = loader.load_document(missing_file_id)
        print("❌ Should have raised FileNotFoundError for missing file")
        return False
    except FileNotFoundError as e:
        print(f"✅ Correctly raised FileNotFoundError: {e}")
        return True
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    print("Running LocalKnowledgeDocumentLoader tests...\n")
    
    test_results = []
    test_results.append(test_local_document_loader())
    test_results.append(test_invalid_document_id())
    test_results.append(test_nonexistent_file())
    
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"\nTest Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("💥 Some tests failed!")
        sys.exit(1)
