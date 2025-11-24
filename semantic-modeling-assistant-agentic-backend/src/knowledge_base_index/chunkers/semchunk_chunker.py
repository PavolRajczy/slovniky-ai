from typing import List, Dict, Optional, Tuple
import uuid
from dataclasses import dataclass
from semchunk import chunkerify
import tiktoken
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import ParseError

from knowledge_base_index.indexer import IndexDocumentChunker

from ..domain import TextChunk, IndexDocument


@dataclass
class ContentFragment:
    """
    Represents a content fragment in hierarchical XML content.
    """
    fragment_id: str
    opening_text: str
    children: List['ContentFragment']
    parent: Optional['ContentFragment'] = None


class SemchunkIndexDocumentChunker(IndexDocumentChunker):
    """
    Implementation of IndexDocumentChunker using the semchunk library.
    
    This chunker uses semantic chunking to split index documents into 
    meaningful text chunks while preserving semantic boundaries.
    Supports both plain text and hierarchical XML content.
    """
    
    def __init__(self, chunk_size: int = 250, chunk_overlap: float = 0, target_model: str = "gpt-4.1"):
        """
        Initialize the semchunk-based chunker.
        
        Args:
            chunk_size: Maximum number of tokens per chunk
            chunk_overlap: Number of tokens to overlap between chunks
            target_model: Target LLM model the chunks are optimized for.
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.target_model = target_model
        self.chunker = chunkerify(tiktoken.encoding_for_model(target_model), chunk_size=chunk_size)

    def get_text_chunks(self, index_document: IndexDocument) -> List[TextChunk]:
        """
        Chunk the given index document into smaller semantic pieces using semchunk.
        
        Args:
            index_document: The index document to chunk
            
        Returns:
            A list of TextChunk objects representing the chunked document
        """
        if not index_document.content:
            return []
        
        # Check if content is XML with hierarchical structure
        if self._is_hierarchical_xml_content(index_document.content):
            return self._chunk_hierarchical_content(index_document)
        else:
            return self._chunk_plain_text_content(index_document)

    def _is_hierarchical_xml_content(self, content: str) -> bool:
        """
        Check if the content is hierarchical XML with <f> fragments.
        
        Args:
            content: The content to check
            
        Returns:
            True if content is hierarchical XML, False otherwise
        """
        try:
            # Try to parse as XML and check for <f> elements
            root = ET.fromstring(f"<root>{content}</root>")
            return len(root.findall('.//f')) > 0
        except ParseError:
            return False

    def _chunk_plain_text_content(self, index_document: IndexDocument) -> List[TextChunk]:
        """
        Chunk plain text content using semchunk.
        
        Args:
            index_document: The index document with plain text content
            
        Returns:
            A list of TextChunk objects
        """
        # Use semchunk to create semantic chunks
        chunk_texts = self.chunker(index_document.content)
        
        chunks = []
        current_offset = 0
        
        for chunk_text in chunk_texts:
            # Find the start position of this chunk in the original text
            start_offset = index_document.content.find(chunk_text, current_offset)
            if start_offset == -1:
                # If exact match not found, use approximate position
                start_offset = current_offset
            
            end_offset = start_offset + len(chunk_text)
            
            chunk = TextChunk(
                chunk_id=str(uuid.uuid4()),
                document_id=index_document.id,
                text=chunk_text.strip(),
                start_offset=start_offset,
                end_offset=end_offset,
                fragment_id=None  # No fragment ID for plain text
            )
            
            chunks.append(chunk)
            current_offset = end_offset
        
        return chunks

    def _chunk_hierarchical_content(self, index_document: IndexDocument) -> List[TextChunk]:
        """
        Chunk hierarchical XML content using fragment-based chunking.
        
        Args:
            index_document: The index document with hierarchical XML content
            
        Returns:
            A list of TextChunk objects
        """
        try:
            # Parse XML content
            root = ET.fromstring(f"<root>{index_document.content}</root>")
            
            # Build fragment hierarchy
            root_fragment = self._build_fragment_hierarchy(root)
            
            # Get all leaf fragments
            leaf_fragments = self._get_leaf_fragments(root_fragment)
            
            # Generate chunks for each leaf fragment
            chunks = []
            for leaf_fragment in leaf_fragments:
                contextual_text = self._build_contextual_text(leaf_fragment)
                fragment_chunks = self._chunk_contextual_text(
                    contextual_text, 
                    index_document.id, 
                    leaf_fragment.fragment_id
                )
                chunks.extend(fragment_chunks)
            
            return chunks
            
        except ParseError as e:
            # If XML parsing fails, fall back to plain text chunking
            return self._chunk_plain_text_content(index_document)

    def _build_fragment_hierarchy(self, xml_element: ET.Element, parent: Optional[ContentFragment] = None) -> ContentFragment:
        """
        Build a hierarchy of content fragments from XML elements.
        
        Args:
            xml_element: The XML element to process
            parent: The parent fragment
            
        Returns:
            ContentFragment representing the hierarchy
        """
        fragment_id = xml_element.get('id', f"fragment_{uuid.uuid4().hex[:8]}")
        
        # Extract opening text (text before first child fragment)
        opening_text = xml_element.text or ""
        
        # Create fragment
        fragment = ContentFragment(
            fragment_id=fragment_id,
            opening_text=opening_text.strip(),
            children=[],
            parent=parent
        )
        
        # Process child <f> elements
        for child_element in xml_element.findall('./f'):
            child_fragment = self._build_fragment_hierarchy(child_element, fragment)
            fragment.children.append(child_fragment)
        
        return fragment

    def _get_leaf_fragments(self, fragment: ContentFragment) -> List[ContentFragment]:
        """
        Get all leaf fragments from the hierarchy.
        
        Args:
            fragment: The root fragment
            
        Returns:
            List of leaf fragments
        """
        if not fragment.children:
            return [fragment]
        
        leaf_fragments = []
        for child in fragment.children:
            leaf_fragments.extend(self._get_leaf_fragments(child))
        
        return leaf_fragments

    def _build_contextual_text(self, leaf_fragment: ContentFragment) -> str:
        """
        Build contextual text for a leaf fragment by combining ancestor opening texts.
        
        Args:
            leaf_fragment: The leaf fragment
            
        Returns:
            Contextual text combining all ancestor opening texts
        """
        # Collect opening texts from root to leaf
        opening_texts = []
        
        current = leaf_fragment
        while current is not None:
            if current.opening_text:
                opening_texts.insert(0, current.opening_text)
            current = current.parent
        
        # Join with spaces
        return " ".join(opening_texts).strip()

    def _chunk_contextual_text(self, contextual_text: str, document_id: str, fragment_id: str) -> List[TextChunk]:
        """
        Chunk the contextual text for a fragment.
        
        Args:
            contextual_text: The contextual text to chunk
            document_id: The document ID
            fragment_id: The fragment ID
            
        Returns:
            List of TextChunk objects
        """
        if not contextual_text:
            return []
        
        # Use semchunk to create semantic chunks
        chunk_texts = self.chunker(contextual_text)
        
        chunks = []
        current_offset = 0
        
        for chunk_text in chunk_texts:
            # Find the start position of this chunk in the contextual text
            start_offset = contextual_text.find(chunk_text, current_offset)
            if start_offset == -1:
                # If exact match not found, use approximate position
                start_offset = current_offset
            
            end_offset = start_offset + len(chunk_text)
            
            chunk = TextChunk(
                chunk_id=str(uuid.uuid4()),
                document_id=document_id,
                text=chunk_text.strip(),
                start_offset=start_offset,
                end_offset=end_offset,
                fragment_id=fragment_id
            )
            
            chunks.append(chunk)
            current_offset = end_offset
        
        return chunks
