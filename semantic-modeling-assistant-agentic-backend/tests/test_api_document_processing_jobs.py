"""Background jobs that add a document to the project knowledge base and report their progress."""
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.controllers.design_project_controller import router
from knowledge_base.domain import KnowledgeDocument
from knowledge_base.processing_progress import DocumentProcessingStage

app = FastAPI()
app.include_router(router)
client = TestClient(app)

PROJECT_ID = "project-1"
LEGAL_ACT_URL = "https://opendata.eselpoint.gov.cz/esel-esb/eli/cz/sb/2001/56/2025-07-01"
CONTROLLER = "api.controllers.design_project_controller"


def legal_document() -> KnowledgeDocument:
    return KnowledgeDocument(id=LEGAL_ACT_URL, title="Act 56/2001", content=None, contentSummary=None)


def empty_project() -> SimpleNamespace:
    return SimpleNamespace(id=PROJECT_ID, legalKnowledgeBase=[], expertKnowledgeBase=[])


def summarize_in_three_steps(document_ids, progress):
    progress.start_stage(DocumentProcessingStage.LOADING)
    progress.start_stage(DocumentProcessingStage.SUMMARIZING, total=3)
    progress.advance(3)
    return [legal_document()]


def start_legal_job() -> dict:
    response = client.post(f"/projects/{PROJECT_ID}/knowledge-base/legal/jobs", json={"document_ids": [LEGAL_ACT_URL]})
    assert response.status_code == 202
    return response.json()


def get_job(job_id: str) -> dict:
    response = client.get(f"/projects/{PROJECT_ID}/knowledge-base/jobs/{job_id}")
    assert response.status_code == 200
    return response.json()


@patch(f"{CONTROLLER}.knowledge_base_index_service")
@patch(f"{CONTROLLER}.knowledge_base_service")
@patch(f"{CONTROLLER}.design_project_service")
def test_legal_document_job_completes_and_attaches_the_document(project_service, knowledge_service, index_service):
    project_service.load_project.return_value = empty_project()
    knowledge_service.load_legal_knowledge_documents.side_effect = summarize_in_three_steps

    started = start_legal_job()
    finished = get_job(started["id"])

    assert started["document_label"] == "act 2001/56/2025-07-01"
    assert finished["stage"] == "completed"
    assert finished["finished_at"] is not None
    project = project_service.load_project.return_value
    assert [doc.id for doc in project.legalKnowledgeBase] == [LEGAL_ACT_URL]
    project_service.save_project.assert_called_once_with(project)


@patch(f"{CONTROLLER}.knowledge_base_index_service")
@patch(f"{CONTROLLER}.knowledge_base_service")
@patch(f"{CONTROLLER}.design_project_service")
def test_legal_document_job_fails_when_the_document_cannot_be_loaded(project_service, knowledge_service, index_service):
    project_service.load_project.return_value = empty_project()
    knowledge_service.load_legal_knowledge_documents.return_value = []

    finished = get_job(start_legal_job()["id"])

    assert finished["stage"] == "failed"
    assert "could not be loaded" in finished["error"]
    project_service.save_project.assert_not_called()


@patch(f"{CONTROLLER}.knowledge_base_index_service")
@patch(f"{CONTROLLER}.knowledge_base_service")
@patch(f"{CONTROLLER}.design_project_service")
def test_legal_document_job_reports_the_processing_error(project_service, knowledge_service, index_service):
    project_service.load_project.return_value = empty_project()
    knowledge_service.load_legal_knowledge_documents.side_effect = RuntimeError("e-Sbirka is unavailable")

    finished = get_job(start_legal_job()["id"])

    assert finished["stage"] == "failed"
    assert finished["error"] == "e-Sbirka is unavailable"


@patch(f"{CONTROLLER}.design_project_service")
def test_legal_document_job_rejects_an_invalid_address(project_service):
    response = client.post(f"/projects/{PROJECT_ID}/knowledge-base/legal/jobs", json={"document_ids": ["https://example.org/law"]})

    assert response.status_code == 400


@patch(f"{CONTROLLER}.design_project_service")
def test_legal_document_job_returns_404_for_an_unknown_project(project_service):
    project_service.load_project.side_effect = FileNotFoundError()

    response = client.post(f"/projects/{PROJECT_ID}/knowledge-base/legal/jobs", json={"document_ids": [LEGAL_ACT_URL]})

    assert response.status_code == 404


def test_unknown_job_returns_404():
    response = client.get(f"/projects/{PROJECT_ID}/knowledge-base/jobs/unknown-job")

    assert response.status_code == 404
