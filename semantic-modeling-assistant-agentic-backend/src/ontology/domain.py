from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Tuple, Any
from rdflib import URIRef

class Kind(Enum):
    """Enum representing the kind of an ontology class."""
    SUBJECT = "subject"
    OBJECT = "object"

@dataclass
class OntologyElement:
    # A base class for all ontology elements.
    uri: URIRef                                             # A global identifier for the ontology element in the form of URI.
    label: str                                              # A human-readable label for the ontology element.
    definition: Optional[str]                               # A formal definition of the ontology element.
    description: Optional[str]                              # A human-readable description providing more context about the ontology element semantics.
    
    def __repr__(self) -> str:
        """Shallow repr to avoid deep recursion in debugger."""
        class_name = self.__class__.__name__
        uri_str = str(self.uri) if self.uri else "None"
        label_str = self.label[:30] + "..." if len(self.label) > 30 else self.label
        return f"{class_name}(uri={uri_str!r}, label={label_str!r})"

@dataclass
class OntologyClass(OntologyElement):
    # A class representing an ontology class in an ontology.
    kind: Kind = Kind.SUBJECT                               # The kind of this class, either SUBJECT or OBJECT. Defaults to SUBJECT.
    generalizations: List[OntologyClass] = field(default_factory=list, compare=False)   # The ontology classes that are generalizations of this class (i.e. the classes this class inherits from). This is a list of classes that are more general than this class.
    specializations: List[OntologyClass] = field(default_factory=list, compare=False)   # The ontology classes that are specializations of this class (i.e. the classes this class generalizes). This is a list of classes that are more specific than this class.
    attributes: List[OntologyAttribute] = field(default_factory=list, compare=False)    # The attributes that belong to this class.
    outgoingRelationships: List[OntologyRelationship] = field(default_factory=list, compare=False)  # The relationships where this class is the source class.
    incomingRelationships: List[OntologyRelationship] = field(default_factory=list, compare=False)  # The relationships where this class is the target class.
    definition_references: List[str] = field(default_factory=list)     # List of knowledge base element IDs that explicitly define this ontology element.
    specification_references: List[str] = field(default_factory=list)  # List of knowledge base element IDs that explicitly specify or describe this ontology element.
    references: List[str] = field(default_factory=list)                # List of knowledge base element IDs that generally reference this ontology element without being explicit in defining, specifying or describing it.
    
    def __repr__(self) -> str:
        """Shallow repr to avoid deep recursion in debugger."""
        uri_str = str(self.uri) if self.uri else "None"
        label_str = self.label[:30] + "..." if len(self.label) > 30 else self.label
        return (f"OntologyClass(uri={uri_str!r}, label={label_str!r}, kind={self.kind.value}, "
                f"generalizations={len(self.generalizations)}, specializations={len(self.specializations)}, "
                f"attributes={len(self.attributes)}, outgoingRels={len(self.outgoingRelationships)}, "
                f"incomingRels={len(self.incomingRelationships)})")

@dataclass
class OntologyAttribute(OntologyElement):
    # A class representing an ontology attribute in an ontology.
    # Corresponds to RDF datatype property.
    owningClass: Optional[OntologyClass] = None             # The ontology class that owns this attribute. Corresponds to RDF domain.
    definition_references: List[str] = field(default_factory=list)     # List of knowledge base element IDs that explicitly define this ontology element.
    specification_references: List[str] = field(default_factory=list)  # List of knowledge base element IDs that explicitly specify or describe this ontology element.
    references: List[str] = field(default_factory=list)                # List of knowledge base element IDs that generally reference this ontology element without being explicit in defining, specifying or describing it.
    
    def __repr__(self) -> str:
        """Shallow repr to avoid deep recursion in debugger."""
        uri_str = str(self.uri) if self.uri else "None"
        label_str = self.label[:30] + "..." if len(self.label) > 30 else self.label
        owner_uri = str(self.owningClass.uri) if self.owningClass and self.owningClass.uri else "None"
        return f"OntologyAttribute(uri={uri_str!r}, label={label_str!r}, owningClass={owner_uri!r})"

@dataclass
class OntologyRelationship(OntologyElement):
    # A class representing an ontology relationship in an ontology.
    # Corresponds to RDF object property.
    sourceClass: Optional[OntologyClass] = None             # The source class of this relationship. Corresponds to RDF domain.
    targetClass: Optional[OntologyClass] = None             # The target class of this relationship. Corresponds to RDF range.
    definition_references: List[str] = field(default_factory=list)     # List of knowledge base element IDs that explicitly define this ontology element.
    specification_references: List[str] = field(default_factory=list)  # List of knowledge base element IDs that explicitly specify or describe this ontology element.
    references: List[str] = field(default_factory=list)                # List of knowledge base element IDs that generally reference this ontology element without being explicit in defining, specifying or describing it.
    
    def __repr__(self) -> str:
        """Shallow repr to avoid deep recursion in debugger."""
        uri_str = str(self.uri) if self.uri else "None"
        label_str = self.label[:30] + "..." if len(self.label) > 30 else self.label
        source_uri = str(self.sourceClass.uri) if self.sourceClass and self.sourceClass.uri else "None"
        target_uri = str(self.targetClass.uri) if self.targetClass and self.targetClass.uri else "None"
        return f"OntologyRelationship(uri={uri_str!r}, label={label_str!r}, source={source_uri!r}, target={target_uri!r})"

@dataclass
class Ontology:
    # A class representing an ontology.
    uri: URIRef                                             # The global identifier for the ontology in the form of URI.
    label: str                                              # A human-readable label for the ontology.
    description: Optional[str]                              # A human-readable description providing more context about the ontology semantics.
    classes: Dict[URIRef, OntologyClass] = field(default_factory=dict, compare=False)       # The ontology classes that belong to this ontology.
    attributes: Dict[URIRef, OntologyAttribute] = field(default_factory=dict, compare=False)  # The ontology attributes that belong to this ontology.
    relationships: Dict[URIRef, OntologyRelationship] = field(default_factory=dict, compare=False)  # The ontology relationships that belong to this ontology.
    
    def __repr__(self) -> str:
        """Shallow repr to avoid deep recursion in debugger."""
        uri_str = str(self.uri) if self.uri else "None"
        label_str = self.label[:30] + "..." if len(self.label) > 30 else self.label
        return (f"Ontology(uri={uri_str!r}, label={label_str!r}, "
                f"classes={len(self.classes)}, attributes={len(self.attributes)}, "
                f"relationships={len(self.relationships)})")