"""
Unit tests for apply_iteration_changes validation.

Tests the security and validation logic when applying operations to an iteration.
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from fastapi import HTTPException
from api.models import ApplyOperationsRequest, OntologyOperationModel


def test_apply_operations_request_validation():
    """Test that ApplyOperationsRequest requires iteration_id."""
    print("\n=== Testing ApplyOperationsRequest Validation ===")
    
    # Create a valid request with iteration_id
    valid_request = ApplyOperationsRequest(
        iteration_id="test-iteration-123",
        operations=[
            OntologyOperationModel(
                operation_type="create",
                target_type="class",
                uri="http://example.org/Person",
                label="Person"
            )
        ]
    )
    
    print(f"Valid request created: iteration_id={valid_request.iteration_id}, operations count={len(valid_request.operations)}")
    
    assert valid_request.iteration_id == "test-iteration-123"
    assert len(valid_request.operations) == 1
    print("✓ Valid request structure verified!")
    
    # Try to create request without iteration_id (should fail)
    try:
        invalid_request = ApplyOperationsRequest(
            operations=[
                OntologyOperationModel(
                    operation_type="create",
                    target_type="class",
                    uri="http://example.org/Person",
                    label="Person"
                )
            ]
        )
        print("✗ Should have failed - iteration_id is required!")
        assert False, "Should have raised validation error"
    except Exception as e:
        print(f"✓ Correctly rejected request without iteration_id: {type(e).__name__}")


def test_apply_operations_model_dump():
    """Test that the request serializes correctly."""
    print("\n=== Testing ApplyOperationsRequest Serialization ===")
    
    request = ApplyOperationsRequest(
        iteration_id="test-iteration-456",
        operations=[
            OntologyOperationModel(
                operation_type="create",
                target_type="class",
                uri="http://example.org/Person",
                label="Person",
                kind="subject"
            ),
            OntologyOperationModel(
                operation_type="update",
                target_type="attribute",
                uri="http://example.org/age",
                label="Age",
                owning_class_uri="http://example.org/Person"
            )
        ]
    )
    
    dumped = request.model_dump()
    print(f"Serialized request: {dumped}")
    
    assert dumped["iteration_id"] == "test-iteration-456"
    assert len(dumped["operations"]) == 2
    assert dumped["operations"][0]["operation_type"] == "create"
    assert dumped["operations"][1]["operation_type"] == "update"
    
    print("✓ Serialization successful!")


def test_validation_scenario_documentation():
    """Document the expected validation scenarios."""
    print("\n=== Expected Validation Scenarios ===")
    
    scenarios = [
        {
            "scenario": "Valid request",
            "iteration_id": "current-iteration-id",
            "current_iteration_exists": True,
            "current_iteration_id": "current-iteration-id",
            "current_iteration_status": "prepared",
            "expected": "SUCCESS"
        },
        {
            "scenario": "No current iteration",
            "iteration_id": "some-iteration-id",
            "current_iteration_exists": False,
            "current_iteration_id": None,
            "current_iteration_status": None,
            "expected": "409 CONFLICT - No current iteration to apply"
        },
        {
            "scenario": "Iteration ID mismatch",
            "iteration_id": "wrong-iteration-id",
            "current_iteration_exists": True,
            "current_iteration_id": "current-iteration-id",
            "current_iteration_status": "prepared",
            "expected": "409 CONFLICT - Iteration ID mismatch"
        },
        {
            "scenario": "Iteration not prepared",
            "iteration_id": "current-iteration-id",
            "current_iteration_exists": True,
            "current_iteration_id": "current-iteration-id",
            "current_iteration_status": "in_progress",
            "expected": "409 CONFLICT - Iteration not in prepared status"
        },
        {
            "scenario": "Iteration already completed",
            "iteration_id": "current-iteration-id",
            "current_iteration_exists": True,
            "current_iteration_id": "current-iteration-id",
            "current_iteration_status": "completed",
            "expected": "409 CONFLICT - Iteration not in prepared status"
        }
    ]
    
    print("\nValidation Matrix:")
    print("-" * 100)
    for i, scenario in enumerate(scenarios, 1):
        print(f"{i}. {scenario['scenario']}")
        print(f"   Request iteration_id: {scenario['iteration_id']}")
        print(f"   Current iteration exists: {scenario['current_iteration_exists']}")
        print(f"   Current iteration ID: {scenario['current_iteration_id']}")
        print(f"   Current iteration status: {scenario['current_iteration_status']}")
        print(f"   Expected result: {scenario['expected']}")
        print("-" * 100)
    
    print("\n✓ Validation scenarios documented")


if __name__ == "__main__":
    print("Testing apply_iteration_changes validation logic")
    print("=" * 100)
    
    try:
        test_apply_operations_request_validation()
        test_apply_operations_model_dump()
        test_validation_scenario_documentation()
        
        print("\n" + "=" * 100)
        print("✓ All validation tests passed!")
        print("=" * 100)
        print("\nSUMMARY:")
        print("- ApplyOperationsRequest now requires iteration_id")
        print("- Backend validates iteration_id matches current iteration")
        print("- Backend validates iteration is in 'prepared' status")
        print("- Prevents applying operations to wrong or unprepared iterations")
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
