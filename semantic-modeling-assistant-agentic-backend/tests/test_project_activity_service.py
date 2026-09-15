"""Unit tests for the project activity log: recording, filtering and decision counts."""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from design_project.domain import ProjectActivityActor, ProjectActivityEventType
from design_project.project_activity_service import ProjectActivityService
from design_project.project_activity_store import (
    ACTIVITY_FILENAME,
    FileSystemProjectActivityStore,
)


def _service(tmp_dir: str) -> ProjectActivityService:
    return ProjectActivityService(FileSystemProjectActivityStore(base_dir=tmp_dir))


def test_empty_log_returns_no_events():
    with tempfile.TemporaryDirectory() as tmp_dir:
        service = _service(tmp_dir)
        assert service.list_events("project-without-activity") == []


def test_recorded_events_are_returned_newest_first():
    with tempfile.TemporaryDirectory() as tmp_dir:
        service = _service(tmp_dir)
        project_id = "p-timeline"

        service.record(
            project_id,
            ProjectActivityEventType.ITERATIONS_SUGGESTED,
            ProjectActivityActor.ASSISTANT,
            "Assistant suggested 3 iterations",
        )
        service.record(
            project_id,
            ProjectActivityEventType.ITERATION_APPLIED,
            ProjectActivityActor.USER,
            "You applied 9 operations",
            iteration_id="it-1",
        )

        events = service.list_events(project_id)
        assert len(events) == 2
        assert events[0].type == ProjectActivityEventType.ITERATION_APPLIED
        assert events[0].actor == ProjectActivityActor.USER
        assert events[0].iteration_id == "it-1"
        assert events[1].type == ProjectActivityEventType.ITERATIONS_SUGGESTED


def test_events_are_scoped_per_project():
    with tempfile.TemporaryDirectory() as tmp_dir:
        service = _service(tmp_dir)
        service.record(
            "p-a",
            ProjectActivityEventType.GUIDANCE_ADDED,
            ProjectActivityActor.USER,
            "You added guidance",
        )

        assert len(service.list_events("p-a")) == 1
        assert service.list_events("p-b") == []


def test_filter_by_type_iteration_and_limit():
    with tempfile.TemporaryDirectory() as tmp_dir:
        service = _service(tmp_dir)
        project_id = "p-filter"

        service.record(
            project_id,
            ProjectActivityEventType.OPERATION_APPROVED,
            ProjectActivityActor.USER,
            "kept A",
            iteration_id="it-1",
            task_id="t-1",
        )
        service.record(
            project_id,
            ProjectActivityEventType.OPERATION_REJECTED,
            ProjectActivityActor.USER,
            "rejected B",
            iteration_id="it-1",
            task_id="t-2",
        )
        service.record(
            project_id,
            ProjectActivityEventType.OPERATION_APPROVED,
            ProjectActivityActor.USER,
            "kept C",
            iteration_id="it-2",
        )

        rejected = service.list_events(
            project_id, types=[ProjectActivityEventType.OPERATION_REJECTED]
        )
        assert len(rejected) == 1
        assert rejected[0].summary == "rejected B"

        first_iteration = service.list_events(project_id, iteration_id="it-1")
        assert len(first_iteration) == 2

        by_task = service.list_events(project_id, task_id="t-2")
        assert len(by_task) == 1

        assert len(service.list_events(project_id, limit=2)) == 2
        assert len(service.list_events(project_id, limit=0)) == 0


def test_decision_counts_overall_and_per_iteration():
    with tempfile.TemporaryDirectory() as tmp_dir:
        service = _service(tmp_dir)
        project_id = "p-counts"

        for _ in range(3):
            service.record(
                project_id,
                ProjectActivityEventType.OPERATION_APPROVED,
                ProjectActivityActor.USER,
                "kept",
                iteration_id="it-1",
            )
        service.record(
            project_id,
            ProjectActivityEventType.OPERATION_REJECTED,
            ProjectActivityActor.USER,
            "rejected",
            iteration_id="it-1",
        )
        service.record(
            project_id,
            ProjectActivityEventType.OPERATION_APPROVED,
            ProjectActivityActor.USER,
            "kept",
            iteration_id="it-2",
        )
        # Non-decision events must not be counted.
        service.record(
            project_id,
            ProjectActivityEventType.GUIDANCE_ADDED,
            ProjectActivityActor.USER,
            "You added guidance",
            iteration_id="it-1",
        )

        assert service.get_decision_counts(project_id) == {"approved": 4, "rejected": 1}
        assert service.get_decision_counts(project_id, iteration_id="it-1") == {
            "approved": 3,
            "rejected": 1,
        }


def test_rejection_reason_is_preserved_in_detail():
    with tempfile.TemporaryDirectory() as tmp_dir:
        service = _service(tmp_dir)
        project_id = "p-detail"

        service.record(
            project_id,
            ProjectActivityEventType.OPERATION_REJECTED,
            ProjectActivityActor.USER,
            "You rejected is_connected_to",
            operation_id="op-7",
            detail={"reason": "must use prefix has", "savedAsGuidance": True},
        )

        event = service.list_events(project_id)[0]
        assert event.operation_id == "op-7"
        assert event.detail["reason"] == "must use prefix has"
        assert event.detail["savedAsGuidance"] is True


def test_log_is_append_only_on_disk():
    with tempfile.TemporaryDirectory() as tmp_dir:
        service = _service(tmp_dir)
        project_id = "p-append"

        service.record(
            project_id,
            ProjectActivityEventType.GUIDANCE_ADDED,
            ProjectActivityActor.USER,
            "first",
        )
        path = os.path.join(tmp_dir, project_id, ACTIVITY_FILENAME)
        with open(path, "r", encoding="utf-8") as f:
            after_first = f.read()

        service.record(
            project_id,
            ProjectActivityEventType.GUIDANCE_DELETED,
            ProjectActivityActor.USER,
            "second",
        )
        with open(path, "r", encoding="utf-8") as f:
            after_second = f.read()

        assert after_second.startswith(after_first)
        assert len(after_second.strip().splitlines()) == 2


def test_unknown_event_type_does_not_break_the_log():
    with tempfile.TemporaryDirectory() as tmp_dir:
        service = _service(tmp_dir)
        project_id = "p-forward-compat"

        service.record(
            project_id,
            ProjectActivityEventType.GUIDANCE_ADDED,
            ProjectActivityActor.USER,
            "known event",
        )

        path = os.path.join(tmp_dir, project_id, ACTIVITY_FILENAME)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "id": "x",
                "projectId": project_id,
                "type": "event_from_a_future_version",
                "actor": "user",
                "summary": "unknown",
                "at": "2026-01-01T00:00:00+00:00",
            }) + "\n")

        events = service.list_events(project_id)
        assert len(events) == 1
        assert events[0].summary == "known event"
