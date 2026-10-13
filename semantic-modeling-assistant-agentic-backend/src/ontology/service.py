"""
Ontology Service Module

This module provides a high-level service interface for working with ontologies.
It abstracts the storage layer and provides convenient methods for loading and storing
ontologies by URI.
"""

from typing import Optional, List
import os
from rdflib import URIRef

from .domain import Ontology
from .store import OntologyStore, FilesystemOntologyStore
from .edit_operations import OntologyEditOperation
from .edit_operation_handlers import EditOperationHandler

class OntologyService:
    """
    Service class that provides a high-level interface for ontology operations.
    
    This service acts as a facade over the ontology store, providing convenient
    methods for other modules to load and store ontologies without directly
    interacting with the storage layer.
    """
    
    def __init__(self, store: Optional[OntologyStore] = None):
        """
        Initialize the OntologyService with a store.
        
        Args:
            store (Optional[OntologyStore]): The store to use for persistence.
                                           If None, a default FilesystemOntologyStore will be created.
        """
        if store is not None:
            self.store = store
        else:
            # Allow overriding the base directory via environment variable for tests
            base_dir = os.getenv("ONTOLOGY_BASE_DIR", "data/ontologies")
            self.store = FilesystemOntologyStore(base_dir=base_dir)
        self._edit_handler = EditOperationHandler()
    
    def load_ontology(self, ontology_uri: str) -> Ontology:
        """
        Load an ontology by its URI.
        
        Args:
            ontology_uri (str): The URI of the ontology to load.
            
        Returns:
            Ontology: The loaded ontology.
            
        Raises:
            FileNotFoundError: If the ontology with the given URI is not found.
            ValueError: If the ontology URI is invalid or empty.
        """
        if not ontology_uri or not ontology_uri.strip():
            raise ValueError("Ontology URI cannot be empty or None")
        
        return self.store.load_ontology(ontology_uri.strip())
    
    def store_ontology(self, ontology: Ontology) -> None:
        """
        Store an ontology.
        
        Args:
            ontology (Ontology): The ontology to store.
            
        Raises:
            ValueError: If the ontology is None or has invalid data.
        """
        if ontology is None:
            raise ValueError("Ontology cannot be None")
        
        if ontology.uri is None:
            raise ValueError("Ontology URI cannot be None")
        
        # FilesystemOntologyStore.store_ontology enforces a "load-before-store"
        # contract by checking that ontology.uri is present in its in-memory
        # `ontologies` dict. For ontologies that have just been constructed
        # from external data (e.g. imported from Dataspecer) there is nothing
        # to load yet, and the previous "try load first" workaround was
        # fragile: when the on-disk file existed under the same safe dirname
        # but with a slightly different URI (e.g. trailing '#' added by
        # _normalize_base_uri), the cache would be populated with the *old*
        # URI and the subsequent store call would still raise
        # "Ontology not found in the store". Register the exact ontology we
        # are about to store directly to make the operation deterministic.
        if hasattr(self.store, 'ontologies'):
            self.store.ontologies[ontology.uri] = ontology
        
        self.store.store_ontology(ontology)
    
    def ontology_exists(self, ontology_uri: str) -> bool:
        """
        Check if an ontology with the given URI exists in the store.
        
        Args:
            ontology_uri (str): The URI of the ontology to check.
            
        Returns:
            bool: True if the ontology exists, False otherwise.
        """
        if not ontology_uri or not ontology_uri.strip():
            return False
        
        # Use store.exists to avoid side effects (like creating an empty file)
        return getattr(self.store, "exists", lambda uri: False)(ontology_uri.strip())
    
    def create_empty_ontology(self, ontology_uri: str, label: str, description: Optional[str] = None) -> Ontology:
        """
        Create a new empty ontology with the given URI and metadata.
        
        Args:
            ontology_uri (str): The URI for the new ontology.
            label (str): A human-readable label for the ontology.
            description (Optional[str]): An optional description of the ontology.
            
        Returns:
            Ontology: The newly created empty ontology.
            
        Raises:
            ValueError: If the ontology URI or label is invalid.
        """
        if not ontology_uri or not ontology_uri.strip():
            raise ValueError("Ontology URI cannot be empty or None")
        
        if not label or not label.strip():
            raise ValueError("Ontology label cannot be empty or None")
        
        ontology = Ontology(
            uri=URIRef(ontology_uri.strip()),
            label=label.strip(),
            description=description.strip() if description else None,
            classes={},
            attributes={},
            relationships={}
        )
        
        return ontology
    
    def apply_edit_operation(self, ontology: Ontology, operation: OntologyEditOperation) -> Ontology:
        """
        Apply an edit operation to the supplied ontology and return the edited ontology.
        
        Args:
            ontology (Ontology): The ontology to apply the operation to.
            operation (OntologyEditOperation): The edit operation to apply.
            
        Returns:
            Ontology: A new ontology with the operation applied.
            
        Raises:
            ValueError: If the operation is invalid or cannot be applied.
            KeyError: If trying to update/delete a non-existent entity.
        """
        if ontology is None:
            raise ValueError("Ontology cannot be None")
        
        if operation is None:
            raise ValueError("Operation cannot be None")
        
        return self._edit_handler.apply_operation(ontology, operation)

    def list_ontologies(self) -> List[Ontology]:
        """List all ontologies available in the store.

        Returns:
            List[Ontology]: All ontologies reconstructed from storage.
        """
        # Use store.list_all if available; otherwise, fallback to scanning is not supported
        if hasattr(self.store, "list_all"):
            return self.store.list_all()
        return []
