"""
Test the remove_iteration functionality.
This tests that we can remove both planned and current iterations.
"""

import os
import sys
import uuid

# Ensure src/ is importable when running as a script
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from design_project.store import FileSystemDesignProjectStore
from design_project.domain import DesignProject, DesignIteration, DesignIterationStatus, KnowledgeDomainArea, KnowledgeDomain
from ontology.domain import Ontology
from ontology.service import OntologyService
from ontology.store import FilesystemOntologyStore

TEST_DATA_DIR = "data_test"


def create_iteration(iteration_id, name, status, area, planned_operations=None):
    """Helper function to create a DesignIteration with all required fields."""
    return DesignIteration(
        id=iteration_id,
        name=name,
        status=status,
        specification="Test specification",
        finishedTasks=[],
        currentTask=None,
        plannedTasks=[],
        focusedArea=area,
        plannedOperations=planned_operations,
        designedOntologyChangesSpecification=None
    )


def create_test_project_with_store():
    """Create a test project directly using the store."""
    ontology_store = FilesystemOntologyStore(base_dir=f"{TEST_DATA_DIR}/ontologies")
    ontology_service = OntologyService(store=ontology_store)
    store = FileSystemDesignProjectStore(
        ontology_service=ontology_service,
        base_dir=f"{TEST_DATA_DIR}/projects"
    )
    
    # Create a test ontology
    ontology = Ontology(
        uri="http://test.example.org/remove-iteration-test",
        label="Test Ontology",
        description="Test ontology for iteration removal",
        classes={},
        attributes={},
        relationships={}
    )
    
    # Create a domain area
    domain = KnowledgeDomain(
        label="Test Domain",
        description="Test domain for iteration removal",
        areas=[]
    )
    
    area = KnowledgeDomainArea(
        id=str(uuid.uuid4()),
        label="Test Area",
        description="Test area for iteration removal",
        parent=domain,
        keyConcepts=["concept1", "concept2"],
        modelingClasses=[],
        modelingAttributes=[],
        modelingRelationships=[],
        explainingKnowledgeResources=[]
    )
    
    domain.areas.append(area)
    
    # Create a project
    project = DesignProject(
        id=str(uuid.uuid4()),
        name="Test Remove Iteration",
        finishedIterations=[],
        currentIteration=None,
        plannedIterations=[],
        patterns=[],
        patternsFactoryId="default",
        legalKnowledgeBase=[],
        expertKnowledgeBase=[],
        keyKnowledgeDocument=None,
        modeledKnowledgeDomain=domain,
        designedOntology=ontology
    )
    
    # Add ontology to store's cache so it can be stored
    ontology_store.ontologies[ontology.uri] = ontology
    ontology_service.store_ontology(ontology)
    
    # Store the project
    store.store_project(project)
    
    # Return store and ontology_store for later use
    return store, ontology_store, project, area


def test_remove_planned_iteration():
    """Test removing a planned iteration."""
    print("\n=== Test: Remove Planned Iteration ===")
    
    store, ontology_store, project, area = create_test_project_with_store()
    
    # Create a planned iteration manually
    iteration = create_iteration(
        iteration_id=str(uuid.uuid4()),
        name="Test Planned Iteration",
        status=DesignIterationStatus.PLANNED,
        area=area
    )
    
    project.plannedIterations.append(iteration)
    store.store_project(project)
    
    print(f"Created planned iteration: {iteration.id}")
    print(f"Planned iterations count: {len(project.plannedIterations)}")
    
    # Now import and use the service method
    from design_project.service import DesignProjectService
    
    # Create a minimal service instance just for this method
    # We can pass None for agents since we won't be using them
    service = DesignProjectService(
        store=store,
        knowledge_base_service=None,
        ontology_service=None,
        knowledge_domain_area_analyzer_agent=None,
        iteration_suggester_agent=None,
        task_planner_agent=None,
        modeler_agent=None
    )
    
    # Remove the iteration
    service.remove_iteration(project.id, iteration.id)
    
    # Verify it was removed
    project = store.load_project(project.id)
    assert len(project.plannedIterations) == 0, "Planned iteration should be removed"
    assert project.currentIteration is None, "Current iteration should still be None"
    
    print("✓ Successfully removed planned iteration")
    print(f"✓ Planned iterations count after removal: {len(project.plannedIterations)}")


def test_remove_current_iteration():
    """Test removing the current iteration."""
    print("\n=== Test: Remove Current Iteration ===")
    
    store, ontology_store, project, area = create_test_project_with_store()
    
    # Create a current iteration manually
    iteration = create_iteration(
        iteration_id=str(uuid.uuid4()),
        name="Test Current Iteration",
        status=DesignIterationStatus.OPERATIONS_GENERATED,
        area=area,
        planned_operations=[]
    )
    
    project.currentIteration = iteration
    store.store_project(project)
    
    print(f"Created current iteration: {iteration.id}")
    print(f"Current iteration status: {iteration.status}")
    
    from design_project.service import DesignProjectService
    service = DesignProjectService(
        store=store,
        knowledge_base_service=None,
        ontology_service=None,
        knowledge_domain_area_analyzer_agent=None,
        iteration_suggester_agent=None,
        task_planner_agent=None,
        modeler_agent=None
    )
    
    # Remove the iteration
    service.remove_iteration(project.id, iteration.id)
    
    # Verify it was removed
    project = store.load_project(project.id)
    assert project.currentIteration is None, "Current iteration should be removed"
    assert len(project.plannedIterations) == 0, "Should have no planned iterations"
    
    print("✓ Successfully removed current iteration")
    print(f"✓ Current iteration after removal: {project.currentIteration}")


