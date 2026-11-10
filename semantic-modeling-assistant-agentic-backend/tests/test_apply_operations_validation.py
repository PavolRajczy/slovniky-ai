"""
Unit tests for the request model of the apply-iteration-changes endpoint.

The iteration ID is part of the URL (/projects/{project_id}/iterations/{iteration_id}/apply),
so the request body carries only the operations to apply.
"""
import pytest
from pydantic import ValidationError

from api.models import ApplyOperationsRequest, OntologyOperationModel


def _create_person_class(operation_id: str = "op-1") -> OntologyOperationModel:
    return OntologyOperationModel(
        id=operation_id,
        operation_type="create",
        target_type="class",
        uri="http://example.org/Person",
        label="Person",
    )


def test_apply_operations_request_accepts_explicit_operations():
    request = ApplyOperationsRequest(operations=[_create_person_class()])

    assert len(request.operations) == 1
    assert request.operations[0].id == "op-1"


def test_apply_operations_request_without_operations_uses_persisted_ones():
    request = ApplyOperationsRequest()

    assert request.operations is None


def test_operation_model_requires_id():
    with pytest.raises(ValidationError):
        OntologyOperationModel(
            operation_type="create",
            target_type="class",
            uri="http://example.org/Person",
            label="Person",
        )


def test_operation_model_rejects_unknown_operation_type():
    with pytest.raises(ValidationError):
        OntologyOperationModel(
            id="op-1",
            operation_type="rename",
            target_type="class",
            uri="http://example.org/Person",
        )


def test_apply_operations_model_dump():
    request = ApplyOperationsRequest(
        operations=[
            OntologyOperationModel(
                id="op-1",
                operation_type="create",
                target_type="class",
                uri="http://example.org/Person",
                label="Person",
                kind="subject",
            ),
            OntologyOperationModel(
                id="op-2",
                operation_type="update",
                target_type="attribute",
                uri="http://example.org/age",
                label="Age",
                owning_class_uri="http://example.org/Person",
            ),
        ]
    )

    dumped = request.model_dump()

    assert [operation["id"] for operation in dumped["operations"]] == ["op-1", "op-2"]
    assert dumped["operations"][0]["operation_type"] == "create"
    assert dumped["operations"][1]["operation_type"] == "update"
    assert dumped["operations"][1]["owning_class_uri"] == "http://example.org/Person"
