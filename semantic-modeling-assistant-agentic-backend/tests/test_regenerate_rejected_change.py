"""Regenerating a rejected change replaces only that change and uses the rejection reason."""
import tempfile

from rdflib import URIRef

from ontology.domain import Kind
from ontology.edit_operations import CreateClassOperation
from test_prepare_does_not_apply_until_finalize import _make_service, _seed_project

BASE = "http://test.example.org/ontology#"


def _class(name: str) -> CreateClassOperation:
    return CreateClassOperation(uri=URIRef(BASE + name), label=name, kind=Kind.OBJECT, definition=f"{name} class.")


class ScriptedModeler:
    """Returns the next scripted answer for each call and records the guidance it received."""

    def __init__(self, answers):
        self.answers = list(answers)
        self.guidance = []

    def get_operations_for_design_task(self, design_project, current_ontology, iteration, task, project_guidance_text=None):
        self.guidance.append(project_guidance_text)
        return list(self.answers.pop(0))


def test_regenerate_replaces_the_rejected_change_in_place():
    with tempfile.TemporaryDirectory() as tmp_dir:
        modeler = ScriptedModeler([
            [_class("Vozidlo"), _class("Motocykl"), _class("Ridic")],
            [_class("Vozidlo"), _class("JednostopeVozidlo")],
        ])
        service = _make_service(tmp_dir, modeler)
        project = _seed_project(service, ["t-1"])
        vozidlo, motocykl, ridic = service.prepare_planned_iteration_task(project.id, "it-1", "t-1")

        replacements = service.regenerate_rejected_operation(
            project.id, "it-1", motocykl.id, rejection_reason="Use the term from the act."
        )

        assert [op.operation.label for op in replacements] == ["JednostopeVozidlo"]
        assert replacements[0].created_from_task_id == "t-1"
        assert "Use the term from the act." in modeler.guidance[-1]
        remaining = service.store.load_project(project.id).currentIteration.plannedOperations
        assert [op.id for op in remaining] == [vozidlo.id, replacements[0].id, ridic.id]


def test_regenerate_keeps_the_rejected_change_when_nothing_new_is_proposed():
    with tempfile.TemporaryDirectory() as tmp_dir:
        modeler = ScriptedModeler([
            [_class("Vozidlo"), _class("Motocykl")],
            [_class("Vozidlo"), _class("Motocykl")],
        ])
        service = _make_service(tmp_dir, modeler)
        project = _seed_project(service, ["t-1"])
        vozidlo, motocykl = service.prepare_planned_iteration_task(project.id, "it-1", "t-1")

        replacements = service.regenerate_rejected_operation(project.id, "it-1", motocykl.id)

        assert replacements == []
        remaining = service.store.load_project(project.id).currentIteration.plannedOperations
        assert [op.id for op in remaining] == [vozidlo.id, motocykl.id]
