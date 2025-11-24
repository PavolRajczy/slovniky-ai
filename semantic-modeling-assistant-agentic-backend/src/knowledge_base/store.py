from typing import List, Dict

from knowledge_base.domain import KnowledgeDocument, KnowledgeDocumentElement

class KnowledgeDocumentLoader:
    """
    An interface for loading knowledge documents.

    Each implementation of this interface should provide the logic to load a knowledge document from a specific source.
    """

    def load_document(self, document_id: str) -> KnowledgeDocument | None:
        # Implementation to load a document by its ID
        """
        Load a knowledge document by its ID.

        Args:
            document_id: The ID of the knowledge document to load.

        Returns:
            The loaded knowledge document, or None if not found.
        """
        pass

class KnowledgeDocumentSummarizer:
    """
    An interface for summarizing knowledge documents.

    Each implementation of this interface should provide the logic to summarize a knowledge document and its elements.
    """
    def summarize_document(self, document: KnowledgeDocument) -> None:
        # Implementation to summarize the document
        pass

class KnowledgeStore:
    def __init__(self):
        self.documents: Dict[str, KnowledgeDocument] = {}

    def load_documents(self, document_ids: List[str], document_loader: KnowledgeDocumentLoader, document_summarizer: KnowledgeDocumentSummarizer) -> List[KnowledgeDocument]:
        """
        Load multiple knowledge documents by their IDs and summarizes them.
        
        Args:
            document_ids: A list of knowledge document IDs to load.
            document_loader: The knowledge document loader to use for loading knowledge documents.
            document_summarizer: The knowledge document summarizer to use for summarizing loaded documents.

        Returns:
            A list of loaded knowledge documents.
        """
        loaded_docs = []
        for doc_id in document_ids:
            doc = document_loader.load_document(doc_id)
            if doc:
                document_summarizer.summarize_document(doc)
                loaded_docs.append(doc)
                self.documents[doc.id] = doc
        return loaded_docs

    def get_knowledge_document(self, document_id: str) -> KnowledgeDocument | None:
        """
        Get a knowledge document by its ID.
        
        Args:
            document_id: The ID of the knowledge document to retrieve.

        Returns:
            The knowledge document with the specified ID, or None if not found.
        """
        return self.documents.get(document_id)
    
    def get_knowledge_document_element(self, document_id: str, element_id: str) -> KnowledgeDocumentElement | None:
        """
        Get a knowledge document element by its ID within a specific knowledge document.

        Args:
            document_id: The ID of the knowledge document containing the element.
            element_id: The ID of the knowledge document element to retrieve.

        Returns:
            The knowledge document element with the specified ID, or None if not found.
        """
        doc = self.get_knowledge_document(document_id)
        if not doc:
            return None
        
        def _find_element(element: KnowledgeDocumentElement) -> KnowledgeDocumentElement | None:
            if element.id == element_id:
                return element
            for child in element.childElements:
                found = _find_element(child)
                if found:
                    return found
            return None
        
        return _find_element(doc)
