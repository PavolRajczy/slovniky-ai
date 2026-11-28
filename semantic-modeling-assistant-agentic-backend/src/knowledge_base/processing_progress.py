import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Optional


class DocumentProcessingStage(str, Enum):
    QUEUED = "queued"
    LOADING = "loading"
    SUMMARIZING = "summarizing"
    INDEXING = "indexing"
    SAVING = "saving"
    COMPLETED = "completed"
    FAILED = "failed"


class ProcessingProgressListener:
    """
    Receives progress of a long-running document processing pipeline (load, summarize, index).

    A stage with an unknown amount of work is started with total=None.
    """

    def start_stage(self, stage: DocumentProcessingStage, total: Optional[int] = None) -> None:
        """Enter a new stage. Resets the completed count of the stage."""
        ...

    def advance(self, steps: int = 1) -> None:
        """Mark the given number of units of the current stage as done."""
        ...


class NullProgressListener(ProcessingProgressListener):
    def start_stage(self, stage: DocumentProcessingStage, total: Optional[int] = None) -> None:
        pass

    def advance(self, steps: int = 1) -> None:
        pass


NULL_PROGRESS = NullProgressListener()


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class DocumentProcessingSnapshot:
    id: str
    project_id: str
    document_kind: str
    document_label: str
    stage: DocumentProcessingStage
    completed: int
    total: Optional[int]
    message: Optional[str]
    error: Optional[str]
    failed_stage: Optional[DocumentProcessingStage]
    started_at: datetime
    updated_at: datetime
    finished_at: Optional[datetime]


@dataclass
class DocumentProcessingJob(ProcessingProgressListener):
    """Progress of adding one document to a project, shared between the worker thread and status requests."""

    project_id: str
    document_kind: str
    document_label: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    stage: DocumentProcessingStage = DocumentProcessingStage.QUEUED
    completed: int = 0
    total: Optional[int] = None
    message: Optional[str] = None
    error: Optional[str] = None
    failed_stage: Optional[DocumentProcessingStage] = None
    started_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)
    finished_at: Optional[datetime] = None
    lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def start_stage(self, stage: DocumentProcessingStage, total: Optional[int] = None) -> None:
        with self.lock:
            self.stage = stage
            self.completed = 0
            self.total = total
            self.updated_at = _now()

    def advance(self, steps: int = 1) -> None:
        with self.lock:
            self.completed += steps
            if self.total is not None:
                self.completed = min(self.completed, self.total)
            self.updated_at = _now()

    def complete(self, message: str) -> None:
        self._finish(DocumentProcessingStage.COMPLETED, message=message, error=None)

    def fail(self, error: str) -> None:
        self._finish(DocumentProcessingStage.FAILED, message=None, error=error)

    def snapshot(self) -> DocumentProcessingSnapshot:
        with self.lock:
            return DocumentProcessingSnapshot(
                id=self.id,
                project_id=self.project_id,
                document_kind=self.document_kind,
                document_label=self.document_label,
                stage=self.stage,
                completed=self.completed,
                total=self.total,
                message=self.message,
                error=self.error,
                failed_stage=self.failed_stage,
                started_at=self.started_at,
                updated_at=self.updated_at,
                finished_at=self.finished_at,
            )

    def _finish(self, stage: DocumentProcessingStage, message: Optional[str], error: Optional[str]) -> None:
        with self.lock:
            if stage == DocumentProcessingStage.FAILED:
                self.failed_stage = self.stage
            self.stage = stage
            self.message = message
            self.error = error
            self.finished_at = _now()
            self.updated_at = self.finished_at


class DocumentProcessingJobRegistry:
    """In-memory registry of document processing jobs. Jobs are lost when the server restarts."""

    def __init__(self):
        self.jobs: Dict[str, DocumentProcessingJob] = {}
        self.lock = threading.Lock()

    def create(self, project_id: str, document_kind: str, document_label: str) -> DocumentProcessingJob:
        job = DocumentProcessingJob(project_id=project_id, document_kind=document_kind, document_label=document_label)
        with self.lock:
            self.jobs[job.id] = job
        return job

    def get(self, project_id: str, job_id: str) -> Optional[DocumentProcessingJob]:
        with self.lock:
            job = self.jobs.get(job_id)
        if job is None or job.project_id != project_id:
            return None
        return job
