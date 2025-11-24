#!/usr/bin/env python3
"""
Unit tests for SemchunkIndexDocumentChunker with hierarchical chunking support.

Tests both plain text chunking and hierarchical XML chunking functionality.
Verifies that:
- Plain text content is chunked correctly without fragment IDs
- Hierarchical XML content is parsed and chunked with proper fragment IDs
- Contextual text is built correctly from fragment hierarchy
- Edge cases are handled appropriately
"""

import os
import sys
import uuid
from typing import List

# Ensure src/ is importable when running as a script
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from knowledge_base_index.domain import IndexDocument, TextChunk
from knowledge_base_index.chunkers.semchunk_chunker import SemchunkIndexDocumentChunker


def test_plain_text_chunking():
    """Test chunking of plain text content."""
    print("Testing plain text chunking...")
    
    chunker = SemchunkIndexDocumentChunker(chunk_size=100)
    
    # Create test document with plain text
    plain_text = """
    This is a simple document with plain text content. It contains multiple sentences and paragraphs
    that should be chunked appropriately by the semantic chunker. The chunker should preserve
    semantic boundaries while keeping chunks within the specified size limits.
    
    This is another paragraph that extends the content further to ensure we get multiple chunks
    from this document. The text is long enough to require splitting into several smaller pieces.
    """
    
    index_doc = IndexDocument(
        id="test_doc_plain",
        element_id="elem_001",
        content=plain_text.strip(),
        element_type="Document"
    )
    
    # Get chunks
    chunks = chunker.get_text_chunks(index_doc)
    
    # Validate results
    assert len(chunks) > 0, "Should generate at least one chunk"
    print(f"Generated {len(chunks)} chunks for plain text")
    
    for i, chunk in enumerate(chunks):
        # Validate chunk structure
        assert chunk.chunk_id is not None, f"Chunk {i} should have a chunk_id"
        assert chunk.document_id == "test_doc_plain", f"Chunk {i} should have correct document_id"
        assert chunk.text is not None, f"Chunk {i} should have text content"
        assert chunk.start_offset >= 0, f"Chunk {i} should have valid start_offset"
        assert chunk.end_offset > chunk.start_offset, f"Chunk {i} should have valid end_offset"
        assert chunk.fragment_id is None, f"Chunk {i} should have no fragment_id for plain text"
        
        print(f"Chunk {i}: text_length={len(chunk.text)}, fragment_id={chunk.fragment_id}")
    
    print("Plain text chunking test passed!\n")


def test_hierarchical_xml_chunking():
    """Test chunking of hierarchical XML content."""
    print("Testing hierarchical XML chunking...")
    
    chunker = SemchunkIndexDocumentChunker(chunk_size=150)
    
    # Create test document with hierarchical XML content
    xml_content = """
    <f id="root">
        This is the root fragment opening text that provides context for the entire document.
        <f id="section1">
            This is section 1 opening text describing the first major section.
            <f id="subsection1.1">
                This is subsection 1.1 with detailed content about specific topic A. 
                It contains important information that should be chunked with full context.
            </f>
            <f id="subsection1.2">
                This is subsection 1.2 with detailed content about specific topic B.
                It also contains valuable information that needs proper contextualization.
            </f>
        </f>
        <f id="section2">
            This is section 2 opening text describing the second major section.
            <f id="subsection2.1">
                This is subsection 2.1 with content about topic C. The content here
                should be chunked with the full hierarchical context from root and section 2.
            </f>
        </f>
    </f>
    """
    
    index_doc = IndexDocument(
        id="test_doc_xml",
        element_id="elem_002",
        content=xml_content.strip(),
        element_type="Document"
    )
    
    # Get chunks
    chunks = chunker.get_text_chunks(index_doc)
    
    # Validate results
    assert len(chunks) > 0, "Should generate at least one chunk"
    print(f"Generated {len(chunks)} chunks for hierarchical XML")
    
    # Expected leaf fragment IDs
    expected_fragment_ids = {"subsection1.1", "subsection1.2", "subsection2.1"}
    found_fragment_ids = set()
    
    for i, chunk in enumerate(chunks):
        # Validate chunk structure
        assert chunk.chunk_id is not None, f"Chunk {i} should have a chunk_id"
        assert chunk.document_id == "test_doc_xml", f"Chunk {i} should have correct document_id"
        assert chunk.text is not None, f"Chunk {i} should have text content"
        assert chunk.start_offset >= 0, f"Chunk {i} should have valid start_offset"
        assert chunk.end_offset >= chunk.start_offset, f"Chunk {i} should have valid end_offset"
        assert chunk.fragment_id is not None, f"Chunk {i} should have fragment_id for XML content"
        
        found_fragment_ids.add(chunk.fragment_id)
        
        # Validate that contextual text includes hierarchical context
        if chunk.fragment_id == "subsection1.1":
            # Should contain root + section1 + subsection1.1 opening texts
            assert "root fragment opening text" in chunk.text, "Should include root context"
            assert "section 1 opening text" in chunk.text, "Should include section 1 context"
            assert "subsection 1.1" in chunk.text, "Should include subsection 1.1 content"
        elif chunk.fragment_id == "subsection2.1":
            # Should contain root + section2 + subsection2.1 opening texts
            assert "root fragment opening text" in chunk.text, "Should include root context"
            assert "section 2 opening text" in chunk.text, "Should include section 2 context"
            assert "subsection 2.1" in chunk.text, "Should include subsection 2.1 content"
        
        print(f"Chunk {i}: fragment_id={chunk.fragment_id}, text_length={len(chunk.text)}")
    
    # Validate that all expected fragment IDs were found
    assert found_fragment_ids == expected_fragment_ids, f"Expected fragment IDs {expected_fragment_ids}, found {found_fragment_ids}"
    
    print("Hierarchical XML chunking test passed!\n")


