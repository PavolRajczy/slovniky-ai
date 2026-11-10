"""Progress reporting while a knowledge document is loaded, summarized and indexed."""
from typing import List, Optional, Tuple
from unittest.mock import patch

from knowledge_base.document_summarizers.document_summarizer_simple_openai import SimpleOpenAIKnowledgeDocumentSummarizer
from knowledge_base.domain import KnowledgeDocument, KnowledgeDocumentElement
from knowledge_base.processing_progress import (
    DocumentProcessingJobRegistry,
    DocumentProcessingStage,
    ProcessingProgressListener,
)
from knowledge_base.store import KnowledgeStore
from fakes import FakeKnowledgeDocumentLoader, FakeKnowledgeDocumentSummarizer


class RecordingProgress(ProcessingProgressListener):
    def __init__(self):
        self.stages: List[Tuple[DocumentProcessingStage, Optional[int]]] = []
        self.steps = 0

    def start_stage(self, stage: DocumentProcessingStage, total: Optional[int] = None) -> None:
        self.stages.append((stage, total))

    def advance(self, steps: int = 1) -> None:
        self.steps += steps


def element(element_id: str, summary: Optional[str] = None, children: Optional[List[KnowledgeDocumentElement]] = None) -> KnowledgeDocumentElement:
    return KnowledgeDocumentElement(id=element_id, title=element_id, content=f"Content of {element_id}", contentSummary=summary, childElements=children or [])


def document_with_sections(children: List[KnowledgeDocumentElement]) -> KnowledgeDocument:
    return KnowledgeDocument(id="doc", title="Doc", content=None, contentSummary=None, childElements=children)


def create_summarizer() -> SimpleOpenAIKnowledgeDocumentSummarizer:
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key", "SUMMARIZE_ONLY_ELEMENT_ID_CONTAINS": ""}):
        return SimpleOpenAIKnowledgeDocumentSummarizer(model="fake")


def test_job_reports_stage_counts_and_resets_them_for_each_stage():
    job = DocumentProcessingJobRegistry().create("project-1", "legal", "act 2001/56")

    job.start_stage(DocumentProcessingStage.SUMMARIZING, total=3)
    job.advance()
    job.advance()
    summarizing = job.snapshot()
    job.start_stage(DocumentProcessingStage.INDEXING)
    indexing = job.snapshot()

    assert (summarizing.stage, summarizing.completed, summarizing.total) == (DocumentProcessingStage.SUMMARIZING, 2, 3)
    assert (indexing.stage, indexing.completed, indexing.total) == (DocumentProcessingStage.INDEXING, 0, None)


def test_job_never_reports_more_completed_units_than_the_stage_total():
    job = DocumentProcessingJobRegistry().create("project-1", "legal", "act")

    job.start_stage(DocumentProcessingStage.INDEXING, total=2)
    job.advance(5)

    assert job.snapshot().completed == 2


def test_completed_and_failed_jobs_are_finished():
    registry = DocumentProcessingJobRegistry()
    completed_job = registry.create("project-1", "expert", "a.pdf")
    failed_job = registry.create("project-1", "expert", "b.pdf")

    completed_job.complete("Added a.pdf.")
    failed_job.fail("Could not read b.pdf.")

    completed = completed_job.snapshot()
    failed = failed_job.snapshot()
    assert (completed.stage, completed.message, completed.finished_at is not None) == (DocumentProcessingStage.COMPLETED, "Added a.pdf.", True)
    assert (failed.stage, failed.error, failed.finished_at is not None) == (DocumentProcessingStage.FAILED, "Could not read b.pdf.", True)


def test_failed_job_remembers_the_stage_that_was_running():
    job = DocumentProcessingJobRegistry().create("project-1", "legal", "act")

    job.start_stage(DocumentProcessingStage.SUMMARIZING, total=10)
    job.fail("LLM unavailable")

    assert job.snapshot().failed_stage == DocumentProcessingStage.SUMMARIZING


def test_registry_returns_a_job_only_for_its_own_project():
    registry = DocumentProcessingJobRegistry()
    job = registry.create("project-1", "legal", "act")

    assert registry.get("project-1", job.id) is job
    assert registry.get("project-2", job.id) is None
    assert registry.get("project-1", "unknown") is None


def test_summarizer_reports_one_step_per_element_without_summary():
    document = document_with_sections([
        element("part-1", children=[element("section-1"), element("section-2")]),
        element("part-2", summary="Already summarized", children=[element("section-3")]),
    ])
    summarizer = create_summarizer()
    progress = RecordingProgress()

    with patch.object(summarizer, "_summarize_text", return_value="Summary"):
        summarizer.summarize_document(document, progress)

    assert progress.stages == [(DocumentProcessingStage.SUMMARIZING, 4)]
    assert progress.steps == 4


def test_summarizer_counts_failed_summaries_as_processed():
    document = document_with_sections([element("section-1"), element("section-2")])
    summarizer = create_summarizer()
    progress = RecordingProgress()

    with patch.object(summarizer, "_summarize_text", side_effect=RuntimeError("LLM unavailable")):
        summarizer.summarize_document(document, progress)

    assert progress.stages == [(DocumentProcessingStage.SUMMARIZING, 3)]
    assert progress.steps == 3


def test_store_reports_loading_before_summarizing():
    progress = RecordingProgress()

    KnowledgeStore().load_documents(["doc-1"], FakeKnowledgeDocumentLoader(), FakeKnowledgeDocumentSummarizer(), progress)

    assert progress.stages == [(DocumentProcessingStage.LOADING, None)]
