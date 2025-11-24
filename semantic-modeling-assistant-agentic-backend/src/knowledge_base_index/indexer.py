from abc import ABC, abstractmethod
from typing import List
from knowledge_base.domain import KnowledgeDocument

from .domain import IndexDocument, TextChunk, SearchQuery, SearchResult


class IndexDocumentChunker(ABC):
    """
    An abstract interface for chunking index documents into smaller, manageable pieces.
    """
    
    @abstractmethod
    def get_text_chunks(self, index_document: IndexDocument) -> List[TextChunk]:
        """
        Chunk the given index document into smaller pieces.

        Args:
            index_document: The index document to chunk.

        Returns:
            A list of TextChunk objects representing the chunked document.
        """
        pass


class KnowledgeDocumentIndexer(ABC):
    """
    An abstract interface for indexing and retrieving knowledge documents.
    
    The indexer should:
    1. Build index documents from knowledge document elements
    2. Use a chunker to split index documents into text chunks
    3. Generate embeddings for text chunks
    4. Store embeddings in a vector store for fast similarity search
    5. Store and load indexes for persistence
    """

    @abstractmethod
    def build_index(self, knowledge_document: KnowledgeDocument) -> None:
        """
        Build an index for the given knowledge document.
        
        This method should create IndexDocument objects, chunk them using
        the configured chunker, generate embeddings, and store them in
        a vector store.
        
        Args:
            knowledge_document: The knowledge document to index.
        """
        pass

    @abstractmethod
    def search(self, query: SearchQuery) -> List[SearchResult]:
        """
        Search the index for the given query.

        Args:
            query: The search query to execute.

        Returns:
            A list of search results matching the query, sorted by relevance.
        """
        pass

    @abstractmethod
    def store_index(self, knowledge_document: KnowledgeDocument) -> None:
        """
        Store the index for the given knowledge document to persistent storage.
        
        This method should save the current state of the index (embeddings,
        metadata, etc.) to storage for later retrieval.
        
        Args:
            knowledge_document: The knowledge document whose index should be stored.
        """
        pass

    @abstractmethod
    def load_index(self, knowledge_document: KnowledgeDocument) -> bool:
        """
        Load a previously stored index for the given knowledge document.
        
        This method should restore the index state from persistent storage,
        allowing the indexer to perform searches without rebuilding the index.
        
        Args:
            knowledge_document: The knowledge document whose index should be loaded.
            
        Returns:
            True if the index was successfully loaded, False if no stored index exists
            or loading failed.
        """
        pass