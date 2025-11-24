"""
Ontology Edit Operations Module

This module defines value objects representing various edit operations that can be applied
to ontologies. These are pure data classes without behavior - the actual application logic
is implemented elsewhere using the registry pattern.
"""

from abc import ABC
from dataclasses import dataclass
from typing import Optional, List
from rdflib import URIRef
from enum import Enum, auto
from .domain import Kind


class OperationType(Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"

@dataclass(frozen=True)
class OntologyEditOperation(ABC):
    """
    Abstract base class for ontology edit operations.
    This is a value object that only holds operation data.
    """
    pass

# Class Operations
@dataclass(frozen=True)
class CreateClassOperation(OntologyEditOperation):
    """Operation to create a new ontology class."""
    uri: URIRef
    label: str
    kind: Optional[Kind] = None
    definition: Optional[str] = None
    description: Optional[str] = None
    generalization_uris: Optional[List[URIRef]] = None
    definition_references: Optional[List[str]] = None
    specification_references: Optional[List[str]] = None
    references: Optional[List[str]] = None
    operation_type: OperationType = OperationType.CREATE


@dataclass(frozen=True)
class UpdateClassOperation(OntologyEditOperation):
    """Operation to update an existing ontology class."""
    uri: URIRef
    label: Optional[str] = None
    kind: Optional[Kind] = None
    definition: Optional[str] = None
    description: Optional[str] = None
    generalization_uris: Optional[List[URIRef]] = None
    definition_references: Optional[List[str]] = None
    specification_references: Optional[List[str]] = None
    references: Optional[List[str]] = None
    operation_type: OperationType = OperationType.UPDATE

@dataclass(frozen=True)
class DeleteClassOperation(OntologyEditOperation):
    """Operation to delete an ontology class."""
    uri: URIRef
    operation_type: OperationType = OperationType.DELETE


# Attribute Operations
@dataclass(frozen=True)
class CreateAttributeOperation(OntologyEditOperation):
    """Operation to create a new ontology attribute."""
    uri: URIRef
    label: str
    owning_class_uri: URIRef
    definition: Optional[str] = None
    description: Optional[str] = None
    definition_references: Optional[List[str]] = None
    specification_references: Optional[List[str]] = None
    references: Optional[List[str]] = None
    operation_type: OperationType = OperationType.CREATE


@dataclass(frozen=True)
class UpdateAttributeOperation(OntologyEditOperation):
    """Operation to update an existing ontology attribute."""
    uri: URIRef
    label: Optional[str] = None
    owning_class_uri: Optional[URIRef] = None
    definition: Optional[str] = None
    description: Optional[str] = None
    definition_references: Optional[List[str]] = None
    specification_references: Optional[List[str]] = None
    references: Optional[List[str]] = None
    operation_type: OperationType = OperationType.UPDATE


@dataclass(frozen=True)
class DeleteAttributeOperation(OntologyEditOperation):
    """Operation to delete an ontology attribute."""
    uri: URIRef
    operation_type: OperationType = OperationType.DELETE


# Relationship Operations
@dataclass(frozen=True)
class CreateRelationshipOperation(OntologyEditOperation):
    """Operation to create a new ontology relationship."""
    uri: URIRef
    label: str
    source_class_uri: URIRef
    target_class_uri: URIRef
    definition: Optional[str] = None
    description: Optional[str] = None
    definition_references: Optional[List[str]] = None
    specification_references: Optional[List[str]] = None
    references: Optional[List[str]] = None
    operation_type: OperationType = OperationType.CREATE


@dataclass(frozen=True)
class UpdateRelationshipOperation(OntologyEditOperation):
    """Operation to update an existing ontology relationship."""
    uri: URIRef
    label: Optional[str] = None
    source_class_uri: Optional[URIRef] = None
    target_class_uri: Optional[URIRef] = None
    definition: Optional[str] = None
    description: Optional[str] = None
    definition_references: Optional[List[str]] = None
    specification_references: Optional[List[str]] = None
    references: Optional[List[str]] = None
    operation_type: OperationType = OperationType.UPDATE


@dataclass(frozen=True)
class DeleteRelationshipOperation(OntologyEditOperation):
    """Operation to delete an ontology relationship."""
    uri: URIRef
    operation_type: OperationType = OperationType.DELETE