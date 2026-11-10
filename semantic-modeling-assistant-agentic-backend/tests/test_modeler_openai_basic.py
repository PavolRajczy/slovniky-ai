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
from ontology.domain import Kind, Ontology, OntologyAttribute, OntologyClass, OntologyRelationship
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
            plannedOperations=None,
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
            self.assertEqual(agent.model_name, "mini")
    
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
        """Elements in the ontology namespace are shortened to their local name."""
        ontology_uri = URIRef("http://example.org/vehicles#")
        element_uri = URIRef("http://example.org/vehicles#Car")

        self.assertEqual(self.agent.prefix_uri(element_uri, ontology_uri), "Car")

    def test_prefix_uri_external_namespace(self):
        """Elements outside the ontology namespace keep their full URI in angle brackets."""
        ontology_uri = URIRef("http://example.org/vehicles#")
        rdfs_label = URIRef("http://www.w3.org/2000/01/rdf-schema#label")

        self.assertEqual(
            self.agent.prefix_uri(rdfs_label, ontology_uri),
            "<http://www.w3.org/2000/01/rdf-schema#label>",
        )

    def test_local_name_to_full_uri(self):
        """Local names returned by the model become URIs in the ontology namespace."""
        ontology_uri = "http://example.org/vehicles"

        self.assertEqual(self.agent._local_name_to_full_uri(":Car", ontology_uri), URIRef("http://example.org/vehicles#Car"))
        self.assertEqual(self.agent._local_name_to_full_uri(":vehicles#Car", ontology_uri), URIRef("http://example.org/vehicles#Car"))
        self.assertIsNone(self.agent._local_name_to_full_uri("Car", ontology_uri))
        self.assertIsNone(self.agent._local_name_to_full_uri(":", ontology_uri))

    def test_ontology_to_prompt_empty_ontology(self):
        """An empty ontology is rendered with its label and empty sections."""
        result = self.agent._ontology_to_prompt(self.test_ontology)

        self.assertIn('"Test Ontology"', result)
        self.assertIn("CLASSES (0):", result)
        self.assertIn("RELATIONSHIPS (0):", result)

    def test_ontology_to_prompt_lists_classes_attributes_and_relationships(self):
        """Classes show kind, definition, superclasses and attributes; relationships show their ends."""
        ontology = Ontology(uri=URIRef("http://example.org/vehicles#"), label="Vehicles", description=None)
        person = OntologyClass(uri=URIRef("http://example.org/vehicles#Person"), label="Person", definition="A human.", description=None)
        vehicle = OntologyClass(uri=URIRef("http://example.org/vehicles#Vehicle"), label="Vehicle", definition=None, description=None, kind=Kind.OBJECT)
        car = OntologyClass(uri=URIRef("http://example.org/vehicles#Car"), label="Car", definition=None, description=None, kind=Kind.OBJECT)
        car.generalizations.append(vehicle)
        vin = OntologyAttribute(uri=URIRef("http://example.org/vehicles#vin"), label="VIN", definition="Vehicle identification number.", description=None, owningClass=vehicle)
        vehicle.attributes.append(vin)
        owns = OntologyRelationship(uri=URIRef("http://example.org/vehicles#owns"), label="owns", definition=None, description=None, sourceClass=person, targetClass=vehicle)
        ontology.classes = {c.uri: c for c in (person, vehicle, car)}
        ontology.attributes = {vin.uri: vin}
        ontology.relationships = {owns.uri: owns}

        result = self.agent._ontology_to_prompt(ontology)

        self.assertIn("CLASSES (3):", result)
        self.assertIn(':Person "Person" [SUBJECT]', result)
        self.assertIn("DEF: A human.", result)
        self.assertIn(':Car "Car" [OBJECT]', result)
        self.assertIn("SUPER: :Vehicle", result)
        self.assertIn('- :vin "VIN"', result)
        self.assertIn("RELATIONSHIPS (1):", result)
        self.assertIn("FROM: :Person  TO: :Vehicle", result)
    
    @patch("agents.modelers.modeler_openai_basic.parse_structured")
    def test_do_design_task_success(self, mock_parse):
        """Test successful execution of design task."""
        class_operation = Mock(
            operation_type="create",
            prefixed_name=":TestClass",
            label="Test Class",
            definition="A test class",
            description="Description of test class",
            generalizations_prefixed_names=None,
            kind=None,
            definition_references=None,
            specification_references=None,
            references=None,
        )
        mock_parse.return_value = Mock(
            class_operations=[class_operation],
            attribute_operations=[],
            relationship_operations=[],
        )
        self.knowledge_base_index_service.search_relative.return_value = []

        result = self.agent.get_operations_for_design_task(
            self.test_project,
            self.test_ontology,
            self.test_iteration,
            self.test_task,
        )

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], CreateClassOperation)
        self.assertEqual(str(result[0].uri), "http://example.org/test-ontology#TestClass")
        self.assertEqual(result[0].label, "Test Class")

    @patch("agents.modelers.modeler_openai_basic.parse_structured")
    def test_do_design_task_error_handling(self, mock_parse):
        """Test error handling in do_design_task method."""
        mock_parse.side_effect = Exception("OpenAI API failed")
        self.knowledge_base_index_service.search_relative.return_value = []

        result = self.agent.get_operations_for_design_task(
            self.test_project,
            self.test_ontology,
            self.test_iteration,
            self.test_task,
        )

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)


if __name__ == '__main__':
    # Run the tests
    unittest.main()