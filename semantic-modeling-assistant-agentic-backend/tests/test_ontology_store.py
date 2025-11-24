#!/usr/bin/env python3
"""
Unit tests for FilesystemOntologyStore (ontology/store.py)

Covers two Ontology instances:
- simple ontology: minimal ontology with one class, one attribute, and one relationship
- complex ontology: multiple classes with inheritance, multiple attributes and relationships

Each scenario performs:
- store test: verify JSON structure written to disk
- load test: verify correct reconstruction of objects from JSON
"""

import os
import sys
import json
from pathlib import Path

# Ensure src/ is importable when running as a script
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from rdflib import URIRef

from ontology.store import FilesystemOntologyStore
from ontology.domain import Ontology, OntologyClass, OntologyAttribute, OntologyRelationship, Kind


# ------------------------
# Helper builders
# ------------------------
def build_simple_ontology() -> Ontology:
    """Build a simple ontology with one class, one attribute, and one self-relationship."""
    o_uri = URIRef("https://example.org/ontologies/simple")
    cls_uri = URIRef("https://example.org/ontologies/simple#SimpleClass")
    attr_uri = URIRef("https://example.org/ontologies/simple#simpleAttribute")
    rel_uri = URIRef("https://example.org/ontologies/simple#simpleRelationship")

    # Create class first
    simple_class = OntologyClass(
        uri=cls_uri,
        label="SimpleClass",
        kind=Kind.SUBJECT,
        definition="A simple class for testing",
        description="Simple class description",
        generalizations=[],
        specializations=[],
        attributes=[],
        outgoingRelationships=[],
        incomingRelationships=[],
    )
    
    # Create attribute owned by the class
    simple_attribute = OntologyAttribute(
        uri=attr_uri,
        label="simpleAttribute",
        definition="A simple attribute for testing",
        description="Simple attribute description",
        owningClass=simple_class,
    )
    
    # Create self-relationship
    simple_relationship = OntologyRelationship(
        uri=rel_uri,
        label="simpleRelationship",
        definition="A simple relationship for testing",
        description="Simple relationship description",
        sourceClass=simple_class,
        targetClass=simple_class,
    )
    
    # Wire back-references
    simple_class.attributes.append(simple_attribute)
    simple_class.outgoingRelationships.append(simple_relationship)
    simple_class.incomingRelationships.append(simple_relationship)

    return Ontology(
        uri=o_uri,
        label="Simple Ontology",
        description="A simple test ontology",
        classes={cls_uri: simple_class},
        attributes={attr_uri: simple_attribute},
        relationships={rel_uri: simple_relationship},
    )


