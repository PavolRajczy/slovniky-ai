"""A work item whose preparation fails must not hide changes prepared for other work items."""
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from agents.modelers.modeler import OperationGenerationError
from design_project.domain import DesignIterationStatus, DesignTaskStatus
from test_prepare_does_not_apply_until_finalize import RecordingModeler, _make_service, _seed_project


class FailingSecondTaskModeler(RecordingModeler):
    def get_operations_for_design_task(
        self, design_project, current_ontology, iteration, task, project_guidance_text=None
    ):
        if task.id == "t-2":
            raise OperationGenerationError(task.name, ValueError("invalid tool call"))
        return super().get_operations_for_design_task(
            design_project, current_ontology, iteration, task, project_guidance_text
        )


def test_failed_task_returns_to_prepare_and_keeps_other_changes_ready():
    with tempfile.TemporaryDirectory() as tmp_dir:
        service = _make_service(tmp_dir, FailingSecondTaskModeler())
        project = _seed_project(service, ["t-1", "t-2"])

        service.prepare_planned_iteration_task(project.id, "it-1", "t-1")
        with pytest.raises(OperationGenerationError):
            service.prepare_planned_iteration_task(project.id, "it-1", "t-2")

        iteration = service.store.load_project(project.id).currentIteration
        by_id = {task.id: task for task in iteration.plannedTasks}
        assert by_id["t-1"].status == DesignTaskStatus.OPERATIONS_GENERATED
        assert by_id["t-2"].status == DesignTaskStatus.PLANNED
        assert iteration.status == DesignIterationStatus.OPERATIONS_GENERATED
        assert len(iteration.plannedOperations) == 1


def test_failed_only_task_leaves_direction_ready_to_prepare():
    with tempfile.TemporaryDirectory() as tmp_dir:
        service = _make_service(tmp_dir, FailingSecondTaskModeler())
        project = _seed_project(service, ["t-2"])

        with pytest.raises(OperationGenerationError):
            service.prepare_planned_iteration_task(project.id, "it-1", "t-2")

        iteration = service.store.load_project(project.id).currentIteration
        assert iteration.plannedTasks[0].status == DesignTaskStatus.PLANNED
        assert iteration.status == DesignIterationStatus.TASKS_PLANNED
