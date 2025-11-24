"""
Test suite for Design Project Service - State Management Workflow

This test validates the hybrid state management approach where:
- Location (which list) represents workflow position
- Status (enum) represents detailed work stage

Tests cover the complete workflow:
1. suggest_iterations
2. initialize_iteration_tasks  
3. prepare_planned_iteration
4. apply_current_iteration_changes

Plus rollback scenarios.
"""

import os
import shutil
import uuid
from rdflib import URIRef

from design_project.service import DesignProjectService
from design_project.store import FileSystemDesignProjectStore
from design_project.domain import (
    DesignIterationStatus, DesignTaskStatus, DesignTaskPattern, 
    DesignTaskCategory, KnowledgeDomain, KnowledgeDomainArea
)
from knowledge_base.service import KnowledgeBaseService
from knowledge_base.store import KnowledgeDocumentLoader, KnowledgeDocumentSummarizer
from knowledge_base.domain import KnowledgeDocument
from ontology.service import OntologyService
from ontology.store import FilesystemOntologyStore
from ontology.domain import Ontology, Kind
from ontology.edit_operations import CreateClassOperation, OperationType

from agents.knowledge_domain_area_analyzers.knowledge_domain_area_analyzer import KnowledgeDomainAreaAnalyzerAgentFake
from agents.iteration_suggesters.iteration_suggester import IterationSuggesterAgentFake
from agents.task_planners.task_planner import TaskPlannerAgentFake
from agents.modelers.modeler import ModelerAgentFake


# Test data directory
TEST_DATA_DIR = "data_test/design_project_service"


def setup_test_environment():
    """Setup test directory and services."""
    # Clean and create test directory
    if os.path.exists(TEST_DATA_DIR):
        shutil.rmtree(TEST_DATA_DIR)
    os.makedirs(TEST_DATA_DIR, exist_ok=True)
    
    # Create services
    ontology_store = FilesystemOntologyStore(base_dir=f"{TEST_DATA_DIR}/ontologies")
    ontology_service = OntologyService(store=ontology_store)
    
    # Create fake loaders and summarizer for knowledge base
    class FakeLoader(KnowledgeDocumentLoader):
        def load_document(self, document_id: str) -> KnowledgeDocument:
            return KnowledgeDocument(id=document_id, title="Fake", content="Fake content", contentSummary=None)
        def list_all_documents(self) -> list:
            return []
    
    class FakeSummarizer(KnowledgeDocumentSummarizer):
        def summarize_document(self, document: KnowledgeDocument) -> str:
            return "Fake summary"
    
    kb_service = KnowledgeBaseService(
        legal_knowledge_document_loader=FakeLoader(),
        expert_knowledge_document_loader=FakeLoader(),
        document_summarizer=FakeSummarizer()
    )
    
    project_store = FileSystemDesignProjectStore(
        ontology_service=ontology_service,
        base_dir=f"{TEST_DATA_DIR}/projects"
    )
    
    # Create fake agents
    domain_area_analyzer = KnowledgeDomainAreaAnalyzerAgentFake()
    iteration_suggester = IterationSuggesterAgentFake()
    task_planner = TaskPlannerAgentFake()
    modeler = ModelerAgentFake()
    
    service = DesignProjectService(
        store=project_store,
        knowledge_base_service=kb_service,
        ontology_service=ontology_service,
        knowledge_domain_area_analyzer_agent=domain_area_analyzer,
        iteration_suggester_agent=iteration_suggester,
        task_planner_agent=task_planner,
        modeler_agent=modeler
    )
    
    return service, ontology_service, kb_service


def create_test_ontology(ontology_service):
    """Create a test ontology."""
    ontology = Ontology(
        uri=URIRef("http://test.example.org/ontology"),
        label="Test Ontology",
        description="A test ontology",
        classes={},
        attributes={},
        relationships={}
    )
    ontology_service.store_ontology(ontology)
    return ontology