def build_complex_ontology() -> Ontology:
    """Build a complex ontology with inheritance, multiple classes, attributes, and relationships."""
    o_uri = URIRef("https://transport.example.com/ontologies/vehicles/v1.0")
    
    # Class URIs
    person_uri = URIRef("https://transport.example.com/ontologies/vehicles/v1.0#Person")
    vehicle_uri = URIRef("https://transport.example.com/ontologies/vehicles/v1.0#Vehicle")
    car_uri = URIRef("https://transport.example.com/ontologies/vehicles/v1.0#Car")
    truck_uri = URIRef("https://transport.example.com/ontologies/vehicles/v1.0#Truck")
    
    # Attribute URIs
    name_attr_uri = URIRef("https://transport.example.com/ontologies/vehicles/v1.0#name")
    age_attr_uri = URIRef("https://transport.example.com/ontologies/vehicles/v1.0#age")
    vin_attr_uri = URIRef("https://transport.example.com/ontologies/vehicles/v1.0#vin")
    capacity_attr_uri = URIRef("https://transport.example.com/ontologies/vehicles/v1.0#capacity")
    
    # Relationship URIs
    owns_rel_uri = URIRef("https://transport.example.com/ontologies/vehicles/v1.0#owns")
    drives_rel_uri = URIRef("https://transport.example.com/ontologies/vehicles/v1.0#drives")

    # Create classes first (without relationships)
    person = OntologyClass(
        uri=person_uri,
        label="Person",
        kind=Kind.SUBJECT,
        definition="An individual human being",
        description="A person in the transportation domain",
        generalizations=[],
        specializations=[],
        attributes=[],
        outgoingRelationships=[],
        incomingRelationships=[],
    )
    
    vehicle = OntologyClass(
        uri=vehicle_uri,
        label="Vehicle",
        kind=Kind.OBJECT,
        definition="A means of transport",
        description="A vehicle for carrying people or goods",
        generalizations=[],
        specializations=[],
        attributes=[],
        outgoingRelationships=[],
        incomingRelationships=[],
    )
    
    car = OntologyClass(
        uri=car_uri,
        label="Car",
        kind=Kind.OBJECT,
        definition="A passenger vehicle",
        description="A road vehicle for passengers",
        generalizations=[vehicle],  # Car is a Vehicle
        specializations=[],
        attributes=[],
        outgoingRelationships=[],
        incomingRelationships=[],
    )
    
    truck = OntologyClass(
        uri=truck_uri,
        label="Truck",
        kind=Kind.OBJECT,
        definition="A cargo vehicle",
        description="A road vehicle for cargo",
        generalizations=[vehicle],  # Truck is a Vehicle
        specializations=[],
        attributes=[],
        outgoingRelationships=[],
        incomingRelationships=[],
    )
    
    # Set up inheritance relationships
    vehicle.specializations = [car, truck]
    
    # Create attributes
    name_attr = OntologyAttribute(
        uri=name_attr_uri,
        label="name",
        definition="A person's name",
        description="The full name of a person",
        owningClass=person,
    )
    
    age_attr = OntologyAttribute(
        uri=age_attr_uri,
        label="age",
        definition="A person's age",
        description="The age of a person in years",
        owningClass=person,
    )
    
    vin_attr = OntologyAttribute(
        uri=vin_attr_uri,
        label="vin",
        definition="Vehicle identification number",
        description="A unique identifier for a vehicle",
        owningClass=vehicle,
    )
    
    capacity_attr = OntologyAttribute(
        uri=capacity_attr_uri,
        label="capacity",
        definition="Cargo capacity",
        description="The maximum cargo capacity of a truck",
        owningClass=truck,
    )
    
    # Create relationships
    owns_rel = OntologyRelationship(
        uri=owns_rel_uri,
        label="owns",
        definition="Ownership relationship",
        description="A person owns a vehicle",
        sourceClass=person,
        targetClass=vehicle,
    )
    
    drives_rel = OntologyRelationship(
        uri=drives_rel_uri,
        label="drives",
        definition="Driving relationship",
        description="A person drives a vehicle",
        sourceClass=person,
        targetClass=vehicle,
    )
    
    # Wire back-references for attributes
    person.attributes = [name_attr, age_attr]
    vehicle.attributes = [vin_attr]
    truck.attributes = [capacity_attr]
    
    # Wire back-references for relationships
    person.outgoingRelationships = [owns_rel, drives_rel]
    vehicle.incomingRelationships = [owns_rel, drives_rel]

    return Ontology(
        uri=o_uri,
        label="Complex Transportation Ontology",
        description="A complex ontology for transportation domain testing",
        classes={
            person_uri: person,
            vehicle_uri: vehicle,
            car_uri: car,
            truck_uri: truck,
        },
        attributes={
            name_attr_uri: name_attr,
            age_attr_uri: age_attr,
            vin_attr_uri: vin_attr,
            capacity_attr_uri: capacity_attr,
        },
        relationships={
            owns_rel_uri: owns_rel,
            drives_rel_uri: drives_rel,
        },
    )


