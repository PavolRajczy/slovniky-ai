"""Editing prepared changes while another work item is being prepared waits instead of failing."""
import tempfile
import threading

from test_prepare_does_not_apply_until_finalize import RecordingModeler, _make_service, _seed_project


class BlockingModeler(RecordingModeler):
    def __init__(self, blocked_task_id: str):
        super().__init__()
        self.blocked_task_id = blocked_task_id
        self.started = threading.Event()
        self.release = threading.Event()

    def get_operations_for_design_task(self, design_project, current_ontology, iteration, task, project_guidance_text=None):
        if task.id == self.blocked_task_id:
            self.started.set()
            self.release.wait(timeout=5)
        return super().get_operations_for_design_task(design_project, current_ontology, iteration, task, project_guidance_text)


def test_deleting_a_change_waits_for_the_running_prepare():
    with tempfile.TemporaryDirectory() as tmp_dir:
        modeler = BlockingModeler(blocked_task_id="t-2")
        service = _make_service(tmp_dir, modeler)
        project = _seed_project(service, ["t-1", "t-2"])
        [first_change] = service.prepare_planned_iteration_task(project.id, "it-1", "t-1")

        preparing = threading.Thread(target=service.prepare_planned_iteration_task, args=(project.id, "it-1", "t-2"))
        preparing.start()
        assert modeler.started.wait(timeout=5)

        errors = []

        def delete_first_change():
            try:
                service.delete_iteration_operation(project_id=project.id, iteration_id="it-1", operation_id=first_change.id)
            except Exception as error:
                errors.append(error)

        deleting = threading.Thread(target=delete_first_change)
        deleting.start()
        deleting.join(timeout=0.3)
        deleted_before_prepare_finished = not deleting.is_alive()

        modeler.release.set()
        preparing.join(timeout=5)
        deleting.join(timeout=5)

        assert deleted_before_prepare_finished is False
        assert errors == []
        remaining = service.store.load_project(project.id).currentIteration.plannedOperations
        assert [change.created_from_task_id for change in remaining] == ["t-2"]