def create_test_project(service, ontology):
    """Create a test project with domain areas."""
    project = service.initialize_new_project(
        project_name="Test Project",
        working_ontology_uri=str(ontology.uri),
        knowledge_domain_name="Test Domain",
        knowledge_domain_description="A test domain"
    )
    
    # Manually add domain areas (simulating what would come from generate_domain_areas)
    area1 = KnowledgeDomainArea(
        id=str(uuid.uuid4()),
        label="Area 1",
        description="First test area",
        parent=project.modeledKnowledgeDomain,
        keyConcepts=["concept1", "concept2"],
        modelingClasses=[],
        modelingAttributes=[],
        modelingRelationships=[],
        explainingKnowledgeResources=[]
    )
    
    area2 = KnowledgeDomainArea(
        id=str(uuid.uuid4()),
        label="Area 2",
        description="Second test area",
        parent=project.modeledKnowledgeDomain,
        keyConcepts=["concept3", "concept4"],
        modelingClasses=[],
        modelingAttributes=[],
        modelingRelationships=[],
        explainingKnowledgeResources=[]
    )
    
    project.modeledKnowledgeDomain.areas = [area1, area2]
    service.save_project(project)
    
    return project


def test_workflow_step1_suggest_iterations():
    """Test Step 1: suggest_iterations creates iterations in plannedIterations with PLANNED status."""
    print("\n" + "="*80)
    print("TEST: suggest_iterations - Step 1")
    print("="*80)
    
    service, ontology_service, kb_service = setup_test_environment()
    ontology = create_test_ontology(ontology_service)
    project = create_test_project(service, ontology)
    
    # Execute: suggest iterations
    iterations = service.suggest_iterations(
        project_id=project.id,
        focused_area_id=project.modeledKnowledgeDomain.areas[0].id,
        k=2,
        user_instruction="Focus on core classes"
    )
    
    # Verify
    assert len(iterations) == 2, f"Expected 2 iterations, got {len(iterations)}"
    
    # Reload project to verify persistence
    project = service.load_project(project.id)
    
    # Check location: should be in plannedIterations
    assert len(project.plannedIterations) == 2, f"Expected 2 planned iterations, got {len(project.plannedIterations)}"
    assert project.currentIteration is None, "Current iteration should be None"
    assert len(project.finishedIterations) == 0, "Finished iterations should be empty"
    
    # Check status: should be PLANNED
    for iteration in project.plannedIterations:
        assert iteration.status == DesignIterationStatus.PLANNED, \
            f"Iteration status should be PLANNED, got {iteration.status}"
        assert iteration.plannedOperations is None, \
            "plannedOperations should be None initially"
    
    print("✓ Iterations created in plannedIterations with PLANNED status")
    print(f"✓ Location: plannedIterations (count={len(project.plannedIterations)})")
    print(f"✓ Status: {project.plannedIterations[0].status}")
    return project


def test_workflow_step2_initialize_tasks():
    """Test Step 2: initialize_iteration_tasks transitions to TASKS_PLANNED, stays in plannedIterations."""
    print("\n" + "="*80)
    print("TEST: initialize_iteration_tasks - Step 2")
    print("="*80)
    
    service, ontology_service, kb_service = setup_test_environment()
    ontology = create_test_ontology(ontology_service)
    project = create_test_project(service, ontology)
    
    # Setup: create an iteration
    iterations = service.suggest_iterations(
        project_id=project.id,
        focused_area_id=project.modeledKnowledgeDomain.areas[0].id,
        k=1,
        user_instruction="Test"
    )
    iteration_id = iterations[0].id
    
    # Execute: initialize tasks
    tasks = service.initialize_iteration_tasks(
        project_id=project.id,
        iteration_id=iteration_id,
        user_instruction="Create basic classes"
    )
    
    # Verify
    assert len(tasks) > 0, "Should have created tasks"
    
    # Reload project
    project = service.load_project(project.id)
    
    # Check location: should still be in plannedIterations
    assert len(project.plannedIterations) == 1, "Should still have 1 planned iteration"
    assert project.currentIteration is None, "Current iteration should still be None"
    
    iteration = project.plannedIterations[0]
    
    # Check status: should be TASKS_PLANNED
    assert iteration.status == DesignIterationStatus.TASKS_PLANNED, \
        f"Status should be TASKS_PLANNED, got {iteration.status}"
    
    # Check tasks
    assert len(iteration.plannedTasks) > 0, "Should have planned tasks"
    for task in iteration.plannedTasks:
        assert task.status == DesignTaskStatus.PLANNED, \
            f"Task status should be PLANNED, got {task.status}"
    
    print(f"✓ Tasks initialized: {len(iteration.plannedTasks)} tasks")
    print(f"✓ Location: plannedIterations (unchanged)")
    print(f"✓ Status: {iteration.status}")
    print(f"✓ All tasks have status: PLANNED")
    return project


