"""
Unit tests for the ModelerAgent_Simple_OpenAI implementation.
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock
from rdflib import URIRef

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from agents.modelers.modeler_openai_basic import ModelerAgent_Simple_OpenAI
from design_project.domain import (
    DesignProject, DesignIteration, DesignTask, DesignTaskPattern, 
    DesignTaskCategory, DesignTaskStatus, KnowledgeDomainArea, KnowledgeDomain
)
from ontology.domain import Ontology
from ontology.edit_operations import CreateClassOperation, CreateAttributeOperation, CreateRelationshipOperation


class TestModelerAgent_Simple_OpenAI(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        self.knowledge_base_service = Mock()
        self.knowledge_base_index_service = Mock()
        
        # Create a modeler agent (without OpenAI key for testing)
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            self.agent = ModelerAgent_Simple_OpenAI(
                self.knowledge_base_service, 
                self.knowledge_base_index_service,
                "gpt-4o"
            )
        
        # Create test ontology
        self.test_ontology = Ontology(
            uri=URIRef("http://example.org/test-ontology"),
            label="Test Ontology",
            description="A test ontology for unit testing",
            classes={},
            attributes={},
            relationships={}
        )
        
        # Create test knowledge domain and area
        self.test_domain = KnowledgeDomain(
            label="Test Domain",
            description="A test knowledge domain",
            areas=[]
        )
        
        self.test_area = KnowledgeDomainArea(
            id="test-area-1",
            label="Test Area",
            description="A test knowledge domain area",
            parent=self.test_domain,
            keyConcepts=["concept1", "concept2"],
            modelingClasses=[],
            modelingAttributes=[],
            modelingRelationships=[],
            explainingKnowledgeResources=[]
        )
        
        # Create test design project
        self.test_project = DesignProject(
            id="test-project",
            name="Test Project",
            finishedIterations=[],
            currentIteration=None,
            plannedIterations=[],
            patterns=[],
            patternsFactoryId="basic",
            legalKnowledgeBase=[],
            expertKnowledgeBase=[],
            keyKnowledgeDocument=None,
            modeledKnowledgeDomain=self.test_domain,
            designedOntology=self.test_ontology
        )
        
        # Create test iteration
        self.test_iteration = DesignIteration(
            id="test-iteration",
            name="Test Iteration",
            status="in_progress",
            specification="Test iteration specification",
            finishedTasks=[],
            currentTask=None,
            plannedTasks=[],
            focusedArea=self.test_area,
            designedOntologyChangesSpecification=None
        )
        
        # Create test task pattern
        self.test_pattern = DesignTaskPattern(
            id="test-pattern",
            name="Test Pattern",
            category=DesignTaskCategory.CLASS,
            specification="Test pattern specification",
            whenApplicable="When testing",
            exampleTasks=[]
        )
        
        # Create test task
        self.test_task = DesignTask(
            id="test-task",
            name="Test Task",
            status=DesignTaskStatus.PLANNED,
            followedPattern=self.test_pattern,
            specification="Test task specification",
            knowledgeResources=[],
            designedOntologyChangesSpecification=None
        )

    def test_initialization(self):
        """Test that the agent initializes correctly."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            agent = ModelerAgent_Simple_OpenAI(
                self.knowledge_base_service, 
                self.knowledge_base_index_service
            )
            
            self.assertEqual(agent.knowledge_base_service, self.knowledge_base_service)
            self.assertEqual(agent.knowledge_base_index_service, self.knowledge_base_index_service)
            self.assertEqual(agent.model_name, "gpt-4o")
    
    def test_initialization_missing_api_key(self):
        """Test that initialization fails without OpenAI API key."""
        with patch.dict('os.environ', {}, clear=True):
            with self.assertRaises(ValueError) as context:
                ModelerAgent_Simple_OpenAI(
                    self.knowledge_base_service, 
                    self.knowledge_base_index_service
                )
            
            self.assertIn("OPENAI_API_KEY", str(context.exception))
    
    def test_prefix_uri_ontology_namespace(self):
        """Test URI prefixing with ontology namespace."""
        ontology_uri = URIRef("http://example.org/ontology")
        element_uri = URIRef("http://example.org/ontology#TestClass")
        
        result = self.agent._prefix_uri(element_uri, ontology_uri)
        self.assertEqual(result, "onto:TestClass")
    
    def test_prefix_uri_external_namespace(self):
        """Test URI prefixing with external namespaces."""
        ontology_uri = URIRef("http://example.org/ontology")
        
        # Test RDF namespace
        rdf_uri = URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
        result = self.agent._prefix_uri(rdf_uri, ontology_uri)
        self.assertEqual(result, "rdf:type")
        
        # Test RDFS namespace
        rdfs_uri = URIRef("http://www.w3.org/2000/01/rdf-schema#label")
        result = self.agent._prefix_uri(rdfs_uri, ontology_uri)
        self.assertEqual(result, "rdfs:label")
    
    def test_ontology_to_turtle_empty_ontology(self):
        """Test conversion of empty ontology to Turtle format."""
        result = self.agent._ontology_to_prompt(self.test_ontology)
        
        self.assertIn("@prefix onto:", result)
        self.assertIn("owl:Ontology", result)
        self.assertIn("Test Ontology", result)
    
    @patch('agents.modelers.modeler_openai_basic.OpenAI')
    def test_do_design_task_success(self, mock_openai_class):
        """Test successful execution of design task."""
        # Mock OpenAI client and responses
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        # Mock search queries response
        mock_search_response = Mock()
        mock_search_response.choices = [Mock()]
        mock_search_response.choices[0].message = Mock()
        mock_search_response.choices[0].message.parsed = Mock()
        mock_search_response.choices[0].message.parsed.queries = [
            Mock(query="test query", max_results=10, offset=0)
        ]
        
        # Mock edit operations response
        mock_ops_response = Mock()
        mock_ops_response.choices = [Mock()]
        mock_ops_response.choices[0].message = Mock()
        mock_ops_response.choices[0].message.parsed = Mock()
        mock_ops_response.choices[0].message.parsed.class_operations = [
            Mock(
                operation_type="create",
                uri="http://example.org/test-ontology#TestClass",
                label="Test Class",
                definition="A test class",
                description="Description of test class",
                generalization_uris=None
            )
        ]
        mock_ops_response.choices[0].message.parsed.attribute_operations = []
        mock_ops_response.choices[0].message.parsed.relationship_operations = []
        
        # Configure mock client to return our mock responses
        mock_client.beta.chat.completions.parse.side_effect = [
            mock_search_response, 
            mock_ops_response
        ]
        
        # Mock knowledge base search
        self.knowledge_base_index_service.search_by_query.return_value = [
            Mock(element=Mock(content="Test knowledge", source_document_id="doc1"), similarity_score=0.9)
        ]
        
        # Re-initialize agent with mocked OpenAI
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            self.agent.client = mock_client
        
        # Execute the test
        result = self.agent.get_operations_for_design_task(self.test_project, self.test_iteration, self.test_task)
        
        # Verify results
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], CreateClassOperation)
        self.assertEqual(str(result[0].uri), "http://example.org/test-ontology#TestClass")
        self.assertEqual(result[0].label, "Test Class")

    def test_do_design_task_error_handling(self):
        """Test error handling in do_design_task method."""
        # Mock knowledge base search to raise an exception
        self.knowledge_base_index_service.search_by_query.side_effect = Exception("Search failed")
        
        # Mock OpenAI client that fails
        with patch('agents.modelers.modeler_openai_basic.OpenAI') as mock_openai_class:
            mock_client = Mock()
            mock_openai_class.return_value = mock_client
            mock_client.beta.chat.completions.parse.side_effect = Exception("OpenAI API failed")
            
            with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
                self.agent.client = mock_client
            
            # Execute the test - should return empty list on error
            result = self.agent.get_operations_for_design_task(self.test_project, self.test_iteration, self.test_task)
            
            # Should return empty list on error
            self.assertIsInstance(result, list)
            self.assertEqual(len(result), 0)


if __name__ == '__main__':
    # Run the tests
    unittest.main()