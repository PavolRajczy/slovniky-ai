from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from ontology.domain import OntologyElement

@dataclass
class KnowledgeDocumentElement:
    # A knowledge document element represents a distinct part of a knowledge document.
    id: str                                                                             # A globally unique identifier of the element. It is unique across the entire knowledge base.
    title: Optional[str]                                                                # Title of the element.
    content: Optional[str]                                                              # Textual content of the element that describes in a textual form a piece of the domain knowledge.
    contentSummary: Optional[str]                                                       # Textual summary of the element content that summarizes in a concise form the main parts of the domain knowledge covered in this element.
    childElements: List[KnowledgeDocumentElement] = field(default_factory=list)        # Child elements of the document element.
    parentElement: Optional[KnowledgeDocumentElement] = None                           # Parent element of the document element.
    elementType: str = "KnowledgeDocumentElement"                                      # The type of the document element (e.g., Chapter, Section, Paragraph, etc).
    definedOntologyElements: List[OntologyElement] = field(default_factory=list)       # List of ontology elements defined within the document element.
                                                                                        #   An ontology element is defined within the document element if the content includes a definitory phrase that introduces the element.
    specifiedOntologyElements: List[OntologyElement] = field(default_factory=list)     # List of ontology elements specified within the document element.
                                                                                        #   An ontology element is specified within the document element if the content includes a specification of the element semantics, meaning, context, usage, etc. but is not definitory.
    referencedOntologyElements: List[OntologyElement] = field(default_factory=list)    # List of ontology elements referenced within the document element.
                                                                                        #   An ontology element is referenced within the document element if the content includes a reference to the element without defining or specifying it.

@dataclass
class KnowledgeDocument(KnowledgeDocumentElement):
    # A knowledge document is a textual representation of domain knowledge hierarchically structured to elements.
    # A knowledge document is a specialized type of knowledge document element that represents an entire document.
    elementType: str = "KnowledgeDocument"                      # The type of the document element is fixed to "KnowledgeDocument".
    cacheFilePath: Optional[str] = None                         # Path to the cached content of this document, set by KnowledgeDocumentLoader implementations.