# ------------------------
# Assertion helpers
# ------------------------
def assert_simple_json_structure(json_data: dict):
    """Assert the JSON structure for simple ontology."""
    assert json_data["uri"] == "https://example.org/ontologies/simple"
    assert json_data["label"] == "Simple Ontology"
    assert json_data["description"] == "A simple test ontology"
    
    # Check classes
    assert "classes" in json_data
    classes = json_data["classes"]
    assert len(classes) == 1
    assert "https://example.org/ontologies/simple#SimpleClass" in classes
    
    simple_class = classes["https://example.org/ontologies/simple#SimpleClass"]
    assert simple_class["label"] == "SimpleClass"
    assert simple_class["definition"] == "A simple class for testing"
    assert len(simple_class["attributes"]) == 1
    assert len(simple_class["outgoingRelationships"]) == 1
    assert len(simple_class["incomingRelationships"]) == 1
    
    # Check attributes
    assert "attributes" in json_data
    attributes = json_data["attributes"]
    assert len(attributes) == 1
    assert "https://example.org/ontologies/simple#simpleAttribute" in attributes
    
    simple_attr = attributes["https://example.org/ontologies/simple#simpleAttribute"]
    assert simple_attr["label"] == "simpleAttribute"
    assert simple_attr["owningClass"] == "https://example.org/ontologies/simple#SimpleClass"
    
    # Check relationships
    assert "relationships" in json_data
    relationships = json_data["relationships"]
    assert len(relationships) == 1
    assert "https://example.org/ontologies/simple#simpleRelationship" in relationships
    
    simple_rel = relationships["https://example.org/ontologies/simple#simpleRelationship"]
    assert simple_rel["label"] == "simpleRelationship"
    assert simple_rel["sourceClass"] == "https://example.org/ontologies/simple#SimpleClass"
    assert simple_rel["targetClass"] == "https://example.org/ontologies/simple#SimpleClass"


def assert_simple_loaded(ontology: Ontology):
    """Assert the loaded simple ontology is correctly reconstructed."""
    assert str(ontology.uri) == "https://example.org/ontologies/simple"
    assert ontology.label == "Simple Ontology"
    assert ontology.description == "A simple test ontology"
    
    # Check classes
    assert len(ontology.classes) == 1
    simple_class = next(iter(ontology.classes.values()))
    assert simple_class.label == "SimpleClass"
    assert simple_class.definition == "A simple class for testing"
    assert len(simple_class.attributes) == 1
    assert len(simple_class.outgoingRelationships) == 1
    assert len(simple_class.incomingRelationships) == 1
    
    # Check attributes
    assert len(ontology.attributes) == 1
    simple_attr = next(iter(ontology.attributes.values()))
    assert simple_attr.label == "simpleAttribute"
    assert simple_attr.owningClass is simple_class
    
    # Check relationships
    assert len(ontology.relationships) == 1
    simple_rel = next(iter(ontology.relationships.values()))
    assert simple_rel.label == "simpleRelationship"
    assert simple_rel.sourceClass is simple_class
    assert simple_rel.targetClass is simple_class


def assert_complex_json_structure(json_data: dict):
    """Assert the JSON structure for complex ontology."""
    assert json_data["uri"] == "https://transport.example.com/ontologies/vehicles/v1.0"
    assert json_data["label"] == "Complex Transportation Ontology"
    
    # Check classes
    classes = json_data["classes"]
    assert len(classes) == 4
    expected_classes = [
        "https://transport.example.com/ontologies/vehicles/v1.0#Person", 
        "https://transport.example.com/ontologies/vehicles/v1.0#Vehicle",
        "https://transport.example.com/ontologies/vehicles/v1.0#Car", 
        "https://transport.example.com/ontologies/vehicles/v1.0#Truck"
    ]
    for class_uri in expected_classes:
        assert class_uri in classes
    
    # Check inheritance
    vehicle_class = classes["https://transport.example.com/ontologies/vehicles/v1.0#Vehicle"]
    car_class = classes["https://transport.example.com/ontologies/vehicles/v1.0#Car"]
    truck_class = classes["https://transport.example.com/ontologies/vehicles/v1.0#Truck"]
    
    assert "https://transport.example.com/ontologies/vehicles/v1.0#Car" in vehicle_class["specializations"]
    assert "https://transport.example.com/ontologies/vehicles/v1.0#Truck" in vehicle_class["specializations"]
    assert "https://transport.example.com/ontologies/vehicles/v1.0#Vehicle" in car_class["generalizations"]
    assert "https://transport.example.com/ontologies/vehicles/v1.0#Vehicle" in truck_class["generalizations"]
    
    # Check attributes
    attributes = json_data["attributes"]
    assert len(attributes) == 4
    expected_attrs = [
        "https://transport.example.com/ontologies/vehicles/v1.0#name", 
        "https://transport.example.com/ontologies/vehicles/v1.0#age",
        "https://transport.example.com/ontologies/vehicles/v1.0#vin", 
        "https://transport.example.com/ontologies/vehicles/v1.0#capacity"
    ]
    for attr_uri in expected_attrs:
        assert attr_uri in attributes
    
    # Check relationships
    relationships = json_data["relationships"]
    assert len(relationships) == 2
    expected_rels = [
        "https://transport.example.com/ontologies/vehicles/v1.0#owns", 
        "https://transport.example.com/ontologies/vehicles/v1.0#drives"
    ]
    for rel_uri in expected_rels:
        assert rel_uri in relationships