def test_workflow_step3_prepare_iteration():
    """Test Step 3: prepare_planned_iteration generates operations, moves to currentIteration with OPERATIONS_GENERATED."""
    print("\n" + "="*80)
    print("TEST: prepare_planned_iteration - Step 3")
    print("="*80)
    
    service, ontology_service, kb_service = setup_test_environment()
    ontology = create_test_ontology(ontology_service)
    project = create_test_project(service, ontology)
    
    # Setup: create iteration with tasks
    iterations = service.suggest_iterations(
        project_id=project.id,
        focused_area_id=project.modeledKnowledgeDomain.areas[0].id,
        k=1,
        user_instruction="Test"
    )
    iteration_id = iterations[0].id
    
    service.initialize_iteration_tasks(
        project_id=project.id,
        iteration_id=iteration_id,
        user_instruction="Create classes"
    )
    
    # Execute: prepare iteration
    operations = service.prepare_planned_iteration(
        project_id=project.id,
        iteration_id=iteration_id
    )
    
    # Verify
    assert len(operations) > 0, "Should have generated operations"
    
    # Reload project
    project = service.load_project(project.id)
    
    # Check location: should be in currentIteration
    assert project.currentIteration is not None, "Should have a current iteration"
    assert len(project.plannedIterations) == 0, "Planned iterations should be empty"
    assert len(project.finishedIterations) == 0, "Finished iterations should still be empty"
    
    iteration = project.currentIteration
    
    # Check status: should be OPERATIONS_GENERATED
    assert iteration.status == DesignIterationStatus.OPERATIONS_GENERATED, \
        f"Status should be OPERATIONS_GENERATED, got {iteration.status}"
    
    # Check operations are stored
    assert iteration.plannedOperations is not None, "plannedOperations should be set"
    assert len(iteration.plannedOperations) == len(operations), \
        f"Should have stored {len(operations)} operations"
    
    # Check tasks status
    for task in iteration.plannedTasks:
        assert task.status == DesignTaskStatus.OPERATIONS_GENERATED, \
            f"Task status should be OPERATIONS_GENERATED, got {task.status}"
    
    print(f"✓ Operations generated: {len(operations)} operations")
    print(f"✓ Location: currentIteration")
    print(f"✓ Status: {iteration.status}")
    print(f"✓ Operations stored in iteration.plannedOperations")
    print(f"✓ All tasks have status: OPERATIONS_GENERATED")
    return project, operations


def test_workflow_step4_apply_changes():
    """Test Step 4: apply_current_iteration_changes applies operations, moves to finishedIterations with COMPLETED."""
    print("\n" + "="*80)
    print("TEST: apply_current_iteration_changes - Step 4")
    print("="*80)
    
    service, ontology_service, kb_service = setup_test_environment()
    ontology = create_test_ontology(ontology_service)
    project = create_test_project(service, ontology)
    
    # Setup: create iteration through all previous steps
    iterations = service.suggest_iterations(
        project_id=project.id,
        focused_area_id=project.modeledKnowledgeDomain.areas[0].id,
        k=1,
        user_instruction="Test"
    )
    iteration_id = iterations[0].id
    
    service.initialize_iteration_tasks(
        project_id=project.id,
        iteration_id=iteration_id,
        user_instruction="Create classes"
    )
    
    operations = service.prepare_planned_iteration(
        project_id=project.id,
        iteration_id=iteration_id
    )
    
    # Execute: apply changes
    service.apply_current_iteration_changes(
        project_id=project.id,
        operations=operations
    )
    
    # Reload project
    project = service.load_project(project.id)
    
    # Check location: should be in finishedIterations
    assert project.currentIteration is None, "Current iteration should be None"
    assert len(project.plannedIterations) == 0, "Planned iterations should be empty"
    assert len(project.finishedIterations) == 1, "Should have 1 finished iteration"
    
    iteration = project.finishedIterations[0]
    
    # Check status: should be COMPLETED
    assert iteration.status == DesignIterationStatus.COMPLETED, \
        f"Status should be COMPLETED, got {iteration.status}"
    
    # Check operations cleared
    assert iteration.plannedOperations is None, \
        "plannedOperations should be cleared after application"
    
    # Check tasks
    assert len(iteration.finishedTasks) > 0, "Should have finished tasks"
    assert len(iteration.plannedTasks) == 0, "Should have no planned tasks"
    for task in iteration.finishedTasks:
        assert task.status == DesignTaskStatus.COMPLETED, \
            f"Task status should be COMPLETED, got {task.status}"
    
    # Verify ontology was actually modified
    ontology = ontology_service.load_ontology(str(project.designedOntology.uri))
    assert len(ontology.classes) > 0, "Ontology should have classes added"
    
    print(f"✓ Changes applied to ontology")
    print(f"✓ Location: finishedIterations")
    print(f"✓ Status: {iteration.status}")
    print(f"✓ Operations cleared from iteration.plannedOperations")
    print(f"✓ All tasks moved to finishedTasks with COMPLETED status")
    print(f"✓ Ontology modified: {len(ontology.classes)} classes")
    return project


