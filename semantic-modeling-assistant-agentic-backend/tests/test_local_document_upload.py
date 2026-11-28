"""Uploaded PDF and DOCX files become local knowledge-document IDs."""
import os
import sys

import pytest
from unittest.mock import Mock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from docling.datamodel.base_models import InputFormat

from knowledge_base.domain import KnowledgeDocument
from knowledge_base.document_loaders.document_loader_local import LocalKnowledgeDocumentLoader
from knowledge_base.service import KnowledgeBaseService


def test_pdf_conversion_does_not_use_ocr(tmp_path):
    loader = LocalKnowledgeDocumentLoader(base_dir=str(tmp_path))
    pdf_options = loader.converter.format_to_options[InputFormat.PDF].pipeline_options

    assert pdf_options.do_ocr is False


def test_pdf_is_stored_under_its_document_id(tmp_path):
    loader = LocalKnowledgeDocumentLoader(base_dir=str(tmp_path))
    document_id = loader.store_uploaded_file("navod.pdf", b"%PDF-1.4")

    assert document_id == "https://localhost/navod.pdf"
    assert (tmp_path / "navod" / "navod.pdf").read_bytes() == b"%PDF-1.4"


def test_same_bytes_keep_the_conversion_cache(tmp_path):
    loader = LocalKnowledgeDocumentLoader(base_dir=str(tmp_path))
    loader.store_uploaded_file("navod.pdf", b"%PDF-1.4")
    cached = tmp_path / "navod" / "navod.md"
    cached.write_text("old", encoding="utf-8")
    index = tmp_path / "navod" / "indexes" / "faiss_summary_openai" / "faiss.index"
    index.parent.mkdir(parents=True)
    index.write_bytes(b"index")

    loader.store_uploaded_file("navod.pdf", b"%PDF-1.4")

    assert cached.read_text(encoding="utf-8") == "old"
    assert index.read_bytes() == b"index"


def test_replacing_a_file_drops_the_previous_conversion(tmp_path):
    loader = LocalKnowledgeDocumentLoader(base_dir=str(tmp_path))
    loader.store_uploaded_file("navod.pdf", b"%PDF-1.4")
    cached = tmp_path / "navod" / "navod.md"
    cached.write_text("old", encoding="utf-8")
    index = tmp_path / "navod" / "indexes" / "faiss_summary_openai" / "faiss.index"
    index.parent.mkdir(parents=True)
    index.write_bytes(b"index")

    loader.store_uploaded_file("navod.pdf", b"%PDF-new")

    assert not cached.exists()
    assert not index.exists()
    assert (tmp_path / "navod" / "navod.pdf").read_bytes() == b"%PDF-new"


def test_only_pdf_and_docx_are_accepted(tmp_path):
    loader = LocalKnowledgeDocumentLoader(base_dir=str(tmp_path))

    with pytest.raises(ValueError, match="PDF or DOCX"):
        loader.store_uploaded_file("notes.txt", b"hello")


def test_expert_load_skips_summarizer_when_summary_index_exists(tmp_path):
    document = KnowledgeDocument(
        id="https://localhost/navod.pdf",
        title="navod",
        content="text",
        contentSummary=None,
        cacheFilePath=str(tmp_path / "navod"),
    )
    index = tmp_path / "indexes" / "faiss_summary_openai" / "faiss.index"
    index.parent.mkdir(parents=True)
    index.write_bytes(b"index")

    class Loader:
        def load_document(self, document_id):
            assert document_id == document.id
            return document

    summarizer = Mock()
    service = KnowledgeBaseService(Loader(), Loader(), summarizer)

    loaded = service.load_expert_knowledge_documents([document.id])

    assert loaded == [document]
    summarizer.summarize_document.assert_not_called()


def test_directory_names_are_rejected(tmp_path):
    loader = LocalKnowledgeDocumentLoader(base_dir=str(tmp_path))

    with pytest.raises(ValueError, match="without a directory"):
        loader.store_uploaded_file("../secret.pdf", b"%PDF")
