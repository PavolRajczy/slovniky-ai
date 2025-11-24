"""
Test to verify that the custom __repr__ methods prevent deep recursion
and that the performance fixes work correctly.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.ontology.domain import Ontology, OntologyClass, OntologyAttribute, OntologyRelationship, Kind
from rdflib import URIRef


def test_repr_no_deep_recursion():
    """Test that __repr__ doesn't cause infinite recursion with circular references."""
    
    # Create two classes with circular generalization relationship
    class1 = OntologyClass(
        uri=URIRef("http://example.org/Class1"),
        label="Class 1",
        definition="First class",
        description="A test class",
        kind=Kind.SUBJECT
    )
    
    class2 = OntologyClass(
        uri=URIRef("http://example.org/Class2"),
        label="Class 2",
        definition="Second class",
        description="Another test class",
        kind=Kind.OBJECT
    )
    
    # Create circular reference
    class1.generalizations.append(class2)
    class2.specializations.append(class1)
    
    # Create a relationship between them
    rel = OntologyRelationship(
        uri=URIRef("http://example.org/Relationship1"),
        label="has part",
        definition="A part-of relationship",
        description="Connects two classes",
        sourceClass=class1,
        targetClass=class2
    )
    
    class1.outgoingRelationships.append(rel)
    class2.incomingRelationships.append(rel)
    
    # Create an attribute
    attr = OntologyAttribute(
        uri=URIRef("http://example.org/Attribute1"),
        label="name",
        definition="The name attribute",
        description="A simple string attribute",
        owningClass=class1
    )
    
    class1.attributes.append(attr)
    
    # Test that repr() works without hanging or recursion error
    print("Testing repr() methods...")
    
    class1_repr = repr(class1)
    print(f"Class1 repr: {class1_repr}")
    assert "OntologyClass" in class1_repr
    assert "generalizations=1" in class1_repr
    assert "specializations=0" in class1_repr
    assert "attributes=1" in class1_repr
    assert "outgoingRels=1" in class1_repr
    
    class2_repr = repr(class2)
    print(f"Class2 repr: {class2_repr}")
    assert "OntologyClass" in class2_repr
    assert "generalizations=0" in class2_repr
    assert "specializations=1" in class2_repr
    
    rel_repr = repr(rel)
    print(f"Relationship repr: {rel_repr}")
    assert "OntologyRelationship" in rel_repr
    assert "http://example.org/Class1" in rel_repr
    assert "http://example.org/Class2" in rel_repr
    
    attr_repr = repr(attr)
    print(f"Attribute repr: {attr_repr}")
    assert "OntologyAttribute" in attr_repr
    assert "http://example.org/Class1" in attr_repr
    
    # Create an ontology with these objects
    ontology = Ontology(
        uri=URIRef("http://example.org/TestOntology"),
        label="Test Ontology",
        description="A test ontology"
    )
    ontology.classes[class1.uri] = class1
    ontology.classes[class2.uri] = class2
    ontology.relationships[rel.uri] = rel
    ontology.attributes[attr.uri] = attr
    
    ont_repr = repr(ontology)
    print(f"Ontology repr: {ont_repr}")
    assert "Ontology" in ont_repr
    assert "classes=2" in ont_repr
    assert "attributes=1" in ont_repr
    assert "relationships=1" in ont_repr
    
    print("\n✓ All repr() tests passed - no deep recursion!")


def test_equality_excludes_collections():
    """Test that equality comparison excludes list/dict fields."""
    
    class1 = OntologyClass(
        uri=URIRef("http://example.org/Class1"),
        label="Class 1",
        definition="First class",
        description="A test class",
        kind=Kind.SUBJECT
    )
    
    class2 = OntologyClass(
        uri=URIRef("http://example.org/Class1"),  # Same URI
        label="Class 1",  # Same label
        definition="First class",  # Same definition
        description="A test class",  # Same description
        kind=Kind.SUBJECT  # Same kind
    )
    
    # Add different relationships to each
    rel1 = OntologyRelationship(
        uri=URIRef("http://example.org/Rel1"),
        label="rel1",
        definition=None,
        description=None,
        sourceClass=class1,
        targetClass=class1
    )
    
    class1.outgoingRelationships.append(rel1)
    # class2 has no relationships
    
    # They should still be equal because collections are excluded from comparison
    print("Testing equality with different collections...")
    assert class1 == class2, "Classes should be equal despite different relationships"
    print("✓ Equality test passed - collections excluded from comparison!")


if __name__ == "__main__":
    test_repr_no_deep_recursion()
    print()
    test_equality_excludes_collections()
    print("\n✓✓✓ All tests passed!")