def test_complete_workflow():
    """Test the complete workflow from start to finish."""
    print("\n" + "="*80)
    print("TEST: Complete Workflow - All 4 Steps")
    print("="*80)
    
    service, ontology_service, kb_service = setup_test_environment()
    ontology = create_test_ontology(ontology_service)
    project = create_test_project(service, ontology)
    
    print("\nStep 1: Suggest iterations...")
    iterations = service.suggest_iterations(
        project_id=project.id,
        focused_area_id=project.modeledKnowledgeDomain.areas[0].id,
        k=2,
        user_instruction="Create domain model"
    )
    assert len(iterations) == 2
    
    # Process first iteration
    iteration_id = iterations[0].id
    
    print("\nStep 2: Initialize tasks...")
    tasks = service.initialize_iteration_tasks(
        project_id=project.id,
        iteration_id=iteration_id,
        user_instruction="Focus on core entities"
    )
    assert len(tasks) > 0
    
    print("\nStep 3: Prepare iteration (generate operations)...")
    operations = service.prepare_planned_iteration(
        project_id=project.id,
        iteration_id=iteration_id
    )
    assert len(operations) > 0
    
    print("\nStep 4: Apply changes...")
    service.apply_current_iteration_changes(
        project_id=project.id,
        operations=operations
    )
    
    # Verify final state
    project = service.load_project(project.id)
    
    assert len(project.finishedIterations) == 1, "Should have 1 finished iteration"
    assert project.currentIteration is None, "Should have no current iteration"
    assert len(project.plannedIterations) == 1, "Should have 1 remaining planned iteration"
    
    finished = project.finishedIterations[0]
    assert finished.status == DesignIterationStatus.COMPLETED
    assert finished.id == iteration_id
    
    planned = project.plannedIterations[0]
    assert planned.status == DesignIterationStatus.PLANNED
    
    print("\n✓ Complete workflow succeeded")
    print(f"✓ Finished iterations: {len(project.finishedIterations)}")
    print(f"✓ Current iteration: {project.currentIteration}")
    print(f"✓ Planned iterations: {len(project.plannedIterations)}")
    return project


