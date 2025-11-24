"""
Unit tests for OntologyEditOperation <-> OntologyOperationModel conversion.

Tests the round-trip conversion between domain operations and API models.
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from rdflib import URIRef
from ontology.edit_operations import (
    CreateClassOperation, UpdateClassOperation, DeleteClassOperation,
    CreateAttributeOperation, UpdateAttributeOperation, DeleteAttributeOperation,
    CreateRelationshipOperation, UpdateRelationshipOperation, DeleteRelationshipOperation,
    OperationType
)
from ontology.domain import Kind
from api.controllers.design_project_controller import (
    _convert_operation_to_model,
    _convert_model_to_operation
)


def test_create_class_operation_round_trip():
    """Test round-trip conversion for CreateClassOperation."""
    print("\n=== Testing CreateClassOperation Round-Trip ===")
    
    # Create a domain operation
    original_op = CreateClassOperation(
        uri=URIRef("http://example.org/ontology/Person"),
        label="Person",
        kind=Kind.SUBJECT,
        definition="A human being",
        description="Represents a person in the domain",
        generalization_uris=[URIRef("http://example.org/ontology/Agent")],
        definition_references=["Section 1.2"],
        specification_references=["Spec A"],
        references=["Doc 1"]
    )
    
    # Convert to API model
    model = _convert_operation_to_model(original_op)
    
    print(f"Original operation: {original_op}")
    print(f"Converted to model: {model.model_dump()}")
    
    # Convert back to domain operation
    converted_op = _convert_model_to_operation(model)
    
    print(f"Converted back to operation: {converted_op}")
    
    # Verify they are equal
    assert original_op == converted_op, "Round-trip conversion failed for CreateClassOperation"
    print("✓ Round-trip successful!")


def test_update_attribute_operation_round_trip():
    """Test round-trip conversion for UpdateAttributeOperation."""
    print("\n=== Testing UpdateAttributeOperation Round-Trip ===")
    
    original_op = UpdateAttributeOperation(
        uri=URIRef("http://example.org/ontology/age"),
        label="Age",
        owning_class_uri=URIRef("http://example.org/ontology/Person"),
        definition="The age of a person",
        description="Age in years",
        definition_references=["Section 2.1"],
        specification_references=["Spec B"],
        references=["Doc 2"]
    )
    
    model = _convert_operation_to_model(original_op)
    print(f"Original operation: {original_op}")
    print(f"Converted to model: {model.model_dump()}")
    
    converted_op = _convert_model_to_operation(model)
    print(f"Converted back to operation: {converted_op}")
    
    assert original_op == converted_op, "Round-trip conversion failed for UpdateAttributeOperation"
    print("✓ Round-trip successful!")


def test_create_relationship_operation_round_trip():
    """Test round-trip conversion for CreateRelationshipOperation."""
    print("\n=== Testing CreateRelationshipOperation Round-Trip ===")
    
    original_op = CreateRelationshipOperation(
        uri=URIRef("http://example.org/ontology/worksFor"),
        label="works for",
        source_class_uri=URIRef("http://example.org/ontology/Person"),
        target_class_uri=URIRef("http://example.org/ontology/Organization"),
        definition="Employment relationship",
        description="Indicates that a person works for an organization",
        definition_references=["Section 3.1"],
        specification_references=["Spec C"],
        references=["Doc 3"]
    )
    
    model = _convert_operation_to_model(original_op)
    print(f"Original operation: {original_op}")
    print(f"Converted to model: {model.model_dump()}")
    
    converted_op = _convert_model_to_operation(model)
    print(f"Converted back to operation: {converted_op}")
    
    assert original_op == converted_op, "Round-trip conversion failed for CreateRelationshipOperation"
    print("✓ Round-trip successful!")


def test_delete_class_operation_round_trip():
    """Test round-trip conversion for DeleteClassOperation."""
    print("\n=== Testing DeleteClassOperation Round-Trip ===")
    
    original_op = DeleteClassOperation(
        uri=URIRef("http://example.org/ontology/ObsoleteClass")
    )
    
    model = _convert_operation_to_model(original_op)
    print(f"Original operation: {original_op}")
    print(f"Converted to model: {model.model_dump()}")
    
    converted_op = _convert_model_to_operation(model)
    print(f"Converted back to operation: {converted_op}")
    
    assert original_op == converted_op, "Round-trip conversion failed for DeleteClassOperation"
    print("✓ Round-trip successful!")


def test_minimal_create_class_operation():
    """Test round-trip with minimal fields (only required ones)."""
    print("\n=== Testing Minimal CreateClassOperation ===")
    
    original_op = CreateClassOperation(
        uri=URIRef("http://example.org/ontology/Thing"),
        label="Thing"
    )
    
    model = _convert_operation_to_model(original_op)
    print(f"Original operation: {original_op}")
    print(f"Converted to model: {model.model_dump()}")
    
    converted_op = _convert_model_to_operation(model)
    print(f"Converted back to operation: {converted_op}")
    
    assert original_op == converted_op, "Round-trip conversion failed for minimal CreateClassOperation"
    print("✓ Round-trip successful!")


if __name__ == "__main__":
    print("Testing OntologyEditOperation <-> OntologyOperationModel conversion")
    print("=" * 70)
    
    try:
        test_create_class_operation_round_trip()
        test_update_attribute_operation_round_trip()
        test_create_relationship_operation_round_trip()
        test_delete_class_operation_round_trip()
        test_minimal_create_class_operation()
        
        print("\n" + "=" * 70)
        print("✓ All tests passed!")
        print("=" * 70)
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
