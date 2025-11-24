"""
Unit tests for the ontology service module.
"""

import os
import tempfile
import shutil
from rdflib import URIRef

# Add the src directory to Python path to import our modules
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from ontology.service import OntologyService
from ontology.store import FilesystemOntologyStore
from ontology.domain import Ontology


def test_ontology_service_basic_operations():
    """Test basic ontology service operations."""
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Initialize service with a store pointing to temp directory
        store = FilesystemOntologyStore(base_dir=temp_dir)
        service = OntologyService(store)
        
        # Test creating a new empty ontology
        test_uri = "http://test.example.org/ontology"
        test_label = "Test Ontology"
        test_description = "A test ontology for unit testing"
        
        ontology = service.create_empty_ontology(test_uri, test_label, test_description)
        
        # Verify the created ontology
        assert ontology.uri == URIRef(test_uri)
        assert ontology.label == test_label
        assert ontology.description == test_description
        assert len(ontology.classes) == 0
        assert len(ontology.attributes) == 0
        assert len(ontology.relationships) == 0
        
        # Test storing the ontology
        service.store_ontology(ontology)
        
        # Test checking if ontology exists
        assert service.ontology_exists(test_uri) == True
        assert service.ontology_exists("http://non-existent.org/ontology") == False
        
        # Test loading the ontology
        loaded_ontology = service.load_ontology(test_uri)
        
        # Verify loaded ontology matches original
        assert loaded_ontology.uri == ontology.uri
        assert loaded_ontology.label == ontology.label
        assert loaded_ontology.description == ontology.description
        assert len(loaded_ontology.classes) == len(ontology.classes)
        assert len(loaded_ontology.attributes) == len(ontology.attributes)
        assert len(loaded_ontology.relationships) == len(ontology.relationships)
        
        print("✓ Basic ontology service operations test passed")


def test_ontology_service_error_handling():
    """Test error handling in ontology service."""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        store = FilesystemOntologyStore(base_dir=temp_dir)
        service = OntologyService(store)
        
        # Test loading non-existent ontology
        try:
            service.load_ontology("http://non-existent.org/ontology")
            assert False, "Should have raised FileNotFoundError"
        except FileNotFoundError:
            pass  # Expected
        
        # Test invalid URI validation
        try:
            service.load_ontology("")
            assert False, "Should have raised ValueError for empty URI"
        except ValueError:
            pass  # Expected
        
        try:
            service.load_ontology("   ")
            assert False, "Should have raised ValueError for whitespace URI"
        except ValueError:
            pass  # Expected
        
        # Test storing None ontology
        try:
            service.store_ontology(None)
            assert False, "Should have raised ValueError for None ontology"
        except ValueError:
            pass  # Expected
        
        # Test creating ontology with invalid parameters
        try:
            service.create_empty_ontology("", "Test")
            assert False, "Should have raised ValueError for empty URI"
        except ValueError:
            pass  # Expected
        
        try:
            service.create_empty_ontology("http://test.org", "")
            assert False, "Should have raised ValueError for empty label"
        except ValueError:
            pass  # Expected
        
        print("✓ Error handling test passed")


def test_ontology_service_with_existing_ontology():
    """Test service operations with existing ontology data."""
    
    # Use the test data directory
    store = FilesystemOntologyStore(base_dir="data_test/ontologies")
    service = OntologyService(store)
    
    # Test loading existing ontology
    existing_uri = "http://example.org/onto"
    
    if service.ontology_exists(existing_uri):
        ontology = service.load_ontology(existing_uri)
        
        # Verify the loaded ontology has expected structure
        assert ontology.uri == URIRef(existing_uri)
        assert ontology.label == "Simple Ontology"
        assert ontology.description == "A simple test ontology"
        
        # Check that it has the expected elements
        assert len(ontology.classes) > 0
        assert len(ontology.attributes) > 0
        assert len(ontology.relationships) > 0
        
        print("✓ Existing ontology test passed")
    else:
        print("! Skipping existing ontology test - no test data found")


if __name__ == "__main__":
    test_ontology_service_basic_operations()
    test_ontology_service_error_handling()
    test_ontology_service_with_existing_ontology()
    print("\nAll ontology service tests passed! ✓")
