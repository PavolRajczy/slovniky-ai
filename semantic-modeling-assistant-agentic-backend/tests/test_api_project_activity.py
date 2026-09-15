"""API-level tests for the project activity endpoints."""
import os
import sys
import tempfile

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from api.controllers import design_project_controller as controller
from design_project.project_activity_service import ProjectActivityService
from design_project.project_activity_store import FileSystemProjectActivityStore

PROJECT_ID = "project-activity-api"


@pytest.fixture
def client(monkeypatch):
    """
    Test client with the activity log redirected to a temporary directory and
    project loading stubbed out, so the endpoints can be exercised in isolation.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        monkeypatch.setattr(
            controller,
            "activity_service",
            ProjectActivityService(FileSystemProjectActivityStore(base_dir=tmp_dir)),
        )
        monkeypatch.setattr(
            controller.design_project_service,
            "load_project",
            lambda project_id: None,
        )

        app = FastAPI()
        app.include_router(controller.router, prefix="/api")
        yield TestClient(app)


def test_activity_is_empty_for_a_fresh_project(client):
    response = client.get(f"/api/projects/{PROJECT_ID}/activity")

    assert response.status_code == 200
    body = response.json()
    assert body["events"] == []
    assert body["approved_count"] == 0
    assert body["rejected_count"] == 0


def test_recorded_decisions_appear_in_the_timeline(client):
    response = client.post(
        f"/api/projects/{PROJECT_ID}/activity/decisions",
        json={
            "iteration_id": "it-1",
            "task_id": "t-1",
            "task_name": "Identifiers",
            "approved": [{"operation_id": "op-1", "label": "create class Legal document"}],
            "rejected": [
                {
                    "operation_id": "op-2",
                    "label": "create relationship is_connected_to",
                    "reason": "must use prefix has",
                    "saved_as_guidance": True,
                }
            ],
        },
    )

    assert response.status_code == 201
    created = response.json()
    assert created["approved_count"] == 1
    assert created["rejected_count"] == 1

    timeline = client.get(f"/api/projects/{PROJECT_ID}/activity").json()
    assert len(timeline["events"]) == 2

    rejected = next(e for e in timeline["events"] if e["type"] == "operation_rejected")
    assert rejected["actor"] == "user"
    assert rejected["operation_id"] == "op-2"
    assert rejected["iteration_id"] == "it-1"
    assert rejected["detail"]["reason"] == "must use prefix has"
    assert rejected["detail"]["savedAsGuidance"] is True
    assert rejected["detail"]["taskName"] == "Identifiers"


def test_timeline_can_be_filtered_by_type_and_iteration(client):
    client.post(
        f"/api/projects/{PROJECT_ID}/activity/decisions",
        json={
            "iteration_id": "it-1",
            "approved": [{"label": "kept A"}],
            "rejected": [{"label": "rejected B"}],
        },
    )
    client.post(
        f"/api/projects/{PROJECT_ID}/activity/decisions",
        json={
            "iteration_id": "it-2",
            "approved": [{"label": "kept C"}],
        },
    )

    only_rejected = client.get(
        f"/api/projects/{PROJECT_ID}/activity", params={"type": "operation_rejected"}
    ).json()
    assert len(only_rejected["events"]) == 1
    assert only_rejected["events"][0]["summary"] == "Rejected rejected B"

    second_iteration = client.get(
        f"/api/projects/{PROJECT_ID}/activity", params={"iteration_id": "it-2"}
    ).json()
    assert len(second_iteration["events"]) == 1
    # Counts follow the same filter, so they describe the selected iteration only.
    assert second_iteration["approved_count"] == 1
    assert second_iteration["rejected_count"] == 0

    limited = client.get(f"/api/projects/{PROJECT_ID}/activity", params={"limit": 1}).json()
    assert len(limited["events"]) == 1


def test_unknown_event_type_filter_is_rejected(client):
    response = client.get(
        f"/api/projects/{PROJECT_ID}/activity", params={"type": "not_a_real_event"}
    )

    assert response.status_code == 400
