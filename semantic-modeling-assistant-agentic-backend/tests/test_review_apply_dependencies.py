"""Kept changes reach the vocabulary: missing classes are proposed and unapplied changes are reported."""
import tempfile

from rdflib import URIRef

from design_project.operation_dependencies import label_from_uri
from ontology.domain import Kind
from ontology.edit_operations import CreateAttributeOperation, CreateClassOperation
from test_prepare_does_not_apply_until_finalize import _make_service, _seed_project

BASE = "http://test.example.org/ontology#"


class FixedModeler:
    def __init__(self, operations_by_task):
        self.operations_by_task = operations_by_task

    def get_operations_for_design_task(self, design_project, current_ontology, iteration, task, project_guidance_text=None):
        return list(self.operations_by_task.get(task.id, []))


def _attribute(name: str, owning_class: str) -> CreateAttributeOperation:
    return CreateAttributeOperation(
        uri=URIRef(BASE + name),
        label=name,
        owning_class_uri=URIRef(BASE + owning_class),
        definition="A test attribute.",
    )


def _class(name: str, label: str) -> CreateClassOperation:
    return CreateClassOperation(uri=URIRef(BASE + name), label=label, kind=Kind.OBJECT, definition="A test class.")


def test_attribute_of_a_missing_class_is_proposed_together_with_the_class():
    with tempfile.TemporaryDirectory() as tmp_dir:
        modeler = FixedModeler({"t-1": [_attribute("datumPlatnosti", "TechnickaZpusobilost")]})
        service = _make_service(tmp_dir, modeler)
        project = _seed_project(service, ["t-1"])

        operations = service.prepare_planned_iteration_task(project.id, "it-1", "t-1")

        assert [type(op.operation).__name__ for op in operations] == ["CreateClassOperation", "CreateAttributeOperation"]
        assert operations[0].operation.uri == URIRef(BASE + "TechnickaZpusobilost")
        assert operations[0].operation.label == "Technicka zpusobilost"

        applied = service.apply_current_iteration_changes_with_report(project.id, operations)

        assert applied.skipped == []
        assert applied.applied_count == 2
        assert URIRef(BASE + "TechnickaZpusobilost") in applied.ontology.classes
        assert URIRef(BASE + "datumPlatnosti") in applied.ontology.attributes


def test_missing_class_proposed_by_another_work_item_keeps_its_label():
    with tempfile.TemporaryDirectory() as tmp_dir:
        modeler = FixedModeler({
            "t-1": [_class("TechnickaZpusobilost", "Technická způsobilost")],
            "t-2": [_attribute("datumPlatnosti", "TechnickaZpusobilost")],
        })
        service = _make_service(tmp_dir, modeler)
        project = _seed_project(service, ["t-1", "t-2"])
        service.prepare_planned_iteration_task(project.id, "it-1", "t-1")

        operations = service.prepare_planned_iteration_task(project.id, "it-1", "t-2")

        assert operations[0].operation.label == "Technická způsobilost"


def test_apply_reports_a_kept_change_whose_class_is_not_kept():
    with tempfile.TemporaryDirectory() as tmp_dir:
        modeler = FixedModeler({"t-1": [_attribute("datumPlatnosti", "TechnickaZpusobilost")]})
        service = _make_service(tmp_dir, modeler)
        project = _seed_project(service, ["t-1"])
        _class_op, attribute_op = service.prepare_planned_iteration_task(project.id, "it-1", "t-1")

        applied = service.apply_current_iteration_changes_with_report(project.id, [attribute_op])

        assert applied.applied_count == 0
        assert [skipped.operation_id for skipped in applied.skipped] == [attribute_op.id]
        assert "does not exist" in applied.skipped[0].reason
        assert len(applied.ontology.attributes) == 0


def test_class_is_created_before_its_attribute_whatever_the_kept_order():
    with tempfile.TemporaryDirectory() as tmp_dir:
        modeler = FixedModeler({"t-1": [_attribute("datumPlatnosti", "TechnickaZpusobilost")]})
        service = _make_service(tmp_dir, modeler)
        project = _seed_project(service, ["t-1"])
        class_op, attribute_op = service.prepare_planned_iteration_task(project.id, "it-1", "t-1")

        applied = service.apply_current_iteration_changes_with_report(project.id, [attribute_op, class_op])

        assert applied.skipped == []
        assert len(applied.ontology.attributes) == 1


def test_label_from_uri_splits_camel_case():
    assert label_from_uri("https://example.com/vocabulary#TechnickaZpusobilost") == "Technicka zpusobilost"
    assert label_from_uri("https://example.com/vocabulary/Vozidlo") == "Vozidlo"
