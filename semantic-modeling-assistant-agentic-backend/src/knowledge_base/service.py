from typing import List, Dict
import json
from pathlib import Path
from knowledge_base.domain import KnowledgeDocument, KnowledgeDocumentElement
from knowledge_base.store import KnowledgeDocumentLoader, KnowledgeDocumentSummarizer, KnowledgeStore


class KnowledgeBaseService:
    """
    A service for managing knowledge bases comprising knowledge documents.
    """
    def __init__(self, legal_knowledge_document_loader: KnowledgeDocumentLoader, expert_knowledge_document_loader: KnowledgeDocumentLoader, document_summarizer: KnowledgeDocumentSummarizer):
        """
        Initializes a service for managing a knowledge base.

        Args:
            legal_document_loader: The knowledge document loader to use for loading legal knowledge documents into the knowledge base.
            expert_document_loader: The knowledge document loader to use for loading expert knowledge documents into the knowledge base.
            document_summarizer: The knowledge document summarizer to use for summarizing loaded documents if necessary.
        """
        self.legal_knowledge_document_loader = legal_knowledge_document_loader
        self.expert_knowledge_document_loader = expert_knowledge_document_loader
        self.document_summarizer = document_summarizer

        self.knowledge_store = KnowledgeStore()

    def load_knowledge_documents(self, legal_knowledge_document_ids: List[str], expert_knowledge_document_ids: List[str]) -> List[KnowledgeDocument]:
        """
        Retrieve multiple knowledge documents by their IDs, loading and summarizing them as needed.

        Args:
            document_ids: A list of knowledge document IDs to retrieve.

        Returns:
            A list of retrieved knowledge documents.
        """
        
        knowledge_documents = self.knowledge_store.load_documents(legal_knowledge_document_ids, self.legal_knowledge_document_loader, self.document_summarizer)
        knowledge_documents += self.knowledge_store.load_documents(expert_knowledge_document_ids, self.expert_knowledge_document_loader, self.document_summarizer)
        return knowledge_documents

    def load_legal_knowledge_documents(self, document_ids: List[str]) -> List[KnowledgeDocument]:
        """
        Retrieve multiple legal knowledge documents by their IDs, loading and summarizing them as needed.

        Args:
            document_ids: A list of legal knowledge document IDs to retrieve.
        
        Returns:
            A list of retrieved legal knowledge documents.
        """
        for doc_id in document_ids:
            if not doc_id.startswith("https://opendata.eselpoint.cz/esel-esb/eli/cz/sb"):
                raise ValueError(f"Invalid legal knowledge document ID: {doc_id}")
        return self.knowledge_store.load_documents(document_ids, self.legal_knowledge_document_loader, self.document_summarizer)

    def load_expert_knowledge_documents(self, document_ids: List[str]) -> List[KnowledgeDocument]:
        """
        Retrieve multiple expert knowledge documents by their IDs, loading and summarizing them as needed.

        Args:
            document_ids: A list of expert knowledge document IDs to retrieve.

        Returns:
            A list of retrieved expert knowledge documents.
        """
        return self.knowledge_store.load_documents(document_ids, self.expert_knowledge_document_loader, self.document_summarizer)

    def list_legal_knowledge_documents(self, base_dir: str = "data/knowledge_base/esel") -> List[Dict[str, str]]:
        """
        List all available legal knowledge documents.

        Args:
            base_dir: The base directory containing legal knowledge documents. Default is 'data/knowledge_base/esel'.

        Returns:
            A list of dictionaries containing summary information (id, title, contentSummary, elementType) for each document.
        """
        return self._list_documents_in_directory(base_dir)

    def list_expert_knowledge_documents(self, base_dir: str = "data/knowledge_base/local") -> List[Dict[str, str]]:
        """
        List all available expert knowledge documents.

        Args:
            base_dir: The base directory containing expert knowledge documents. Default is 'data/knowledge_base/local'.

        Returns:
            A list of dictionaries containing summary information (id, title, contentSummary, elementType) for each document.
        """
        return self._list_documents_in_directory(base_dir)

    def _list_documents_in_directory(self, base_dir: str) -> List[Dict[str, str]]:
        """
        List all *.content.json files in the given directory and extract their summary information.

        Args:
            base_dir: The base directory to search for content.json files.

        Returns:
            A list of dictionaries with id, title, contentSummary, and elementType for each document.
        """
        documents = []
        base_path = Path(base_dir)
        
        if not base_path.exists():
            return documents
        
        # Search for all *.content.json files recursively
        for content_file in base_path.rglob("*.content.json"):
            try:
                with open(content_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Extract only the required fields
                    doc_summary = {
                        "id": data.get("id", ""),
                        "title": data.get("title", ""),
                        "contentSummary": data.get("contentSummary", ""),
                        "elementType": data.get("elementType", "")
                    }
                    documents.append(doc_summary)
            except Exception as e:
                # Log error but continue processing other files
                print(f"Error reading {content_file}: {e}")
                continue
        
        return documents

    def get_knowledge_document_element(self, element_id: str) -> KnowledgeDocumentElement:
        """
        Retrieve a knowledge document element by its ID from all loaded documents.

        Args:
            element_id: The ID of the knowledge document element to retrieve.

        Returns:
            The knowledge document element with the specified ID.
            
        Raises:
            ValueError: If the element is not found in any loaded document.
        """
        # Try to find the element in all documents
        # The element_id should contain the document_id as a prefix
        for document_id in self.knowledge_store.documents:
            element = self.knowledge_store.get_knowledge_document_element(document_id, element_id)
            if element:
                return element
        
        raise ValueError(f"Knowledge document element not found: {element_id}")

    def get_knowledge_document_outline_from_summaries(self, document: KnowledgeDocument) -> str:
        """
        Generate an outline of a knowledge document based on its summaries.

        Args:
            document: The knowledge document to generate the outline for.

        Returns:
            A string representing the outline of the knowledge document.
        """
        outline = "<document>\n"
        outline += f"\t<id>{document.id}</id>\n"
        outline += f"\t<title>{document.title}</title>\n"
        outline += f"\t<summary>{document.contentSummary or ''}</summary>\n"
        
        # Insert hierarchical serialization of knowledge document elements
        for child_element in document.childElements:
            outline += self._serialize_element_hierarchy(child_element, 1, document.id)
        
        outline += "</document>"
        return outline
    
    def _serialize_element_hierarchy(self, element: KnowledgeDocumentElement, indent_level: int, document_id: str) -> str:
        """
        Recursively serialize a knowledge document element and its children into XML format.
        
        Args:
            element: The knowledge document element to serialize.
            indent_level: The current indentation level for proper XML formatting.
            document_id: The base document ID to use for making relative IDs.
            
        Returns:
            A string representing the XML serialization of the element and its children.
        """
        indent = "\t" * indent_level
        
        # Create relative ID by removing the document ID prefix
        relative_id = element.id
        if element.id.startswith(document_id):
            relative_id = element.id[len(document_id):]
            # Remove leading separator characters like '/', '#', etc.
            relative_id = relative_id.lstrip('/#')
        
        xml_content = f"{indent}<section>\n"
        xml_content += f"{indent}\t<id>{relative_id}</id>\n"
        xml_content += f"{indent}\t<summary>{element.contentSummary or ''}</summary>\n"
        
        # Recursively serialize child elements
        for child_element in element.childElements:
            xml_content += self._serialize_element_hierarchy(child_element, indent_level + 1, document_id)
        
        xml_content += f"{indent}</section>\n"
        return xml_content
