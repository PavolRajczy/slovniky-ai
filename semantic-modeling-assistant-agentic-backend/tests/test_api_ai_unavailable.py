"""AI endpoints report an unresponsive model and never hold up the rest of the backend."""
import asyncio
import threading
from types import SimpleNamespace
from unittest.mock import patch

import httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.controllers.design_project_controller import router
from knowledge_base.domain import KnowledgeDocument
from llm.provider import AIServiceUnavailableError

app = FastAPI()
app.include_router(router)
client = TestClient(app)

PROJECT_ID = "project-1"
PLAN_TASKS_URL = f"/projects/{PROJECT_ID}/iterations/iteration-1/tasks/plan"
CONTROLLER = "api.controllers.design_project_controller"


def project(*legal_documents: KnowledgeDocument) -> SimpleNamespace:
    return SimpleNamespace(id=PROJECT_ID, legalKnowledgeBase=list(legal_documents), expertKnowledgeBase=[])


def unavailable(model_name: str) -> AIServiceUnavailableError:
    return AIServiceUnavailableError(model_name, TimeoutError("Request timed out."))


@patch(f"{CONTROLLER}.activity_service")
@patch(f"{CONTROLLER}.design_project_service")
def test_planning_reports_an_unresponsive_chat_model(project_service, activity_service):
    project_service.load_project.return_value = project()
    project_service.initialize_iteration_tasks.side_effect = unavailable("mini")

    response = client.post(PLAN_TASKS_URL, json={})

    assert response.status_code == 503
    assert "'mini' did not respond after 3 attempts" in response.json()["detail"]


@patch(f"{CONTROLLER}.knowledge_base_index_service")
@patch(f"{CONTROLLER}.activity_service")
@patch(f"{CONTROLLER}.design_project_service")
def test_planning_reports_an_unresponsive_embedding_model(project_service, activity_service, index_service):
    project_service.load_project.return_value = project(KnowledgeDocument(id="doc", title="Doc", content=None, contentSummary=None))
    index_service.has_document.return_value = False
    index_service.add_document.side_effect = unavailable("nemotron-3-5-embed-8b")

    response = client.post(PLAN_TASKS_URL, json={})

    assert response.status_code == 503
    assert "'nemotron-3-5-embed-8b' did not respond" in response.json()["detail"]
    project_service.initialize_iteration_tasks.assert_not_called()


@patch(f"{CONTROLLER}.activity_service")
@patch(f"{CONTROLLER}.design_project_service")
def test_a_slow_ai_call_does_not_block_other_requests(project_service, activity_service):
    project_service.load_project.return_value = project()
    model_answered = threading.Event()

    def wait_for_the_model(**kwargs):
        model_answered.wait(timeout=5)
        return []

    project_service.initialize_iteration_tasks.side_effect = wait_for_the_model

    async def plan_while_polling():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as http:
            planning = asyncio.create_task(http.post(PLAN_TASKS_URL, json={}))
            await asyncio.sleep(0.2)
            polling = await asyncio.wait_for(http.get(f"/projects/{PROJECT_ID}/knowledge-base/jobs/unknown-job"), timeout=2)
            planning_was_pending = not planning.done()
            model_answered.set()
            return polling.status_code, planning_was_pending, (await planning).status_code

    assert asyncio.run(plan_while_polling()) == (404, True, 200)
