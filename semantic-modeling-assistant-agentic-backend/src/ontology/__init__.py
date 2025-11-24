"""
Ontology module for semantic modeling assistant.

This module provides functionality for working with domain ontologies,
including data models, storage, and high-level service interfaces.
"""

from .domain import Ontology, OntologyClass, OntologyAttribute, OntologyRelationship, OntologyElement
from .store import OntologyStore, FilesystemOntologyStore
from .service import OntologyService

__all__ = [
    'Ontology',
    'OntologyClass', 
    'OntologyAttribute',
    'OntologyRelationship',
    'OntologyElement',
    'OntologyStore',
    'FilesystemOntologyStore',
    'OntologyService'
]