"""
Unit test for API iteration and task status mapping.

This test verifies that the conversion functions correctly map domain status values
to API status values for both iterations and tasks.
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from design_project.domain import (
    DesignIteration, DesignTask, DesignIterationStatus, DesignTaskStatus,
    KnowledgeDomainArea, KnowledgeDomain, DesignTaskPattern, DesignTaskCategory
)
from api.controllers.design_project_controller import _convert_iteration_to_model, _convert_task_to_model
from ontology.domain import Ontology


def test_iteration_status_mapping():
    """Test that all domain iteration statuses map correctly to API statuses."""
    
    # Create minimal test data
    domain = KnowledgeDomain(label="Test Domain", description="Test", areas=[])
    area = KnowledgeDomainArea(
        id="area-1",
        label="Test Area",
        description="Test area",
        parent=domain,
        keyConcepts=[],
        modelingClasses=[],
        modelingAttributes=[],
        modelingRelationships=[],
        explainingKnowledgeResources=[]
    )
    
    # Test mapping for each domain status
    status_mappings = {
        DesignIterationStatus.PLANNED: "suggested",
        DesignIterationStatus.TASKS_PLANNED: "planned",
        DesignIterationStatus.GENERATING_OPERATIONS: "prepared",
        DesignIterationStatus.OPERATIONS_GENERATED: "prepared",
        DesignIterationStatus.APPLYING_OPERATIONS: "prepared",
        DesignIterationStatus.COMPLETED: "completed"
    }
    
    for domain_status, expected_api_status in status_mappings.items():
        iteration = DesignIteration(
            id=f"iter-{domain_status.value}",
            name="Test Iteration",
            status=domain_status,
            specification="Test spec",
            finishedTasks=[],
            currentTask=None,
            plannedTasks=[],
            focusedArea=area,
            plannedOperations=None,
            designedOntologyChangesSpecification=None
        )
        
        api_model = _convert_iteration_to_model(iteration)
        
        assert api_model.status == expected_api_status, (
            f"Expected status '{expected_api_status}' for domain status '{domain_status.value}', "
            f"but got '{api_model.status}'"
        )
        print(f"✓ {domain_status.value} -> {api_model.status}")


def test_task_status_mapping():
    """Test that all domain task statuses map correctly to API statuses."""
    
    # Create minimal test pattern
    pattern = DesignTaskPattern(
        id="pattern-1",
        name="Test Pattern",
        category=DesignTaskCategory.CLASS,
        specification="Test pattern",
        whenApplicable=None,
        exampleTasks=[]
    )
    
    # Test mapping for each domain status
    status_mappings = {
        DesignTaskStatus.PLANNED: "planned",
        DesignTaskStatus.GENERATING_OPERATIONS: "generating",
        DesignTaskStatus.OPERATIONS_GENERATED: "generating",
        DesignTaskStatus.COMPLETED: "completed"
    }
    
    for domain_status, expected_api_status in status_mappings.items():
        task = DesignTask(
            id=f"task-{domain_status.value}",
            name="Test Task",
            status=domain_status,
            followedPattern=pattern,
            specification="Test spec",
            knowledgeResources=[],
            designedOntologyChangesSpecification=None
        )
        
        api_model = _convert_task_to_model(task)
        
        assert api_model.status == expected_api_status, (
            f"Expected status '{expected_api_status}' for domain status '{domain_status.value}', "
            f"but got '{api_model.status}'"
        )
        print(f"✓ {domain_status.value} -> {api_model.status}")


def test_pydantic_validation():
    """Test that the API models accept the new status values."""
    from api.models import DesignIterationModel, DesignTaskModel
    
    # Test iteration model with all valid statuses
    valid_iteration_statuses = ["suggested", "planned", "prepared", "completed"]
    for status_value in valid_iteration_statuses:
        model = DesignIterationModel(
            id="test-id",
            name="Test",
            specification="Test spec",
            focused_area_id="area-1",
            status=status_value
        )
        assert model.status == status_value
        print(f"✓ DesignIterationModel accepts status: {status_value}")
    
    # Test task model with all valid statuses
    valid_task_statuses = ["planned", "generating", "completed"]
    for status_value in valid_task_statuses:
        model = DesignTaskModel(
            id="test-id",
            name="Test",
            specification="Test spec",
            followed_pattern_id="pattern-1",
            status=status_value
        )
        assert model.status == status_value
        print(f"✓ DesignTaskModel accepts status: {status_value}")


if __name__ == "__main__":
    print("Testing iteration status mapping...")
    test_iteration_status_mapping()
    print("\nTesting task status mapping...")
    test_task_status_mapping()
    print("\nTesting Pydantic validation...")
    test_pydantic_validation()
    print("\n✅ All tests passed!")
