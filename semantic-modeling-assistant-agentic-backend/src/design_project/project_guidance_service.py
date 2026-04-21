"""
Service for project-scoped human-in-the-loop guidance: CRUD and prompt text generation.
"""
from datetime import datetime, timezone
from typing import List, Optional

from .domain import (
    ProjectGuidanceItem,
    ProjectGuidanceItemType,
    ProjectGuidanceItemSource,
)
from .project_guidance_store import ProjectGuidanceStore
import uuid


# Optional limit for total guidance text length to avoid context overflow (chars).
DEFAULT_MAX_GUIDANCE_CHARS = 8000


class ProjectGuidanceService:
    """
    Manages project guidance items and builds the text block to inject into agent prompts.
    """

    def __init__(self, store: ProjectGuidanceStore):
        self.store = store

    def list_items(self, project_id: str) -> List[ProjectGuidanceItem]:
        """Return all guidance items for the project."""
        return self.store.list_items(project_id)

    def add_item(
        self,
        project_id: str,
        content: str,
        type: ProjectGuidanceItemType = ProjectGuidanceItemType.INSTRUCTION,
        source: Optional[ProjectGuidanceItemSource] = ProjectGuidanceItemSource.MANUAL,
    ) -> ProjectGuidanceItem:
        """Add a new guidance item and return it."""
        now = datetime.now(timezone.utc).isoformat()
        item = ProjectGuidanceItem(
            id=str(uuid.uuid4()),
            project_id=project_id,
            type=type,
            content=content.strip(),
            created_at=now,
            source=source,
        )
        self.store.add_item(item)
        return item

    def update_item(
        self,
        project_id: str,
        item_id: str,
        content: str,
        type: ProjectGuidanceItemType,
    ) -> ProjectGuidanceItem:
        """Update an existing item. Raises ValueError if not found."""
        return self.store.update_item(project_id, item_id, content.strip(), type)

    def delete_item(self, project_id: str, item_id: str) -> bool:
        """Remove a guidance item. Returns True if removed."""
        return self.store.delete_item(project_id, item_id)

    def get_item(self, project_id: str, item_id: str) -> Optional[ProjectGuidanceItem]:
        """Get a single item by id."""
        return self.store.get_item(project_id, item_id)

    def get_guidance_text_for_prompt(
        self,
        project_id: str,
        max_chars: Optional[int] = DEFAULT_MAX_GUIDANCE_CHARS,
    ) -> str:
        """
        Build the <PROJECT_GUIDANCE> block for agent prompts.
        Returns empty string if no items. Optionally truncates by total character count.
        """
        items = self.store.list_items(project_id)
        if not items:
            return ""

        lines = []
        total = 0
        for item in items:
            line = f"- [{item.type.value}] {item.content}"
            if max_chars is not None and total + len(line) + 2 > max_chars:
                break
            lines.append(line)
            total += len(line) + 2

        if not lines:
            return ""
        return "<PROJECT_GUIDANCE>\n" + "\n".join(lines) + "\n</PROJECT_GUIDANCE>"
