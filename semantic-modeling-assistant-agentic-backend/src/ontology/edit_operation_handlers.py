"""
Ontology Edit Operation Handlers Module

This module implements the application logic for ontology edit operations using a registry pattern.
The EditOperationHandler class maintains a registry of operation types to handler functions, providing
a clean way to dispatch operations without long if/elif chains.
"""

from typing import Dict, Callable, Type, List

from .domain import Ontology, OntologyClass, OntologyAttribute, OntologyElement, OntologyRelationship, Kind
from .edit_operations import (
    OntologyEditOperation, CreateClassOperation, UpdateClassOperation, DeleteClassOperation,
    CreateAttributeOperation, UpdateAttributeOperation, DeleteAttributeOperation,
    CreateRelationshipOperation, UpdateRelationshipOperation, DeleteRelationshipOperation
)


class EditOperationError(ValueError):
    """Represents an error that occurs during the application of an ontology edit operation."""
    pass

class CreatedElementExistsError(EditOperationError):
    """Raised when attempting to create an element that already exists."""
    pass

class UpdatedElementNotExistsError(EditOperationError):
    """Raised when attempting to update an element that does not exist."""
    pass

class DeletedElementNotExistsError(EditOperationError):
    """Raised when attempting to delete an element that does not exist."""
    pass

class ReferrencedElementNotExistsError(EditOperationError):
    """Raised when a referenced element does not exist."""
    pass