def assert_complex_loaded(ontology: Ontology):
    """Assert the loaded complex ontology is correctly reconstructed."""
    assert str(ontology.uri) == "https://transport.example.com/ontologies/vehicles/v1.0"
    assert ontology.label == "Complex Transportation Ontology"
    
    # Check classes and inheritance
    assert len(ontology.classes) == 4
    
    person_uri = URIRef("https://transport.example.com/ontologies/vehicles/v1.0#Person")
    vehicle_uri = URIRef("https://transport.example.com/ontologies/vehicles/v1.0#Vehicle")
    car_uri = URIRef("https://transport.example.com/ontologies/vehicles/v1.0#Car")
    truck_uri = URIRef("https://transport.example.com/ontologies/vehicles/v1.0#Truck")
    
    person = ontology.classes[person_uri]
    vehicle = ontology.classes[vehicle_uri]
    car = ontology.classes[car_uri]
    truck = ontology.classes[truck_uri]
    
    # Check inheritance relationships
    assert vehicle in car.generalizations
    assert vehicle in truck.generalizations
    assert car in vehicle.specializations
    assert truck in vehicle.specializations
    
    # Check attributes are correctly linked
    assert len(ontology.attributes) == 4
    assert len(person.attributes) == 2  # name, age
    assert len(vehicle.attributes) == 1  # vin
    assert len(truck.attributes) == 1   # capacity
    
    # Check relationships are correctly linked
    assert len(ontology.relationships) == 2
    assert len(person.outgoingRelationships) == 2  # owns, drives
    assert len(vehicle.incomingRelationships) == 2  # owns, drives


# ------------------------
# Tests: simple ontology
# ------------------------
def test_store_simple_ontology():
    """Test storing a simple ontology to filesystem."""
    store = FilesystemOntologyStore(base_dir="data_test/ontologies")
    ontology = build_simple_ontology()

    # As per store contract: ontology must be previously loaded (present in store cache)
    store.ontologies[ontology.uri] = ontology
    store.store_ontology(ontology)

    safe_dirname = store._uri_to_safe_dirname(str(ontology.uri))
    ontology_dir = Path(store.base_dir) / safe_dirname
    ontology_file = ontology_dir / "ontology.json"
    assert ontology_file.exists(), f"ontology.json should be created at {ontology_file}"

    data = json.loads(ontology_file.read_text(encoding="utf-8"))
    assert_simple_json_structure(data)


def test_load_simple_ontology():
    """Test loading a simple ontology from filesystem."""
    store = FilesystemOntologyStore(base_dir="data_test/ontologies")
    ontology = build_simple_ontology()

    # Persist first to create the JSON
    store.ontologies[ontology.uri] = ontology
    store.store_ontology(ontology)

    loaded = store.load_ontology(str(ontology.uri))
    assert_simple_loaded(loaded)


