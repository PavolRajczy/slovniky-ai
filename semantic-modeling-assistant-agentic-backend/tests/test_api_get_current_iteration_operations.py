"""
Unit tests for the GET /projects/{project_id}/iterations/{iteration_id}/operations endpoint.

This test verifies that we can retrieve prepared operations for an iteration
without re-generating them, which is essential when the client reloads after prepare
but before applying the operations.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import unittest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from rdflib import URIRef

from design_project.domain import (
    DesignProject, DesignIteration, DesignIterationStatus,
    KnowledgeDomain, KnowledgeDomainArea, DesignTaskPattern, DesignTaskCategory
)
from ontology.domain import Ontology
from ontology.edit_operations import CreateClassOperation, Kind

# Import the router
from api.controllers.design_project_controller import router
from fastapi import FastAPI

app = FastAPI()
app.include_router(router)
client = TestClient(app)


class TestGetIterationOperations(unittest.TestCase):
    """Test cases for retrieving iteration operations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.project_id = "test-project-123"
        self.iteration_id = "test-iteration-456"
        
        # Create a mock ontology
        self.mock_ontology = Ontology(
            uri=URIRef("http://example.org/ontology"),
            label="Test Ontology",
            description="A test ontology for unit tests"
        )
        
        # Create a mock knowledge domain with an area
        self.mock_area = KnowledgeDomainArea(
            id="area-1",
            label="Test Area",
            description="Test area description",
            parent=None,  # Will be set when creating domain
            keyConcepts=["concept1", "concept2"],
            modelingClasses=[],
            modelingAttributes=[],
            modelingRelationships=[],
            explainingKnowledgeResources=[]
        )
        
        self.mock_domain = KnowledgeDomain(
            label="Test Domain",
            description="Test domain description",
            areas=[self.mock_area]
        )
        
        self.mock_area.parent = self.mock_domain
        
        # Create mock prepared operations
        self.mock_operations = [
            CreateClassOperation(
                uri=URIRef("http://example.org/Class1"),
                label="Class 1",
                kind=Kind.OBJECT,
                definition="A test class",
                description="Test class description"
            ),
            CreateClassOperation(
                uri=URIRef("http://example.org/Class2"),
                label="Class 2",
                kind=Kind.SUBJECT,
                definition="Another test class",
                description="Another test class description"
            )
        ]
    
    @patch('api.controllers.design_project_controller.design_project_service')
    def test_get_operations_success(self, mock_service):
        """Test successfully retrieving prepared operations for current iteration."""
        # Create a current iteration with prepared operations
        current_iteration = DesignIteration(
            id=self.iteration_id,
            name="Test Iteration",
            status=DesignIterationStatus.OPERATIONS_GENERATED,
            specification="Test iteration specification",
            finishedTasks=[],
            currentTask=None,
            plannedTasks=[],
            focusedArea=self.mock_area,
            plannedOperations=self.mock_operations,  # Operations are already prepared
            designedOntologyChangesSpecification=None
        )
        
        # Create a mock project with current iteration
        mock_project = DesignProject(
            id=self.project_id,
            name="Test Project",
            finishedIterations=[],
            currentIteration=current_iteration,
            plannedIterations=[],
            patterns=[],
            patternsFactoryId="default",
            legalKnowledgeBase=[],
            expertKnowledgeBase=[],
            keyKnowledgeDocument=None,
            modeledKnowledgeDomain=self.mock_domain,
            designedOntology=self.mock_ontology
        )
        
        # Mock the service to return the project
        mock_service.load_project.return_value = mock_project
        
        # Call the endpoint with iteration_id in URL
        response = client.get(f"/projects/{self.project_id}/iterations/{self.iteration_id}/operations")
        
        # Verify response
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data["iteration_id"], self.iteration_id)
        self.assertEqual(data["status"], "prepared")
        self.assertEqual(len(data["operations"]), 2)
        
        # Verify operations content
        self.assertEqual(data["operations"][0]["operation_type"], "create")
        self.assertEqual(data["operations"][0]["target_type"], "class")
        self.assertEqual(data["operations"][0]["label"], "Class 1")
        
        self.assertEqual(data["operations"][1]["operation_type"], "create")
        self.assertEqual(data["operations"][1]["target_type"], "class")
        self.assertEqual(data["operations"][1]["label"], "Class 2")
    
    @patch('api.controllers.design_project_controller.design_project_service')
    def test_get_operations_no_current_iteration(self, mock_service):
        """Test error when the iteration is not the current iteration."""
        # Create a mock project without current iteration
        mock_project = DesignProject(
            id=self.project_id,
            name="Test Project",
            finishedIterations=[],
            currentIteration=None,  # No current iteration
            plannedIterations=[],
            patterns=[],
            patternsFactoryId="default",
            legalKnowledgeBase=[],
            expertKnowledgeBase=[],
            keyKnowledgeDocument=None,
            modeledKnowledgeDomain=self.mock_domain,
            designedOntology=self.mock_ontology
        )
        
        # Mock the service to return the project
        mock_service.load_project.return_value = mock_project
        
        # Call the endpoint
        response = client.get(f"/projects/{self.project_id}/iterations/{self.iteration_id}/operations")
        
        # Verify error response
        self.assertEqual(response.status_code, 409)
        self.assertIn("is not the current iteration", response.json()["detail"])
    
    @patch('api.controllers.design_project_controller.design_project_service')
    def test_get_operations_no_prepared_operations(self, mock_service):
        """Test error when current iteration has no prepared operations."""
        # Create a current iteration without prepared operations
        current_iteration = DesignIteration(
            id=self.iteration_id,
            name="Test Iteration",
            status=DesignIterationStatus.PLANNED,  # Not in prepared state
            specification="Test iteration specification",
            finishedTasks=[],
            currentTask=None,
            plannedTasks=[],
            focusedArea=self.mock_area,
            plannedOperations=None,  # No operations prepared
            designedOntologyChangesSpecification=None
        )
        
        # Create a mock project with current iteration
        mock_project = DesignProject(
            id=self.project_id,
            name="Test Project",
            finishedIterations=[],
            currentIteration=current_iteration,
            plannedIterations=[],
            patterns=[],
            patternsFactoryId="default",
            legalKnowledgeBase=[],
            expertKnowledgeBase=[],
            keyKnowledgeDocument=None,
            modeledKnowledgeDomain=self.mock_domain,
            designedOntology=self.mock_ontology
        )
        
        # Mock the service to return the project
        mock_service.load_project.return_value = mock_project
        
        # Call the endpoint
        response = client.get(f"/projects/{self.project_id}/iterations/{self.iteration_id}/operations")
        
        # Verify error response
        self.assertEqual(response.status_code, 409)
        self.assertIn("has no prepared operations", response.json()["detail"])
    
    @patch('api.controllers.design_project_controller.design_project_service')
    def test_get_operations_project_not_found(self, mock_service):
        """Test error when project is not found."""
        # Mock the service to raise FileNotFoundError
        mock_service.load_project.side_effect = FileNotFoundError("Project not found")
        
        # Call the endpoint
        response = client.get(f"/projects/{self.project_id}/iterations/{self.iteration_id}/operations")
        
        # Verify error response
        self.assertEqual(response.status_code, 404)
        self.assertIn("not found", response.json()["detail"])
    
    @patch('api.controllers.design_project_controller.design_project_service')
    def test_get_operations_wrong_iteration_id(self, mock_service):
        """Test error when requesting operations for a non-current iteration."""
        # Create a current iteration with different ID
        current_iteration = DesignIteration(
            id="different-iteration-id",
            name="Current Iteration",
            status=DesignIterationStatus.OPERATIONS_GENERATED,
            specification="Current iteration specification",
            finishedTasks=[],
            currentTask=None,
            plannedTasks=[],
            focusedArea=self.mock_area,
            plannedOperations=self.mock_operations,
            designedOntologyChangesSpecification=None
        )
        
        # Create a mock project
        mock_project = DesignProject(
            id=self.project_id,
            name="Test Project",
            finishedIterations=[],
            currentIteration=current_iteration,
            plannedIterations=[],
            patterns=[],
            patternsFactoryId="default",
            legalKnowledgeBase=[],
            expertKnowledgeBase=[],
            keyKnowledgeDocument=None,
            modeledKnowledgeDomain=self.mock_domain,
            designedOntology=self.mock_ontology
        )
        
        # Mock the service to return the project
        mock_service.load_project.return_value = mock_project
        
        # Call the endpoint with wrong iteration ID
        response = client.get(f"/projects/{self.project_id}/iterations/{self.iteration_id}/operations")
        
        # Verify error response
        self.assertEqual(response.status_code, 409)
        self.assertIn("is not the current iteration", response.json()["detail"])
    
    @patch('api.controllers.design_project_controller.design_project_service')
    def test_status_mapping(self, mock_service):
        """Test that different iteration statuses are correctly mapped to API status."""
        test_cases = [
            (DesignIterationStatus.OPERATIONS_GENERATED, "prepared"),
            (DesignIterationStatus.GENERATING_OPERATIONS, "generating"),
            (DesignIterationStatus.APPLYING_OPERATIONS, "applying"),
        ]
        
        for domain_status, expected_api_status in test_cases:
            with self.subTest(domain_status=domain_status):
                # Create a current iteration with the test status
                current_iteration = DesignIteration(
                    id=self.iteration_id,
                    name="Test Iteration",
                    status=domain_status,
                    specification="Test iteration specification",
                    finishedTasks=[],
                    currentTask=None,
                    plannedTasks=[],
                    focusedArea=self.mock_area,
                    plannedOperations=self.mock_operations,
                    designedOntologyChangesSpecification=None
                )
                
                # Create a mock project with current iteration
                mock_project = DesignProject(
                    id=self.project_id,
                    name="Test Project",
                    finishedIterations=[],
                    currentIteration=current_iteration,
                    plannedIterations=[],
                    patterns=[],
                    patternsFactoryId="default",
                    legalKnowledgeBase=[],
                    expertKnowledgeBase=[],
                    keyKnowledgeDocument=None,
                    modeledKnowledgeDomain=self.mock_domain,
                    designedOntology=self.mock_ontology
                )
                
                # Mock the service to return the project
                mock_service.load_project.return_value = mock_project
                
                # Call the endpoint
                response = client.get(f"/projects/{self.project_id}/iterations/{self.iteration_id}/operations")
                
                # Verify status mapping
                self.assertEqual(response.status_code, 200)
                data = response.json()
                self.assertEqual(data["status"], expected_api_status)


if __name__ == "__main__":
    # Run the tests
    unittest.main()
