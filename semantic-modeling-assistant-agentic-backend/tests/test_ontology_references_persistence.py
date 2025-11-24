"""
Unit tests for ontology reference fields persistence.

Tests that definition_references, specification_references, and references fields
are properly persisted and loaded from ontology JSON files.
"""

import os
import sys
import tempfile
import shutil

# Ensure src/ is importable when running as a script
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from rdflib import URIRef

from ontology.domain import Ontology, OntologyClass, OntologyAttribute, OntologyRelationship, Kind
from ontology.store import FilesystemOntologyStore
from ontology.service import OntologyService
from ontology.edit_operations import (
    CreateClassOperation, UpdateClassOperation,
    CreateAttributeOperation, UpdateAttributeOperation,
    CreateRelationshipOperation, UpdateRelationshipOperation
)


def test_class_references_persistence():
    """Test that class reference fields are persisted and loaded correctly."""
    # Create a temporary directory for testing
    test_dir = tempfile.mkdtemp(prefix="test_ontology_refs_")
    
    try:
        # Initialize store and service
        store = FilesystemOntologyStore(test_dir)
        service = OntologyService(store)
        
        # Create ontology
        ontology_uri = "http://example.org/test-ontology"
        ontology = service.create_empty_ontology(
            ontology_uri=ontology_uri,
            label="Test Ontology",
            description="Test ontology for reference persistence"
        )
        
        # Create class with references
        create_op = CreateClassOperation(
            uri=URIRef("http://example.org/test-ontology/Vehicle"),
            label="Vehicle",
            kind=Kind.OBJECT,
            definition="A means of transportation",
            description="General vehicle class",
            definition_references=["kb_doc_1_section_2", "kb_doc_1_section_3"],
            specification_references=["kb_doc_2_chapter_1"],
            references=["kb_doc_3_paragraph_5", "kb_doc_4_section_1"]
        )
        
        service.apply_edit_operation(ontology, create_op)
        
        # Store the ontology
        service.store_ontology(ontology)
        
        # Load the ontology in a fresh store
        new_store = FilesystemOntologyStore(test_dir)
        new_service = OntologyService(new_store)
        loaded_ontology = new_service.load_ontology(ontology_uri)
        
        # Verify the class and its references were persisted
        vehicle_uri = URIRef("http://example.org/test-ontology/Vehicle")
        assert vehicle_uri in loaded_ontology.classes
        
        vehicle = loaded_ontology.classes[vehicle_uri]
        assert vehicle.label == "Vehicle"
        assert vehicle.definition == "A means of transportation"
        assert vehicle.definition_references == ["kb_doc_1_section_2", "kb_doc_1_section_3"]
        assert vehicle.specification_references == ["kb_doc_2_chapter_1"]
        assert vehicle.references == ["kb_doc_3_paragraph_5", "kb_doc_4_section_1"]
        
        print("✓ Class references persistence test passed")
        
    finally:
        # Clean up
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)


def test_attribute_references_persistence():
    """Test that attribute reference fields are persisted and loaded correctly."""
    test_dir = tempfile.mkdtemp(prefix="test_ontology_refs_")
    
    try:
        store = FilesystemOntologyStore(test_dir)
        service = OntologyService(store)
        
        ontology_uri = "http://example.org/test-ontology"
        ontology = service.create_empty_ontology(
            ontology_uri=ontology_uri,
            label="Test Ontology",
            description="Test ontology for reference persistence"
        )
        
        # Create a class first
        class_op = CreateClassOperation(
            uri=URIRef("http://example.org/test-ontology/Vehicle"),
            label="Vehicle",
            kind=Kind.OBJECT
        )
        service.apply_edit_operation(ontology, class_op)
        
        # Create attribute with references
        attr_op = CreateAttributeOperation(
            uri=URIRef("http://example.org/test-ontology/maxSpeed"),
            label="Maximum Speed",
            owning_class_uri=URIRef("http://example.org/test-ontology/Vehicle"),
            definition="The maximum speed of the vehicle",
            description="Speed in km/h",
            definition_references=["kb_doc_5_para_1"],
            specification_references=["kb_doc_5_para_2", "kb_doc_6_section_1"],
            references=["kb_doc_7_chapter_3"]
        )
        
        service.apply_edit_operation(ontology, attr_op)
        service.store_ontology(ontology)
        
        # Load and verify
        new_store = FilesystemOntologyStore(test_dir)
        new_service = OntologyService(new_store)
        loaded_ontology = new_service.load_ontology(ontology_uri)
        
        attr_uri = URIRef("http://example.org/test-ontology/maxSpeed")
        assert attr_uri in loaded_ontology.attributes
        
        attr = loaded_ontology.attributes[attr_uri]
        assert attr.label == "Maximum Speed"
        assert attr.definition_references == ["kb_doc_5_para_1"]
        assert attr.specification_references == ["kb_doc_5_para_2", "kb_doc_6_section_1"]
        assert attr.references == ["kb_doc_7_chapter_3"]
        
        print("✓ Attribute references persistence test passed")
        
    finally:
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)


