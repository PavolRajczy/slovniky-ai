"""Unit tests for project guidance CRUD and prompt injection."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from design_project.domain import ProjectGuidanceItemSource, ProjectGuidanceItemType
from design_project.project_guidance_service import ProjectGuidanceService
from design_project.project_guidance_store import FileSystemProjectGuidanceStore
from design_project.service import DesignProjectService


class _DummyStore:
    pass


def _service(tmp_dir: str) -> ProjectGuidanceService:
    return ProjectGuidanceService(FileSystemProjectGuidanceStore(base_dir=tmp_dir))


def test_add_list_update_delete_and_prompt_text():
    with tempfile.TemporaryDirectory() as tmp_dir:
        service = _service(tmp_dir)
        project_id = "project-guidance-test"

        added = service.add_item(
            project_id,
            "Use prefix has- for relationships to legal entities",
            ProjectGuidanceItemType.CORRECTION,
            ProjectGuidanceItemSource.CORRECTION,
        )
        assert added.id
        assert added.source == ProjectGuidanceItemSource.CORRECTION

        listed = service.list_items(project_id)
        assert len(listed) == 1
        assert listed[0].content.startswith("Use prefix")

        updated = service.update_item(
            project_id,
            added.id,
            "Relationships to legal entities must use the prefix has",
            ProjectGuidanceItemType.CORRECTION,
        )
        assert "prefix has" in updated.content

        prompt = service.get_guidance_text_for_prompt(project_id)
        assert prompt.startswith("<PROJECT_GUIDANCE>")
        assert "[correction]" in prompt
        assert "prefix has" in prompt
        assert prompt.endswith("</PROJECT_GUIDANCE>")

        assert service.delete_item(project_id, added.id) is True
        assert service.list_items(project_id) == []
        assert service.get_guidance_text_for_prompt(project_id) == ""


def test_empty_content_rejected():
    with tempfile.TemporaryDirectory() as tmp_dir:
        service = _service(tmp_dir)
        try:
            service.add_item("p1", "   ", ProjectGuidanceItemType.INSTRUCTION)
            assert False, "expected ValueError"
        except ValueError:
            pass


def test_effective_user_instruction_prepends_guidance():
    with tempfile.TemporaryDirectory() as tmp_dir:
        guidance = _service(tmp_dir)
        project_id = "p-instruction"
        guidance.add_item(project_id, "Prefer Czech labels", ProjectGuidanceItemType.PREFERENCE)

        design_service = DesignProjectService(
            store=_DummyStore(),
            knowledge_base_service=_DummyStore(),
            ontology_service=_DummyStore(),
            knowledge_domain_area_analyzer_agent=_DummyStore(),
            iteration_suggester_agent=_DummyStore(),
            task_planner_agent=_DummyStore(),
            modeler_agent=_DummyStore(),
            guidance_service=guidance,
        )
        combined = design_service._effective_user_instruction(project_id, "Focus on section 3")
        assert "<PROJECT_GUIDANCE>" in combined
        assert "Prefer Czech labels" in combined
        assert "Focus on section 3" in combined
        assert combined.index("Prefer Czech labels") < combined.index("Focus on section 3")
