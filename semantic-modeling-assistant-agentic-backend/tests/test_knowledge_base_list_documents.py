"""
Unit tests for listing knowledge base documents.
"""
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from knowledge_base.service import KnowledgeBaseService
from knowledge_base.document_loaders.document_loader_esel import ESELKnowledgeDocumentLoader
from knowledge_base.document_loaders.document_loader_local import LocalKnowledgeDocumentLoader
from knowledge_base.document_summarizers.document_summarizer_simple_openai import SimpleOpenAIKnowledgeDocumentSummarizer


def test_list_legal_documents():
    """Test listing legal knowledge documents from the test data directory."""
    # Initialize service with test data directory
    service = KnowledgeBaseService(
        legal_knowledge_document_loader=ESELKnowledgeDocumentLoader(
            sparql_endpoint="https://opendata.eselpoint.cz/sparql",
            base_dir="data_test/knowledge_base/esel"
        ),
        expert_knowledge_document_loader=LocalKnowledgeDocumentLoader(
            base_dir="data_test/knowledge_base/local"
        ),
        document_summarizer=SimpleOpenAIKnowledgeDocumentSummarizer()
    )
    
    # List legal documents
    documents = service.list_legal_knowledge_documents(base_dir="data_test/knowledge_base/esel")
    
    print(f"\nFound {len(documents)} legal documents:")
    for doc in documents:
        print(f"  ID: {doc['id']}")
        print(f"  Title: {doc['title']}")
        print(f"  Type: {doc['elementType']}")
        summary = doc['contentSummary'] or ""
        print(f"  Summary: {summary[:100]}..." if len(summary) > 100 else f"  Summary: {summary}")
        print()
    
    # Verify we found some documents
    assert len(documents) > 0, "Should find at least one legal document in test data"
    
    # Verify each document has required fields
    for doc in documents:
        assert 'id' in doc and doc['id'], "Document should have an id"
        assert 'title' in doc, "Document should have a title field"
        assert 'contentSummary' in doc, "Document should have a contentSummary field"
        assert 'elementType' in doc and doc['elementType'], "Document should have an elementType"
    
    print("✓ Legal documents listing test passed")


def test_list_expert_documents():
    """Test listing expert knowledge documents from the test data directory."""
    # Initialize service with test data directory
    service = KnowledgeBaseService(
        legal_knowledge_document_loader=ESELKnowledgeDocumentLoader(
            sparql_endpoint="https://opendata.eselpoint.cz/sparql",
            base_dir="data_test/knowledge_base/esel"
        ),
        expert_knowledge_document_loader=LocalKnowledgeDocumentLoader(
            base_dir="data_test/knowledge_base/local"
        ),
        document_summarizer=SimpleOpenAIKnowledgeDocumentSummarizer()
    )
    
    # List expert documents
    documents = service.list_expert_knowledge_documents(base_dir="data_test/knowledge_base/local")
    
    print(f"\nFound {len(documents)} expert documents:")
    for doc in documents:
        print(f"  ID: {doc['id']}")
        print(f"  Title: {doc['title']}")
        print(f"  Type: {doc['elementType']}")
        summary = doc['contentSummary'] or ""
        print(f"  Summary: {summary[:100]}..." if len(summary) > 100 else f"  Summary: {summary}")
        print()
    
    # Verify we found some documents
    assert len(documents) > 0, "Should find at least one expert document in test data"
    
    # Verify each document has required fields
    for doc in documents:
        assert 'id' in doc and doc['id'], "Document should have an id"
        assert 'title' in doc, "Document should have a title field"
        assert 'contentSummary' in doc, "Document should have a contentSummary field"
        assert 'elementType' in doc and doc['elementType'], "Document should have an elementType"
    
    print("✓ Expert documents listing test passed")


def test_list_documents_empty_directory():
    """Test listing documents from a non-existent directory."""
    service = KnowledgeBaseService(
        legal_knowledge_document_loader=ESELKnowledgeDocumentLoader(
            sparql_endpoint="https://opendata.eselpoint.cz/sparql"
        ),
        expert_knowledge_document_loader=LocalKnowledgeDocumentLoader(),
        document_summarizer=SimpleOpenAIKnowledgeDocumentSummarizer()
    )
    
    # Try to list documents from non-existent directory
    documents = service.list_legal_knowledge_documents(base_dir="data_test/knowledge_base/nonexistent")
    
    # Should return empty list, not raise an error
    assert documents == [], "Should return empty list for non-existent directory"
    
    print("✓ Empty directory test passed")


if __name__ == "__main__":
    print("Running knowledge base document listing tests...\n")
    
    test_list_legal_documents()
    test_list_expert_documents()
    test_list_documents_empty_directory()
    
    print("\n✓ All tests passed!")