def test_relationship_references_persistence():
    """Test that relationship reference fields are persisted and loaded correctly."""
    test_dir = tempfile.mkdtemp(prefix="test_ontology_refs_")
    
    try:
        store = FilesystemOntologyStore(test_dir)
        service = OntologyService(store)
        
        ontology_uri = "http://example.org/test-ontology"
        ontology = service.create_empty_ontology(
            ontology_uri=ontology_uri,
            label="Test Ontology",
            description="Test ontology for reference persistence"
        )
        
        # Create two classes
        class1_op = CreateClassOperation(
            uri=URIRef("http://example.org/test-ontology/Vehicle"),
            label="Vehicle",
            kind=Kind.OBJECT
        )
        service.apply_edit_operation(ontology, class1_op)
        
        class2_op = CreateClassOperation(
            uri=URIRef("http://example.org/test-ontology/Person"),
            label="Person",
            kind=Kind.SUBJECT
        )
        service.apply_edit_operation(ontology, class2_op)
        
        # Create relationship with references
        rel_op = CreateRelationshipOperation(
            uri=URIRef("http://example.org/test-ontology/owns"),
            label="owns",
            source_class_uri=URIRef("http://example.org/test-ontology/Person"),
            target_class_uri=URIRef("http://example.org/test-ontology/Vehicle"),
            definition="Ownership relationship",
            description="Person owns a vehicle",
            definition_references=["kb_doc_8_section_1", "kb_doc_8_section_2"],
            specification_references=["kb_doc_9_para_1"],
            references=["kb_doc_10_chapter_2"]
        )
        
        service.apply_edit_operation(ontology, rel_op)
        service.store_ontology(ontology)
        
        # Load and verify
        new_store = FilesystemOntologyStore(test_dir)
        new_service = OntologyService(new_store)
        loaded_ontology = new_service.load_ontology(ontology_uri)
        
        rel_uri = URIRef("http://example.org/test-ontology/owns")
        assert rel_uri in loaded_ontology.relationships
        
        rel = loaded_ontology.relationships[rel_uri]
        assert rel.label == "owns"
        assert rel.definition_references == ["kb_doc_8_section_1", "kb_doc_8_section_2"]
        assert rel.specification_references == ["kb_doc_9_para_1"]
        assert rel.references == ["kb_doc_10_chapter_2"]
        
        print("✓ Relationship references persistence test passed")
        
    finally:
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)


def test_update_operations_with_references():
    """Test that update operations can modify reference fields."""
    test_dir = tempfile.mkdtemp(prefix="test_ontology_refs_")
    
    try:
        store = FilesystemOntologyStore(test_dir)
        service = OntologyService(store)
        
        ontology_uri = "http://example.org/test-ontology"
        ontology = service.create_empty_ontology(
            ontology_uri=ontology_uri,
            label="Test Ontology",
            description="Test ontology for reference persistence"
        )
        
        # Create class with initial references
        create_op = CreateClassOperation(
            uri=URIRef("http://example.org/test-ontology/Vehicle"),
            label="Vehicle",
            kind=Kind.OBJECT,
            definition_references=["initial_ref_1"],
            specification_references=["initial_ref_2"],
            references=["initial_ref_3"]
        )
        service.apply_edit_operation(ontology, create_op)
        
        # Update with new references
        update_op = UpdateClassOperation(
            uri=URIRef("http://example.org/test-ontology/Vehicle"),
            definition_references=["updated_ref_1", "updated_ref_2"],
            specification_references=["updated_ref_3"],
            references=["updated_ref_4", "updated_ref_5", "updated_ref_6"]
        )
        service.apply_edit_operation(ontology, update_op)
        service.store_ontology(ontology)
        
        # Load and verify updates
        new_store = FilesystemOntologyStore(test_dir)
        new_service = OntologyService(new_store)
        loaded_ontology = new_service.load_ontology(ontology_uri)
        
        vehicle_uri = URIRef("http://example.org/test-ontology/Vehicle")
        vehicle = loaded_ontology.classes[vehicle_uri]
        
        assert vehicle.definition_references == ["updated_ref_1", "updated_ref_2"]
        assert vehicle.specification_references == ["updated_ref_3"]
        assert vehicle.references == ["updated_ref_4", "updated_ref_5", "updated_ref_6"]
        
        print("✓ Update operations with references test passed")
        
    finally:
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)


def test_empty_references_persistence():
    """Test that empty reference lists are handled correctly."""
    test_dir = tempfile.mkdtemp(prefix="test_ontology_refs_")
    
    try:
        store = FilesystemOntologyStore(test_dir)
        service = OntologyService(store)
        
        ontology_uri = "http://example.org/test-ontology"
        ontology = service.create_empty_ontology(
            ontology_uri=ontology_uri,
            label="Test Ontology",
            description="Test ontology for reference persistence"
        )
        
        # Create class without any references
        create_op = CreateClassOperation(
            uri=URIRef("http://example.org/test-ontology/Vehicle"),
            label="Vehicle",
            kind=Kind.OBJECT,
            definition="A means of transportation"
        )
        service.apply_edit_operation(ontology, create_op)
        service.store_ontology(ontology)
        
        # Load and verify empty lists
        new_store = FilesystemOntologyStore(test_dir)
        new_service = OntologyService(new_store)
        loaded_ontology = new_service.load_ontology(ontology_uri)
        
        vehicle_uri = URIRef("http://example.org/test-ontology/Vehicle")
        vehicle = loaded_ontology.classes[vehicle_uri]
        
        assert vehicle.definition_references == []
        assert vehicle.specification_references == []
        assert vehicle.references == []
        
        print("✓ Empty references persistence test passed")
        
    finally:
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)


if __name__ == "__main__":
    print("\n" + "="*70)
    print("Testing Ontology References Persistence")
    print("="*70 + "\n")
    
    test_class_references_persistence()
    test_attribute_references_persistence()
    test_relationship_references_persistence()
    test_update_operations_with_references()
    test_empty_references_persistence()
    
    print("\n" + "="*70)
    print("All tests passed! ✓")
    print("="*70 + "\n")