def test_cannot_remove_finished_iteration():
    """Test that we cannot remove a finished iteration."""
    print("\n=== Test: Cannot Remove Finished Iteration ===")
    
    store, ontology_store, project, area = create_test_project_with_store()
    
    # Create a finished iteration manually
    iteration = create_iteration(
        iteration_id=str(uuid.uuid4()),
        name="Test Finished Iteration",
        status=DesignIterationStatus.COMPLETED,
        area=area
    )
    
    project.finishedIterations.append(iteration)
    store.store_project(project)
    
    print(f"Created finished iteration: {iteration.id}")
    print(f"Finished iterations count: {len(project.finishedIterations)}")
    
    from design_project.service import DesignProjectService
    service = DesignProjectService(
        store=store,
        knowledge_base_service=None,
        ontology_service=None,
        knowledge_domain_area_analyzer_agent=None,
        iteration_suggester_agent=None,
        task_planner_agent=None,
        modeler_agent=None
    )
    
    # Try to remove the iteration - should raise ValueError
    try:
        service.remove_iteration(project.id, iteration.id)
        assert False, "Should have raised ValueError for finished iteration"
    except ValueError as e:
        assert "finished" in str(e).lower(), f"Error message should mention 'finished': {e}"
        print(f"✓ Correctly prevented removal of finished iteration: {e}")
    
    # Verify it was NOT removed
    project = store.load_project(project.id)
    assert len(project.finishedIterations) == 1, "Finished iteration should still exist"
    
    print("✓ Finished iteration was not removed (as expected)")


def test_remove_nonexistent_iteration():
    """Test removing a non-existent iteration."""
    print("\n=== Test: Remove Non-existent Iteration ===")
    
    store, ontology_store, project, area = create_test_project_with_store()
    
    fake_id = str(uuid.uuid4())
    
    from design_project.service import DesignProjectService
    service = DesignProjectService(
        store=store,
        knowledge_base_service=None,
        ontology_service=None,
        knowledge_domain_area_analyzer_agent=None,
        iteration_suggester_agent=None,
        task_planner_agent=None,
        modeler_agent=None
    )
    
    # Try to remove the iteration - should raise ValueError
    try:
        service.remove_iteration(project.id, fake_id)
        assert False, "Should have raised ValueError for non-existent iteration"
    except ValueError as e:
        assert "not found" in str(e).lower(), f"Error message should mention 'not found': {e}"
        print(f"✓ Correctly handled non-existent iteration: {e}")


def test_remove_multiple_iterations():
    """Test removing multiple iterations from different locations."""
    print("\n=== Test: Remove Multiple Iterations ===")
    
    store, ontology_store, project, area = create_test_project_with_store()
    
    # Create multiple planned iterations
    planned1 = create_iteration(
        iteration_id=str(uuid.uuid4()),
        name="Planned 1",
        status=DesignIterationStatus.PLANNED,
        area=area
    )
    
    planned2 = create_iteration(
        iteration_id=str(uuid.uuid4()),
        name="Planned 2",
        status=DesignIterationStatus.TASKS_PLANNED,
        area=area
    )
    
    # Create a current iteration
    current = create_iteration(
        iteration_id=str(uuid.uuid4()),
        name="Current",
        status=DesignIterationStatus.GENERATING_OPERATIONS,
        area=area
    )
    
    project.plannedIterations.extend([planned1, planned2])
    project.currentIteration = current
    store.store_project(project)
    
    print(f"Created 2 planned + 1 current iteration")
    
    from design_project.service import DesignProjectService
    service = DesignProjectService(
        store=store,
        knowledge_base_service=None,
        ontology_service=None,
        knowledge_domain_area_analyzer_agent=None,
        iteration_suggester_agent=None,
        task_planner_agent=None,
        modeler_agent=None
    )
    
    # Remove planned iteration
    service.remove_iteration(project.id, planned1.id)
    project = store.load_project(project.id)
    assert len(project.plannedIterations) == 1, "Should have 1 planned iteration"
    assert project.currentIteration is not None, "Should still have current iteration"
    print("✓ Removed first planned iteration")
    
    # Remove current iteration
    service.remove_iteration(project.id, current.id)
    project = store.load_project(project.id)
    assert len(project.plannedIterations) == 1, "Should still have 1 planned iteration"
    assert project.currentIteration is None, "Should have no current iteration"
    print("✓ Removed current iteration")
    
    # Remove last planned iteration
    service.remove_iteration(project.id, planned2.id)
    project = store.load_project(project.id)
    assert len(project.plannedIterations) == 0, "Should have no planned iterations"
    print("✓ Removed last planned iteration")
    
    print("✓ Successfully removed multiple iterations")


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("Testing Iteration Removal Functionality")
    print("=" * 60)
    
    test_remove_planned_iteration()
    test_remove_current_iteration()
    test_cannot_remove_finished_iteration()
    test_remove_nonexistent_iteration()
    test_remove_multiple_iterations()
    
    print("\n" + "=" * 60)
    print("All tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
