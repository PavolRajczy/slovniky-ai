"""
Store for project-scoped human-in-the-loop guidance items.
Persists to data/projects/{project_id}/guidance.json.
"""
import os
import json
from typing import Any, Dict, List

from .domain import (
    ProjectGuidanceItem,
    ProjectGuidanceItemType,
    ProjectGuidanceItemSource,
)


GUIDANCE_FILENAME = "guidance.json"


class ProjectGuidanceStore:
    """Abstract store for project guidance items."""

    def list_items(self, project_id: str) -> List[ProjectGuidanceItem]:
        """Load all guidance items for a project."""
        ...

    def add_item(self, item: ProjectGuidanceItem) -> None:
        """Add a guidance item and persist."""
        ...

    def update_item(self, project_id: str, item_id: str, content: str, type: ProjectGuidanceItemType) -> ProjectGuidanceItem:
        """Update an existing item; returns the updated item or raises if not found."""
        ...

    def delete_item(self, project_id: str, item_id: str) -> bool:
        """Remove a guidance item. Returns True if removed, False if not found."""
        ...

    def get_item(self, project_id: str, item_id: str) -> ProjectGuidanceItem | None:
        """Get a single item by id, or None."""
        ...


class FileSystemProjectGuidanceStore(ProjectGuidanceStore):
    """Stores guidance items in data/projects/{project_id}/guidance.json."""

    def __init__(self, base_dir: str = "data/projects"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def _guidance_path(self, project_id: str) -> str:
        return os.path.join(self.base_dir, project_id, GUIDANCE_FILENAME)

    def _ensure_project_dir(self, project_id: str) -> None:
        project_dir = os.path.join(self.base_dir, project_id)
        os.makedirs(project_dir, exist_ok=True)

    def _load_raw(self, project_id: str) -> List[Dict[str, Any]]:
        path = self._guidance_path(project_id)
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("items", [])

    def _save_raw(self, project_id: str, items: List[Dict[str, Any]]) -> None:
        self._ensure_project_dir(project_id)
        path = self._guidance_path(project_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"items": items}, f, ensure_ascii=False, indent=2)

    @staticmethod
    def _item_to_dict(item: ProjectGuidanceItem) -> Dict[str, Any]:
        return {
            "id": item.id,
            "projectId": item.project_id,
            "type": item.type.value,
            "content": item.content,
            "createdAt": item.created_at,
            "source": item.source.value if item.source else None,
        }

    @staticmethod
    def _dict_to_item(data: Dict[str, Any]) -> ProjectGuidanceItem:
        return ProjectGuidanceItem(
            id=data["id"],
            project_id=data["projectId"],
            type=ProjectGuidanceItemType(data.get("type", "instruction")),
            content=data["content"],
            created_at=data.get("createdAt"),
            source=ProjectGuidanceItemSource(data["source"]) if data.get("source") else None,
        )

    def list_items(self, project_id: str) -> List[ProjectGuidanceItem]:
        raw = self._load_raw(project_id)
        return [self._dict_to_item(r) for r in raw]

    def add_item(self, item: ProjectGuidanceItem) -> None:
        items = self.list_items(item.project_id)
        items.append(item)
        self._save_raw(item.project_id, [self._item_to_dict(i) for i in items])

    def update_item(
        self, project_id: str, item_id: str, content: str, type: ProjectGuidanceItemType
    ) -> ProjectGuidanceItem:
        items = self.list_items(project_id)
        for i, it in enumerate(items):
            if it.id == item_id:
                updated = ProjectGuidanceItem(
                    id=it.id,
                    project_id=it.project_id,
                    type=type,
                    content=content,
                    created_at=it.created_at,
                    source=it.source,
                )
                items[i] = updated
                self._save_raw(project_id, [self._item_to_dict(x) for x in items])
                return updated
        raise ValueError(f"Guidance item not found: {item_id}")

    def delete_item(self, project_id: str, item_id: str) -> bool:
        items = self.list_items(project_id)
        new_items = [i for i in items if i.id != item_id]
        if len(new_items) == len(items):
            return False
        self._save_raw(project_id, [self._item_to_dict(x) for x in new_items])
        return True

    def get_item(self, project_id: str, item_id: str) -> ProjectGuidanceItem | None:
        for item in self.list_items(project_id):
            if item.id == item_id:
                return item
        return None
