"""
Service for the project activity log: records what the user and the assistant did
and reads it back as a timeline.
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .domain import (
    ProjectActivityActor,
    ProjectActivityEvent,
    ProjectActivityEventType,
)
from .project_activity_store import ProjectActivityStore

logger = logging.getLogger(__name__)


# Event types that represent an explicit keep/reject decision on a single operation.
DECISION_EVENT_TYPES = (
    ProjectActivityEventType.OPERATION_APPROVED,
    ProjectActivityEventType.OPERATION_REJECTED,
)


class ProjectActivityService:
    """
    Records project activity events and exposes them as a newest-first timeline.
    """

    def __init__(self, store: ProjectActivityStore):
        self.store = store

    def record(
        self,
        project_id: str,
        type: ProjectActivityEventType,
        actor: ProjectActivityActor,
        summary: str,
        iteration_id: Optional[str] = None,
        task_id: Optional[str] = None,
        operation_id: Optional[str] = None,
        detail: Optional[Dict[str, Any]] = None,
    ) -> Optional[ProjectActivityEvent]:
        """
        Append an event to the project log.

        Returns the recorded event, or None if it could not be persisted. Activity
        logging is auxiliary, so a storage failure is logged and swallowed rather than
        propagated: it must never fail the user action that triggered it.
        """
        event = ProjectActivityEvent(
            id=str(uuid.uuid4()),
            project_id=project_id,
            type=type,
            actor=actor,
            summary=summary,
            at=datetime.now(timezone.utc).isoformat(),
            iteration_id=iteration_id,
            task_id=task_id,
            operation_id=operation_id,
            detail=detail or {},
        )

        try:
            self.store.append_event(event)
        except Exception as e:
            logger.warning(
                "Failed to record activity event %s for project %s: %s",
                type.value,
                project_id,
                e,
            )
            return None

        return event

    def list_events(
        self,
        project_id: str,
        types: Optional[List[ProjectActivityEventType]] = None,
        iteration_id: Optional[str] = None,
        task_id: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[ProjectActivityEvent]:
        """
        Return events newest first, optionally filtered by type, iteration or task.
        When limit is set, the most recent matching events are returned.
        """
        events = self.store.list_events(project_id)

        if types:
            wanted = set(types)
            events = [e for e in events if e.type in wanted]
        if iteration_id is not None:
            events = [e for e in events if e.iteration_id == iteration_id]
        if task_id is not None:
            events = [e for e in events if e.task_id == task_id]

        events.sort(key=lambda e: e.at, reverse=True)

        if limit is not None and limit >= 0:
            return events[:limit]
        return events

    def get_decision_counts(
        self,
        project_id: str,
        iteration_id: Optional[str] = None,
    ) -> Dict[str, int]:
        """
        Count keep/reject decisions, for the whole project or a single iteration.
        Used for the inline summaries shown next to iterations and operations.
        """
        events = self.list_events(
            project_id,
            types=list(DECISION_EVENT_TYPES),
            iteration_id=iteration_id,
        )

        approved = sum(1 for e in events if e.type == ProjectActivityEventType.OPERATION_APPROVED)
        rejected = sum(1 for e in events if e.type == ProjectActivityEventType.OPERATION_REJECTED)
        return {"approved": approved, "rejected": rejected}
