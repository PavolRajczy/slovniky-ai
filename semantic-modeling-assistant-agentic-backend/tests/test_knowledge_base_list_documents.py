"""
Unit tests for listing knowledge base documents.
"""
import json
from pathlib import Path

from knowledge_base.service import KnowledgeBaseService

from fakes import FakeKnowledgeDocumentLoader, FakeKnowledgeDocumentSummarizer


def create_service() -> KnowledgeBaseService:
    return KnowledgeBaseService(
        legal_knowledge_document_loader=FakeKnowledgeDocumentLoader(),
        expert_knowledge_document_loader=FakeKnowledgeDocumentLoader(),
        document_summarizer=FakeKnowledgeDocumentSummarizer(),
    )


def write_content_file(path: Path, document_id: str, title: str, element_type: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({
            "id": document_id,
            "title": title,
            "content": f"Full content of {title}",
            "contentSummary": f"Summary of {title}",
            "elementType": element_type,
            "childElements": [],
        }, ensure_ascii=False),
        encoding="utf-8",
    )


def test_list_legal_documents(tmp_path):
    """Every *.content.json file under the directory is listed with its summary fields."""
    esel_dir = tmp_path / "esel"
    write_content_file(esel_dir / "2001-56.content.json", "leg:2001-56", "Zákon o podmínkách provozu vozidel", "LegalAct")
    write_content_file(esel_dir / "nested" / "1999-13.content.json", "leg:1999-13", "Zákon o pozemních komunikacích", "LegalAct")
    (esel_dir / "2001-56.summary.json").write_text("{}", encoding="utf-8")

    documents = create_service().list_legal_knowledge_documents(base_dir=str(esel_dir))

    assert sorted(documents, key=lambda doc: doc["id"]) == [
        {
            "id": "leg:1999-13",
            "title": "Zákon o pozemních komunikacích",
            "contentSummary": "Summary of Zákon o pozemních komunikacích",
            "elementType": "LegalAct",
        },
        {
            "id": "leg:2001-56",
            "title": "Zákon o podmínkách provozu vozidel",
            "contentSummary": "Summary of Zákon o podmínkách provozu vozidel",
            "elementType": "LegalAct",
        },
    ]


def test_list_expert_documents(tmp_path):
    """Expert documents are listed from their own directory."""
    local_dir = tmp_path / "local"
    write_content_file(local_dir / "vehicles.content.json", "exp:vehicles", "Vehicles", "ExpertDocument")

    documents = create_service().list_expert_knowledge_documents(base_dir=str(local_dir))

    assert [doc["id"] for doc in documents] == ["exp:vehicles"]
    assert documents[0]["elementType"] == "ExpertDocument"


def test_list_documents_skips_unreadable_files(tmp_path):
    """A malformed content file is skipped instead of failing the whole listing."""
    local_dir = tmp_path / "local"
    write_content_file(local_dir / "vehicles.content.json", "exp:vehicles", "Vehicles", "ExpertDocument")
    (local_dir / "broken.content.json").write_text("{not json", encoding="utf-8")

    documents = create_service().list_expert_knowledge_documents(base_dir=str(local_dir))

    assert [doc["id"] for doc in documents] == ["exp:vehicles"]


def test_list_documents_empty_directory(tmp_path):
    """A non-existent directory yields an empty list rather than an error."""
    documents = create_service().list_legal_knowledge_documents(base_dir=str(tmp_path / "nonexistent"))

    assert documents == []