# ------------------------
# Tests: complex ontology
# ------------------------
def test_store_complex_ontology():
    """Test storing a complex ontology to filesystem."""
    store = FilesystemOntologyStore(base_dir="data_test/ontologies")
    ontology = build_complex_ontology()

    store.ontologies[ontology.uri] = ontology
    store.store_ontology(ontology)

    safe_dirname = store._uri_to_safe_dirname(str(ontology.uri))
    ontology_dir = Path(store.base_dir) / safe_dirname
    ontology_file = ontology_dir / "ontology.json"
    assert ontology_file.exists(), f"ontology.json should be created at {ontology_file}"

    data = json.loads(ontology_file.read_text(encoding="utf-8"))
    assert_complex_json_structure(data)


def test_load_complex_ontology():
    """Test loading a complex ontology from filesystem."""
    store = FilesystemOntologyStore(base_dir="data_test/ontologies")
    ontology = build_complex_ontology()

    store.ontologies[ontology.uri] = ontology
    store.store_ontology(ontology)

    loaded = store.load_ontology(str(ontology.uri))
    assert_complex_loaded(loaded)


# ------------------------
# Tests: URI to directory name conversion
# ------------------------
def test_uri_to_safe_dirname():
    """Test URI to filesystem-safe directory name conversion."""
    store = FilesystemOntologyStore(base_dir="data_test/ontologies")
    
    # Test normal HTTP URL
    assert store._uri_to_safe_dirname("https://example.org/ontology") == "example.org_ontology"
    
    # Test URL with special characters (= is now replaced)
    assert store._uri_to_safe_dirname("https://example.org/onto:special?param=value#fragment") == "example.org_onto_special_param_value_fragment"
    
    # Test URL with spaces
    assert store._uri_to_safe_dirname("https://example.org/onto special") == "example.org_onto_special"
    
    # Test very long URL
    long_url = "https://very-long-domain-name.example.com/path/to/very/long/ontology/name/with/many/segments/that/exceed/normal/length"
    safe_name = store._uri_to_safe_dirname(long_url)
    assert len(safe_name) <= 97  # 80 chars + "_" + 16 char hash
    assert safe_name.startswith("very-long-domain-name.example.com_path_to_very_long_ontology_name_with_many_segm")
    assert safe_name.endswith("15e0e76c6174624c")  # hash of the full URL
    
    # Test empty or None
    assert store._uri_to_safe_dirname("") == "unnamed"
    assert store._uri_to_safe_dirname(None) == "unnamed"


# ------------------------
# Tests: error conditions
# ------------------------
def test_store_ontology_not_in_cache():
    """Test that storing an ontology not in cache raises ValueError."""
    store = FilesystemOntologyStore(base_dir="data_test/ontologies")
    ontology = build_simple_ontology()

    # Don't add to cache - should raise ValueError
    try:
        store.store_ontology(ontology)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "not found in the store" in str(e)


def test_load_nonexistent_ontology():
    """Test that loading a non-existent ontology raises FileNotFoundError."""
    store = FilesystemOntologyStore(base_dir="data_test/ontologies")
    
    try:
        store.load_ontology("https://example.org/nonexistent")
        assert False, "Should have raised FileNotFoundError"
    except FileNotFoundError as e:
        assert "Ontology file not found" in str(e)


if __name__ == "__main__":
    # Allow running this test as a standalone script
    print("Running FilesystemOntologyStore tests...\n")
    try:
        test_store_simple_ontology()
        print("✓ test_store_simple_ontology passed")
        test_load_simple_ontology()
        print("✓ test_load_simple_ontology passed")
        test_store_complex_ontology()
        print("✓ test_store_complex_ontology passed")
        test_load_complex_ontology()
        print("✓ test_load_complex_ontology passed")
        print("Running URI test...")
        test_uri_to_safe_dirname()
        print("✓ test_uri_to_safe_dirname passed")
        print("Running error tests...")
        test_store_ontology_not_in_cache()
        print("✓ test_store_ontology_not_in_cache passed")
        test_load_nonexistent_ontology()
        print("✓ test_load_nonexistent_ontology passed")
        print("\nAll tests passed!")
    except AssertionError as e:
        print(f"Assertion failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
