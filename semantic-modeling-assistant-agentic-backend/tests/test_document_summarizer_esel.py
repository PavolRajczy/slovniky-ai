#!/usr/bin/env python3
"""
Test script to verify the document summarizer using ESELKnowledgeDocumentLoader and a cached document.
"""

import sys
import os
from pathlib import Path

# Add the src directory to the path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from knowledge_base.document_loaders.document_loader_esel import ESELKnowledgeDocumentLoader
from knowledge_base.document_summarizers.document_summarizer_simple_openai import SimpleOpenAIKnowledgeDocumentSummarizer
from knowledge_base.domain import KnowledgeDocument


def test_summarizer_on_cached_document():
    """Test summarizer using a cached document loaded by ESELKnowledgeDocumentLoader."""
    print("Testing summarizer on cached document...")

    sparql_endpoint = "https://opendata.eselpoint.cz/sparql"
    loader = ESELKnowledgeDocumentLoader(sparql_endpoint)
    document_id = "https://opendata.eselpoint.cz/esel-esb/eli/cz/sb/1000/01/1000-01-01"

    # Load document from cache (assume cache exists)
    document = loader.load_document(document_id)
    assert document is not None, "Document should not be None"
    assert isinstance(document, KnowledgeDocument), "Document should be a KnowledgeDocument instance"
    print(f"  - Loaded document: {document.id} ({document.title})")

    # Summarize document content
    summarizer = SimpleOpenAIKnowledgeDocumentSummarizer()
    summarizer.summarize_document(document)
    assert document.contentSummary is not None, "Summary should not be None"
    assert isinstance(document.contentSummary, str), "Summary should be a string"
    print(f"  - Summary: {document.contentSummary[:200]}{'...' if len(document.contentSummary) > 200 else ''}")
    print("✓ Document summarization successful")


def run_tests():
    """Run all tests."""
    print("Running document summarizer tests...")
    print("=" * 50)
    try:
        test_summarizer_on_cached_document()
        print("=" * 50)
        print("🎉 All tests passed!")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
