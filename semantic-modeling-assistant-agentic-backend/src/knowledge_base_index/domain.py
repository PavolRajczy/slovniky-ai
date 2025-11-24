from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional
import numpy as np

@dataclass
class IndexDocument:
    """
    A searchable document representing an indexed knowledge document element.
    The content comprises the parent of the knowledge document element and the content of the knowledge document element.
    """
    id: str                             # A globally unique identifier of the index document.
    element_id: str                     # The identifier of the knowledge document element.
    content: Optional[str]              # Textual content combining parent and element content.
    element_type: str                   # The type of the document element (e.g., Chapter, Section, Paragraph, etc).

@dataclass
class TextChunk:
    """
    A chunk of text from an index document representing an indexed knowledge document element.
    """
    chunk_id: str                       # A unique identifier for the text chunk.
    document_id: str                    # The identifier of the index document from which this chunk is derived.
    text: str                           # The textual content of the chunk.
    start_offset: int                   # The starting character offset of the chunk in the original document.
    end_offset: int                     # The ending character offset of the chunk in the original document.
    fragment_id: Optional[str] = None   # The identifier of the XML fragment this chunk belongs to (for hierarchical content).
    embedding: Optional[np.ndarray] = None  # The embedding vector for this text chunk.

@dataclass
class SearchQuery:
    """
    A search query for retrieving indexed knowledge document elements.
    """
    query_text: str                     # The text of the search query.
    max_results: int = 10               # Maximum number of results to return.
    offset: int = 0                     # Number of top results to skip (0 means no skipping).

@dataclass
class ChunkMatch:
    """
    Represents a matching text chunk within a search result.
    """
    chunk_id: str                       # The unique identifier of the chunk
    text: str                           # The text content of the chunk
    relevance_score: float              # The relevance score for this specific chunk
    fragment_id: Optional[str] = None   # The fragment ID (for hierarchical content)
    start_offset: int = 0               # Start position in the original document
    end_offset: int = 0                 # End position in the original document

@dataclass
class SearchResult:
    """
    A search result representing a retrieved knowledge document element.
    Each element appears only once, with all matching chunks listed.
    """
    element_id: str                     # The identifier of the knowledge document element.
    overall_relevance_score: float      # Maximum relevance score from all matching chunks.
    matching_chunks: List[ChunkMatch]   # All chunks from this element that matched the query.