from typing import List, Optional, Dict
from knowledge_base.domain import KnowledgeDocument, KnowledgeDocumentElement
from .domain import SearchQuery, SearchResult
from .indexer import KnowledgeDocumentIndexer
from .indexers.faiss_fulltext_openai_indexer import FAISSFullTextOpenAIKnowledgeDocumentIndexer


class KnowledgeBaseIndexService:
    """
    Service providing a simple interface for building and searching knowledge document indexes.
    
    This service acts as a facade over the KnowledgeDocumentIndexer interface,
    providing a simplified API for index operations on a collection of knowledge documents.
    Each document has its own indexer instance to maintain separation.
    """
    
    def __init__(self, indexer_factory: Optional[callable] = None, indexer: Optional[KnowledgeDocumentIndexer] = None):
        """
        Initialize the knowledge base index service.
        
        Args:
            indexer_factory: A factory function that creates new indexer instances. 
                If None, defaults to creating FAISSFullTextOpenAIKnowledgeDocumentIndexer instances.
            indexer: DEPRECATED - For backward compatibility only. A single indexer instance.
                If provided, the service will wrap it in a factory function.
        """
        if indexer is not None:
            # Backward compatibility: wrap single indexer in a factory
            self._indexer_factory = lambda: indexer
        else:
            self._indexer_factory = indexer_factory if indexer_factory is not None else lambda: FAISSFullTextOpenAIKnowledgeDocumentIndexer()
        self._document_indexers: Dict[str, KnowledgeDocumentIndexer] = {}
        self._documents: Dict[str, KnowledgeDocument] = {}
    
    
    def add_document(self, knowledge_document: KnowledgeDocument) -> None:
        """
        Add a knowledge document to the collection and build or load its index.
        
        If an index already exists for the document, it will be loaded.
        Otherwise, a new index will be built and stored.
        
        Args:
            knowledge_document: The knowledge document to add and index.
            
        Raises:
            Exception: If the indexing or loading process fails.
        """
        try:
            # Create a new indexer for this document
            indexer = self._indexer_factory()
            
            # Try to load existing index first
            if not indexer.load_index(knowledge_document):
                # No existing index found, build a new one
                indexer.build_index(knowledge_document)
                # Store the newly built index
                indexer.store_index(knowledge_document)
            
            # Store the indexer and document for this document
            self._document_indexers[knowledge_document.id] = indexer
            self._documents[knowledge_document.id] = knowledge_document
            
        except Exception as e:
            raise Exception(f"Failed to add document '{knowledge_document.id}': {str(e)}") from e

    def _find_element_by_id(self, element_id: str, document_id: str) -> Optional[KnowledgeDocumentElement]:
        """
        Find a knowledge document element by its ID within a specific document.
        
        Args:
            element_id: The ID of the element to find.
            document_id: The ID of the document to search in.
            
        Returns:
            The knowledge document element if found, None otherwise.
        """
        if document_id not in self._documents:
            return None
            
        document = self._documents[document_id]
        
        def search_element(element: KnowledgeDocumentElement) -> Optional[KnowledgeDocumentElement]:
            if element.id == element_id:
                return element
            for child in element.childElements:
                result = search_element(child)
                if result:
                    return result
            return None
        
        return search_element(document)


    def search_relative(self, query_text: str, relative_difference: float = 0) -> List[KnowledgeDocumentElement]:
        """
        Search for knowledge document elements that match the query text within a certain relative difference.

        This method searches each document separately.
        For each document, it retrieves the top result that matches the query and other results with their relevance scores not lower than
        (1 - relative_difference) * top_relevance_score.
        Finally, it combines and sorts all results from all documents by relevance.

        Args:
            query_text: The text to search for.
            relative_difference: The maximum allowed relative difference from the top relevance score (the default 0 means only the top result).
        """
        if not query_text or not query_text.strip():
            return []
            
        if not self._document_indexers:
            return []
            
        if relative_difference < 0:
            relative_difference = 0
        elif relative_difference > 1:
            relative_difference = 1
            
        try:
            # Use a large max_results to get all possible matches for filtering
            query = SearchQuery(
                query_text=query_text.strip(),
                max_results=30,  # Large number to get all results for filtering
                offset=0
            )
            
            all_filtered_results = []
            
            # Search each document separately
            for document_id, indexer in self._document_indexers.items():
                try:
                    search_results = indexer.search(query)
                    
                    if not search_results:
                        continue
                    
                    # Sort results by relevance score (descending) for this document
                    search_results.sort(key=lambda x: x.overall_relevance_score, reverse=True)
                    
                    # Get the top result's relevance score
                    top_score = search_results[0].overall_relevance_score
                    
                    # Calculate the threshold score
                    threshold_score = (1 - relative_difference) * top_score
                    
                    # Filter results that meet the threshold
                    filtered_results = [
                        result for result in search_results 
                        if result.overall_relevance_score >= threshold_score
                    ]
                    
                    # Add to combined results with document ID
                    for search_result in filtered_results:
                        all_filtered_results.append((search_result, document_id))
                        
                except Exception as e:
                    # Log the error but continue with other documents
                    print(f"Warning: Failed to search in document '{document_id}': {str(e)}")
            
            # Sort all filtered results by relevance score (descending)
            all_filtered_results.sort(key=lambda x: x[0].overall_relevance_score, reverse=True)
            
            # Convert SearchResults to KnowledgeDocumentElements
            knowledge_elements = []
            for search_result, document_id in all_filtered_results:
                element = self._find_element_by_id(search_result.element_id, document_id)
                if element:
                    knowledge_elements.append(element)
            
            return knowledge_elements
            
        except Exception as e:
            raise Exception(f"Failed to search collection with query '{query_text}' and relative_difference {relative_difference}: {str(e)}") from e

    def search(self, query_text: str, max_results: int = 10, offset: int = 0) -> List[KnowledgeDocumentElement]:
        """
        Search across all knowledge documents in the collection with pagination support.
        
        This method searches each document separately and returns up to max_results 
        knowledge document elements from each document, then combines and sorts all results by relevance.
        The offset parameter allows skipping the first K top results.
        
        Args:
            query_text: The text to search for.
            max_results: Maximum number of results to return. Defaults to 10.
            offset: Number of top results to skip (0 means no skipping). Defaults to 0.
            
        Returns:
            A list of knowledge document elements matching the query from all documents, sorted by relevance.
            Results from position offset+1 to offset+max_results are returned.
            
        Raises:
            Exception: If the search operation fails.
        """
        if not query_text or not query_text.strip():
            return []
            
        if not self._document_indexers:
            return []
            
        if offset < 0:
            offset = 0
            
        try:
            query = SearchQuery(
                query_text=query_text.strip(),
                max_results=max_results + offset,  # Request more results to account for offset
                offset=0  # Let individual indexers return all their results, we'll handle offset here
            )
            
            all_results = []
            for document_id, indexer in self._document_indexers.items():
                try:
                    search_results = indexer.search(query)
                    # Create tuples to track which document each result came from
                    for search_result in search_results:
                        all_results.append((search_result, document_id))
                except Exception as e:
                    # Log the error but continue with other documents
                    print(f"Warning: Failed to search in document '{document_id}': {str(e)}")
            
            # Sort all results by relevance score (descending)
            all_results.sort(key=lambda x: x[0].overall_relevance_score, reverse=True)
            
            # Apply offset and max_results limit
            start_index = offset
            end_index = offset + max_results
            limited_results = all_results[start_index:end_index]
            
            # Convert SearchResults to KnowledgeDocumentElements
            knowledge_elements = []
            for search_result, document_id in limited_results:
                element = self._find_element_by_id(search_result.element_id, document_id)
                if element:
                    knowledge_elements.append(element)
            
            return knowledge_elements
        except Exception as e:
            raise Exception(f"Failed to search collection with query '{query_text}': {str(e)}") from e

    def search_in_document(self, document_id: str, query_text: str, max_results: int = 10, offset: int = 0) -> List[KnowledgeDocumentElement]:
        """
        Search within a specific knowledge document.
        
        Args:
            document_id: The ID of the document to search in.
            query_text: The text to search for.
            max_results: Maximum number of results to return. Defaults to 10.
            offset: Number of top results to skip (0 means no skipping). Defaults to 0.
            
        Returns:
            A list of knowledge document elements matching the query from the specified document.
            
        Raises:
            Exception: If the document is not found or search operation fails.
        """
        if document_id not in self._document_indexers:
            raise Exception(f"Document '{document_id}' not found in collection")
            
        if not query_text or not query_text.strip():
            return []
            
        if offset < 0:
            offset = 0
            
        try:
            query = SearchQuery(
                query_text=query_text.strip(),
                max_results=max_results + offset,
                offset=0
            )
            
            indexer = self._document_indexers[document_id]
            search_results = indexer.search(query)
            
            # Sort results by relevance score (descending)
            search_results.sort(key=lambda x: x.overall_relevance_score, reverse=True)
            
            # Apply offset and max_results limit
            start_index = offset
            end_index = offset + max_results
            limited_results = search_results[start_index:end_index]
            
            # Convert SearchResults to KnowledgeDocumentElements
            knowledge_elements = []
            for search_result in limited_results:
                element = self._find_element_by_id(search_result.element_id, document_id)
                if element:
                    knowledge_elements.append(element)
            
            return knowledge_elements
        except Exception as e:
            raise Exception(f"Failed to search in document '{document_id}' with query '{query_text}': {str(e)}") from e

    def search_in_collection(self, query_text: str, max_results: int = 10, offset: int = 0) -> List[KnowledgeDocumentElement]:
        """
        Search across all knowledge documents in the collection.
        
        This is an alias for the search_with_pagination method to maintain backward compatibility.
        
        Args:
            query_text: The text to search for.
            max_results: Maximum number of results to return. Defaults to 10.
            offset: Number of top results to skip (0 means no skipping). Defaults to 0.
            
        Returns:
            A list of knowledge document elements matching the query from all documents, sorted by relevance.
            
        Raises:
            Exception: If the search operation fails.
        """
        return self.search_with_pagination(query_text, max_results, offset)

    def has_document(self, document_id: str) -> bool:
        """
        Check if a document is indexed in the collection.
        
        Args:
            document_id: The ID of the document to check.
            
        Returns:
            True if the document is indexed, False otherwise.
        """
        return document_id in self._document_indexers

    def remove_document(self, document_id: str) -> bool:
        """
        Remove a document from the collection.
        
        Args:
            document_id: The ID of the document to remove.
            
        Returns:
            True if the document was removed, False if it was not found.
        """
        if document_id not in self._document_indexers:
            return False
        
        del self._document_indexers[document_id]
        if document_id in self._documents:
            del self._documents[document_id]
        
        return True

    def get_document_ids(self) -> List[str]:
        """
        Get the list of all document IDs in the collection.
        
        Returns:
            A list of document IDs currently indexed in the collection.
        """
        return list(self._document_indexers.keys())