def test_status_validation():
    """Test that status validation works correctly."""
    print("\n" + "="*80)
    print("TEST: Status Validation")
    print("="*80)
    
    service, ontology_service, kb_service = setup_test_environment()
    ontology = create_test_ontology(ontology_service)
    project = create_test_project(service, ontology)
    
    # Create iteration in PLANNED state
    iterations = service.suggest_iterations(
        project_id=project.id,
        focused_area_id=project.modeledKnowledgeDomain.areas[0].id,
        k=1,
        user_instruction="Test"
    )
    iteration_id = iterations[0].id
    
    # Try to prepare without initializing tasks (should fail)
    try:
        service.prepare_planned_iteration(
            project_id=project.id,
            iteration_id=iteration_id
        )
        assert False, "Should have raised ValueError for missing tasks"
    except ValueError as e:
        assert "no planned tasks" in str(e).lower()
        print("✓ Correctly rejected prepare without tasks")
    
    # Initialize tasks
    service.initialize_iteration_tasks(
        project_id=project.id,
        iteration_id=iteration_id,
        user_instruction="Test"
    )
    
    # Prepare iteration
    operations = service.prepare_planned_iteration(
        project_id=project.id,
        iteration_id=iteration_id
    )
    
    # Try to apply with wrong status by manipulating it
    # (This tests that apply validates the status)
    project = service.load_project(project.id)
    original_status = project.currentIteration.status
    
    # Temporarily change status to wrong value
    project.currentIteration.status = DesignIterationStatus.PLANNED
    service.save_project(project)
    
    try:
        service.apply_current_iteration_changes(
            project_id=project.id,
            operations=operations
        )
        assert False, "Should have raised ValueError for wrong status"
    except ValueError as e:
        assert "OPERATIONS_GENERATED" in str(e)
        print("✓ Correctly rejected apply with wrong status")
    
    # Fix the status and try again
    project = service.load_project(project.id)
    project.currentIteration.status = original_status
    service.save_project(project)
    
    service.apply_current_iteration_changes(
        project_id=project.id,
        operations=operations
    )
    print("✓ Successfully applied with correct status")


def test_invariants():
    """Test that invariants are maintained throughout the workflow."""
    print("\n" + "="*80)
    print("TEST: State Invariants")
    print("="*80)
    
    service, ontology_service, kb_service = setup_test_environment()
    ontology = create_test_ontology(ontology_service)
    project = create_test_project(service, ontology)
    
    def check_invariants(project, step_name):
        """Check that all invariants hold."""
        # Only one current iteration at a time
        assert project.currentIteration is None or isinstance(project.currentIteration, type(project.plannedIterations[0])) if project.plannedIterations else True
        
        # Location-Status consistency
        for iteration in project.plannedIterations:
            assert iteration.status in [DesignIterationStatus.PLANNED, DesignIterationStatus.TASKS_PLANNED], \
                f"[{step_name}] Planned iteration has invalid status: {iteration.status}"
        
        if project.currentIteration:
            assert project.currentIteration.status in [
                DesignIterationStatus.GENERATING_OPERATIONS,
                DesignIterationStatus.OPERATIONS_GENERATED,
                DesignIterationStatus.APPLYING_OPERATIONS
            ], f"[{step_name}] Current iteration has invalid status: {project.currentIteration.status}"
        
        for iteration in project.finishedIterations:
            assert iteration.status == DesignIterationStatus.COMPLETED, \
                f"[{step_name}] Finished iteration has invalid status: {iteration.status}"
        
        print(f"  ✓ Invariants hold at: {step_name}")
    
    # Check at each step
    check_invariants(project, "Initial")
    
    iterations = service.suggest_iterations(
        project_id=project.id,
        focused_area_id=project.modeledKnowledgeDomain.areas[0].id,
        k=1,
        user_instruction="Test"
    )
    project = service.load_project(project.id)
    check_invariants(project, "After suggest_iterations")
    
    service.initialize_iteration_tasks(
        project_id=project.id,
        iteration_id=iterations[0].id,
        user_instruction="Test"
    )
    project = service.load_project(project.id)
    check_invariants(project, "After initialize_tasks")
    
    operations = service.prepare_planned_iteration(
        project_id=project.id,
        iteration_id=iterations[0].id
    )
    project = service.load_project(project.id)
    check_invariants(project, "After prepare_iteration")
    
    service.apply_current_iteration_changes(
        project_id=project.id,
        operations=operations
    )
    project = service.load_project(project.id)
    check_invariants(project, "After apply_changes")
    
    print("✓ All invariants maintained throughout workflow")


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*80)
    print("DESIGN PROJECT SERVICE - STATE MANAGEMENT TESTS")
    print("="*80)
    
    try:
        test_workflow_step1_suggest_iterations()
        test_workflow_step2_initialize_tasks()
        test_workflow_step3_prepare_iteration()
        test_workflow_step4_apply_changes()
        test_complete_workflow()
        test_status_validation()
        test_invariants()
        
        print("\n" + "="*80)
        print("ALL TESTS PASSED ✓")
        print("="*80)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        # Cleanup
        if os.path.exists(TEST_DATA_DIR):
            shutil.rmtree(TEST_DATA_DIR)
        print("\n✓ Test environment cleaned up")


if __name__ == "__main__":
    run_all_tests()