class EditOperationHandler:
    """Handles the application of edit operations to ontologies using a registry pattern."""
    
    def __init__(self):
        """Initialize the handler with the registry of operation handlers."""
        # Registry of operation types to handler functions
        self._handlers: Dict[Type[OntologyEditOperation], Callable[[Ontology, OntologyEditOperation], Ontology]] = {
            CreateClassOperation: self._handle_create_class,
            UpdateClassOperation: self._handle_update_class,
            DeleteClassOperation: self._handle_delete_class,
            CreateAttributeOperation: self._handle_create_attribute,
            UpdateAttributeOperation: self._handle_update_attribute,
            DeleteAttributeOperation: self._handle_delete_attribute,
            CreateRelationshipOperation: self._handle_create_relationship,
            UpdateRelationshipOperation: self._handle_update_relationship,
            DeleteRelationshipOperation: self._handle_delete_relationship,
        }
    
    def apply_operation(self, ontology: Ontology, operation: OntologyEditOperation) -> OntologyElement:
        """Apply an edit operation to the ontology."""
        handler = self._handlers.get(type(operation))
        if handler is None:
            raise ValueError(f"No handler registered for operation type: {type(operation)}")
        
        return handler(ontology, operation)
    
    def _find_class_by_uri(self, ontology: Ontology, uri) -> OntologyClass:
        """Helper method to find a class by URI."""
        if uri not in ontology.classes:
            return None
        return ontology.classes[uri]
    
    def _update_class_generalizations(self, ontology: Ontology, ontology_class: OntologyClass, generalization_uris: List):
        """Helper method to update class generalization relationships."""
        # Clear existing generalizations
        for old_generalization in ontology_class.generalizations:
            if ontology_class in old_generalization.specializations:
                old_generalization.specializations.remove(ontology_class)
        
        ontology_class.generalizations.clear()
        
        # Add new generalizations
        if generalization_uris:
            for gen_uri in generalization_uris:
                generalization_class = self._find_class_by_uri(ontology, gen_uri)
                if not generalization_class:
                    raise ReferrencedElementNotExistsError(f"Generalization class with URI {gen_uri} does not exist")
                ontology_class.generalizations.append(generalization_class)
                if ontology_class not in generalization_class.specializations:
                    generalization_class.specializations.append(ontology_class)
    
    def _remove_class_relationships(self, ontology: Ontology, ontology_class: OntologyClass):
        """Helper method to clean up relationships when deleting a class."""
        # Remove from generalizations/specializations
        for generalization in ontology_class.generalizations:
            if ontology_class in generalization.specializations:
                generalization.specializations.remove(ontology_class)
        
        for specialization in ontology_class.specializations:
            if ontology_class in specialization.generalizations:
                specialization.generalizations.remove(ontology_class)
        
        # Remove attributes owned by this class
        attributes_to_remove = [attr for attr in ontology_class.attributes]
        for attr in attributes_to_remove:
            if attr.uri in ontology.attributes:
                del ontology.attributes[attr.uri]
        
        # Remove relationships involving this class
        relationships_to_remove = ontology_class.outgoingRelationships + ontology_class.incomingRelationships
        for rel in relationships_to_remove:
            if rel.uri in ontology.relationships:
                del ontology.relationships[rel.uri]
            # Clean up references in other classes
            if rel.sourceClass != ontology_class and rel in rel.sourceClass.outgoingRelationships:
                rel.sourceClass.outgoingRelationships.remove(rel)
            if rel.targetClass != ontology_class and rel in rel.targetClass.incomingRelationships:
                rel.targetClass.incomingRelationships.remove(rel)
    
    # Class operation handlers
    def _handle_create_class(self, ontology: Ontology, operation: CreateClassOperation) -> OntologyElement:
        if operation.uri in ontology.classes:
            raise CreatedElementExistsError(f"Class with URI {operation.uri} already exists")
        
        new_class = OntologyClass(
            uri=operation.uri,
            label=operation.label,
            kind=operation.kind or Kind.SUBJECT,  # Default to SUBJECT if not specified
            definition=operation.definition,
            description=operation.description,
            generalizations=[],
            specializations=[],
            attributes=[],
            outgoingRelationships=[],
            incomingRelationships=[],
            definition_references=operation.definition_references or [],
            specification_references=operation.specification_references or [],
            references=operation.references or []
        )
        
        ontology.classes[operation.uri] = new_class
        
        # Set up generalization relationships
        if operation.generalization_uris:
            self._update_class_generalizations(ontology, new_class, operation.generalization_uris)
        
        return new_class

    def _handle_update_class(self, ontology: Ontology, operation: UpdateClassOperation) -> OntologyElement:
        if operation.uri not in ontology.classes:
            raise UpdatedElementNotExistsError(f"Class with URI {operation.uri} does not exist")
        
        existing_class = ontology.classes[operation.uri]
        
        # Update basic properties
        if operation.label is not None:
            existing_class.label = operation.label
        if operation.kind is not None:
            existing_class.kind = operation.kind
        if operation.definition is not None:
            existing_class.definition = operation.definition
        if operation.description is not None:
            existing_class.description = operation.description
        
        # Accumulate reference lists (merge with existing references)
        if operation.definition_references is not None:
            # Add new references while avoiding duplicates
            for ref in operation.definition_references:
                if ref not in existing_class.definition_references:
                    existing_class.definition_references.append(ref)
        if operation.specification_references is not None:
            # Add new references while avoiding duplicates
            for ref in operation.specification_references:
                if ref not in existing_class.specification_references:
                    existing_class.specification_references.append(ref)
        if operation.references is not None:
            # Add new references while avoiding duplicates
            for ref in operation.references:
                if ref not in existing_class.references:
                    existing_class.references.append(ref)
        
        # Update generalization relationships
        if operation.generalization_uris is not None:
            self._update_class_generalizations(ontology, existing_class, operation.generalization_uris)

        return existing_class

    def _handle_delete_class(self, ontology: Ontology, operation: DeleteClassOperation) -> OntologyElement:
        if operation.uri not in ontology.classes:
            raise DeletedElementNotExistsError(f"Class with URI {operation.uri} does not exist")
        
        ontology_class = ontology.classes[operation.uri]
        
        # Clean up all relationships involving this class
        self._remove_class_relationships(ontology, ontology_class)
        
        # Remove the class itself
        del ontology.classes[operation.uri]

        return ontology_class

    # Attribute operation handlers
    def _handle_create_attribute(self, ontology: Ontology, operation: CreateAttributeOperation) -> OntologyElement:
        if operation.uri in ontology.attributes:
            raise CreatedElementExistsError(f"Attribute with URI {operation.uri} already exists")
        
        owning_class = self._find_class_by_uri(ontology, operation.owning_class_uri)
        if not owning_class:
            raise ReferrencedElementNotExistsError(f"Owning class with URI {operation.owning_class_uri} does not exist")
        
        new_attribute = OntologyAttribute(
            uri=operation.uri,
            label=operation.label,
            definition=operation.definition,
            description=operation.description,
            owningClass=owning_class,
            definition_references=operation.definition_references or [],
            specification_references=operation.specification_references or [],
            references=operation.references or []
        )
        
        ontology.attributes[operation.uri] = new_attribute
        owning_class.attributes.append(new_attribute)

        return new_attribute

    def _handle_update_attribute(self, ontology: Ontology, operation: UpdateAttributeOperation) -> OntologyElement:
        if operation.uri not in ontology.attributes:
            raise UpdatedElementNotExistsError(f"Attribute with URI {operation.uri} does not exist")
        
        existing_attribute = ontology.attributes[operation.uri]
        
        # Update basic properties
        if operation.label is not None:
            existing_attribute.label = operation.label
        if operation.definition is not None:
            existing_attribute.definition = operation.definition
        if operation.description is not None:
            existing_attribute.description = operation.description
        
        # Accumulate reference lists (merge with existing references)
        if operation.definition_references is not None:
            # Add new references while avoiding duplicates
            for ref in operation.definition_references:
                if ref not in existing_attribute.definition_references:
                    existing_attribute.definition_references.append(ref)
        if operation.specification_references is not None:
            # Add new references while avoiding duplicates
            for ref in operation.specification_references:
                if ref not in existing_attribute.specification_references:
                    existing_attribute.specification_references.append(ref)
        if operation.references is not None:
            # Add new references while avoiding duplicates
            for ref in operation.references:
                if ref not in existing_attribute.references:
                    existing_attribute.references.append(ref)
        
        # Update owning class if changed
        if operation.owning_class_uri is not None:
            old_owning_class = existing_attribute.owningClass
            new_owning_class = self._find_class_by_uri(ontology, operation.owning_class_uri)
            if not new_owning_class:
                raise ReferrencedElementNotExistsError(f"Owning class with URI {operation.owning_class_uri} does not exist")
            
            if old_owning_class != new_owning_class:
                # Remove from old owning class
                if existing_attribute in old_owning_class.attributes:
                    old_owning_class.attributes.remove(existing_attribute)
                
                # Add to new owning class
                existing_attribute.owningClass = new_owning_class
                if existing_attribute not in new_owning_class.attributes:
                    new_owning_class.attributes.append(existing_attribute)

        return existing_attribute

    def _handle_delete_attribute(self, ontology: Ontology, operation: DeleteAttributeOperation) -> OntologyElement:
        if operation.uri not in ontology.attributes:
            raise DeletedElementNotExistsError(f"Attribute with URI {operation.uri} does not exist")
        
        attribute = ontology.attributes[operation.uri]
        
        # Remove from owning class
        if attribute in attribute.owningClass.attributes:
            attribute.owningClass.attributes.remove(attribute)
        
        # Remove from ontology
        del ontology.attributes[operation.uri]

        return attribute

    # Relationship operation handlers
    def _handle_create_relationship(self, ontology: Ontology, operation: CreateRelationshipOperation) -> OntologyElement:
        if operation.uri in ontology.relationships:
            raise CreatedElementExistsError(f"Relationship with URI {operation.uri} already exists")
        
        source_class = self._find_class_by_uri(ontology, operation.source_class_uri)
        if not source_class:
            raise ReferrencedElementNotExistsError(f"Source class with URI {operation.source_class_uri} does not exist")
        
        target_class = self._find_class_by_uri(ontology, operation.target_class_uri)
        if not target_class:
            raise ReferrencedElementNotExistsError(f"Target class with URI {operation.target_class_uri} does not exist")
        
        new_relationship = OntologyRelationship(
            uri=operation.uri,
            label=operation.label,
            definition=operation.definition,
            description=operation.description,
            sourceClass=source_class,
            targetClass=target_class,
            definition_references=operation.definition_references or [],
            specification_references=operation.specification_references or [],
            references=operation.references or []
        )
        
        ontology.relationships[operation.uri] = new_relationship
        source_class.outgoingRelationships.append(new_relationship)
        target_class.incomingRelationships.append(new_relationship)

        return new_relationship

    def _handle_update_relationship(self, ontology: Ontology, operation: UpdateRelationshipOperation) -> OntologyElement:
        if operation.uri not in ontology.relationships:
            raise UpdatedElementNotExistsError(f"Relationship with URI {operation.uri} does not exist")
        
        existing_relationship = ontology.relationships[operation.uri]
        
        # Update basic properties
        if operation.label is not None:
            existing_relationship.label = operation.label
        if operation.definition is not None:
            existing_relationship.definition = operation.definition
        if operation.description is not None:
            existing_relationship.description = operation.description
        
        # Accumulate reference lists (merge with existing references)
        if operation.definition_references is not None:
            # Add new references while avoiding duplicates
            for ref in operation.definition_references:
                if ref not in existing_relationship.definition_references:
                    existing_relationship.definition_references.append(ref)
        if operation.specification_references is not None:
            # Add new references while avoiding duplicates
            for ref in operation.specification_references:
                if ref not in existing_relationship.specification_references:
                    existing_relationship.specification_references.append(ref)
        if operation.references is not None:
            # Add new references while avoiding duplicates
            for ref in operation.references:
                if ref not in existing_relationship.references:
                    existing_relationship.references.append(ref)
        
        # Update source class if changed
        if operation.source_class_uri is not None:
            old_source_class = existing_relationship.sourceClass
            new_source_class = self._find_class_by_uri(ontology, operation.source_class_uri)
            if not new_source_class:
                raise ReferrencedElementNotExistsError(f"Source class with URI {operation.source_class_uri} does not exist")
            
            if old_source_class != new_source_class:
                # Remove from old source class
                if existing_relationship in old_source_class.outgoingRelationships:
                    old_source_class.outgoingRelationships.remove(existing_relationship)
                
                # Add to new source class
                existing_relationship.sourceClass = new_source_class
                if existing_relationship not in new_source_class.outgoingRelationships:
                    new_source_class.outgoingRelationships.append(existing_relationship)
        
        # Update target class if changed
        if operation.target_class_uri is not None:
            old_target_class = existing_relationship.targetClass
            new_target_class = self._find_class_by_uri(ontology, operation.target_class_uri)
            if not new_target_class:
                raise ReferrencedElementNotExistsError(f"Target class with URI {operation.target_class_uri} does not exist")
            
            if old_target_class != new_target_class:
                # Remove from old target class
                if existing_relationship in old_target_class.incomingRelationships:
                    old_target_class.incomingRelationships.remove(existing_relationship)
                
                # Add to new target class
                existing_relationship.targetClass = new_target_class
                if existing_relationship not in new_target_class.incomingRelationships:
                    new_target_class.incomingRelationships.append(existing_relationship)
        
        return existing_relationship

    def _handle_delete_relationship(self, ontology: Ontology, operation: DeleteRelationshipOperation) -> OntologyElement:
        if operation.uri not in ontology.relationships:
            raise DeletedElementNotExistsError(f"Relationship with URI {operation.uri} does not exist")
        
        relationship = ontology.relationships[operation.uri]
        
        # Remove from source class
        if relationship in relationship.sourceClass.outgoingRelationships:
            relationship.sourceClass.outgoingRelationships.remove(relationship)
        
        # Remove from target class
        if relationship in relationship.targetClass.incomingRelationships:
            relationship.targetClass.incomingRelationships.remove(relationship)
        
        # Remove from ontology
        del ontology.relationships[operation.uri]

        return relationship