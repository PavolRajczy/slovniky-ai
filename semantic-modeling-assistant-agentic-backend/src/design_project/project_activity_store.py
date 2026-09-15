"""
Append-only store for the project activity log.
Persists to data/projects/{project_id}/events.jsonl, one JSON object per line.
"""
import json
import os
from typing import Any, Dict, List, Optional

from .domain import (
    ProjectActivityActor,
    ProjectActivityEvent,
    ProjectActivityEventType,
)


ACTIVITY_FILENAME = "events.jsonl"


class ProjectActivityStore:
    """Abstract append-only store for project activity events."""

    def append_event(self, event: ProjectActivityEvent) -> None:
        """Append a single event to the project log."""
        ...

    def list_events(self, project_id: str) -> List[ProjectActivityEvent]:
        """Load all events for a project, oldest first."""
        ...


class FileSystemProjectActivityStore(ProjectActivityStore):
    """
    Stores activity events in data/projects/{project_id}/events.jsonl.

    JSON Lines is used instead of a single JSON document so that appending an event
    never requires rewriting earlier entries, which keeps the log genuinely append-only.
    """

    def __init__(self, base_dir: str = "data/projects"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def append_event(self, event: ProjectActivityEvent) -> None:
        self._ensure_project_dir(event.project_id)
        with open(self._activity_path(event.project_id), "a", encoding="utf-8") as f:
            f.write(json.dumps(self._event_to_dict(event), ensure_ascii=False) + "\n")

    def list_events(self, project_id: str) -> List[ProjectActivityEvent]:
        path = self._activity_path(project_id)
        if not os.path.exists(path):
            return []

        events: List[ProjectActivityEvent] = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if not stripped:
                    continue
                event = self._dict_to_event(json.loads(stripped))
                if event is not None:
                    events.append(event)
        return events

    def _activity_path(self, project_id: str) -> str:
        return os.path.join(self.base_dir, project_id, ACTIVITY_FILENAME)

    def _ensure_project_dir(self, project_id: str) -> None:
        os.makedirs(os.path.join(self.base_dir, project_id), exist_ok=True)

    @staticmethod
    def _event_to_dict(event: ProjectActivityEvent) -> Dict[str, Any]:
        return {
            "id": event.id,
            "projectId": event.project_id,
            "type": event.type.value,
            "actor": event.actor.value,
            "summary": event.summary,
            "at": event.at,
            "iterationId": event.iteration_id,
            "taskId": event.task_id,
            "operationId": event.operation_id,
            "detail": event.detail,
        }

    @staticmethod
    def _dict_to_event(data: Dict[str, Any]) -> Optional[ProjectActivityEvent]:
        """
        Convert a stored line back into an event, or None when the line predates a
        schema change. Unknown event types must not break the whole log.
        """
        try:
            event_type = ProjectActivityEventType(data["type"])
            actor = ProjectActivityActor(data.get("actor", "user"))
        except (KeyError, ValueError):
            return None

        return ProjectActivityEvent(
            id=data["id"],
            project_id=data["projectId"],
            type=event_type,
            actor=actor,
            summary=data.get("summary", ""),
            at=data.get("at", ""),
            iteration_id=data.get("iterationId"),
            task_id=data.get("taskId"),
            operation_id=data.get("operationId"),
            detail=data.get("detail") or {},
        )