def test_malformed_xml_fallback():
    """Test that malformed XML falls back to plain text chunking."""
    print("Testing malformed XML fallback...")
    
    chunker = SemchunkIndexDocumentChunker(chunk_size=100)
    
    # Create test document with malformed XML content
    malformed_xml = """
    <f id="root">
        This is some content with malformed XML.
        <f id="section1">
            Missing closing tag for this section
        <f id="section2">
            This section is also malformed
        </f>
    """
    
    index_doc = IndexDocument(
        id="test_doc_malformed",
        element_id="elem_003",
        content=malformed_xml.strip(),
        element_type="Document"
    )
    
    # Get chunks - should fall back to plain text chunking
    chunks = chunker.get_text_chunks(index_doc)
    
    # Validate results
    assert len(chunks) > 0, "Should generate at least one chunk even for malformed XML"
    print(f"Generated {len(chunks)} chunks for malformed XML (fallback to plain text)")
    
    for i, chunk in enumerate(chunks):
        # Should have no fragment_id (plain text fallback)
        assert chunk.fragment_id is None, f"Chunk {i} should have no fragment_id for malformed XML"
        print(f"Chunk {i}: text_length={len(chunk.text)}, fragment_id={chunk.fragment_id}")
    
    print("Malformed XML fallback test passed!\n")


def test_empty_content():
    """Test handling of empty content."""
    print("Testing empty content handling...")
    
    chunker = SemchunkIndexDocumentChunker(chunk_size=100)
    
    # Create test document with empty content
    index_doc = IndexDocument(
        id="test_doc_empty",
        element_id="elem_004",
        content="",
        element_type="Document"
    )
    
    # Get chunks
    chunks = chunker.get_text_chunks(index_doc)
    
    # Should return empty list
    assert len(chunks) == 0, "Empty content should return no chunks"
    print("Empty content handling test passed!\n")


def test_xml_without_f_elements():
    """Test XML content without <f> elements falls back to plain text."""
    print("Testing XML without <f> elements...")
    
    chunker = SemchunkIndexDocumentChunker(chunk_size=100)
    
    # Create test document with XML but no <f> elements
    xml_without_f = """
    <document>
        <title>Some Document</title>
        <content>
            This is valid XML but it doesn't contain any <f> elements for hierarchical chunking.
            Therefore it should be treated as plain text content and chunked accordingly.
        </content>
    </document>
    """
    
    index_doc = IndexDocument(
        id="test_doc_xml_no_f",
        element_id="elem_005",
        content=xml_without_f.strip(),
        element_type="Document"
    )
    
    # Get chunks - should fall back to plain text chunking
    chunks = chunker.get_text_chunks(index_doc)
    
    # Validate results
    assert len(chunks) > 0, "Should generate at least one chunk"
    print(f"Generated {len(chunks)} chunks for XML without <f> elements (fallback to plain text)")
    
    for i, chunk in enumerate(chunks):
        # Should have no fragment_id (plain text fallback)
        assert chunk.fragment_id is None, f"Chunk {i} should have no fragment_id for XML without <f> elements"
        print(f"Chunk {i}: text_length={len(chunk.text)}, fragment_id={chunk.fragment_id}")
    
    print("XML without <f> elements test passed!\n")


def main():
    """Run all tests."""
    print("Starting SemchunkIndexDocumentChunker tests...\n")
    
    try:
        test_plain_text_chunking()
        test_hierarchical_xml_chunking()
        test_malformed_xml_fallback()
        test_empty_content()
        test_xml_without_f_elements()
        
        print("=" * 50)
        print("All SemchunkIndexDocumentChunker tests passed!")
        print("=" * 50)
        
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
