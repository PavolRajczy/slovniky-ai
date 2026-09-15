"""Prepare proposes operations; the designed ontology changes only on finalize/apply."""
import os
import sys
import tempfile
from unittest.mock import MagicMock

from rdflib import URIRef

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from design_project.domain import (
    DesignIteration,
    DesignIterationStatus,
    DesignTask,
    DesignTaskCategory,
    DesignTaskPattern,
    DesignTaskStatus,
    KnowledgeDomain,
    KnowledgeDomainArea,
)
from design_project.service import DesignProjectService
from design_project.store import FileSystemDesignProjectStore
from ontology.domain import Kind, Ontology
from ontology.edit_operations import CreateClassOperation
from ontology.service import OntologyService
from ontology.store import FilesystemOntologyStore


class RecordingModeler:
    def __init__(self):
        self.seen_class_counts = []
        self.call_count = 0

    def get_operations_for_design_task(
        self, design_project, current_ontology, iteration, task, project_guidance_text=None
    ):
        self.seen_class_counts.append(len(current_ontology.classes))
        self.call_count += 1
        return [
            CreateClassOperation(
                uri=URIRef(f"http://test.example.org/ontology#Class{self.call_count}"),
                label=f"Class {self.call_count}",
                kind=Kind.SUBJECT,
                definition="A test class.",
                description="A test class.",
            )
        ]


def _make_service(tmp_dir: str, modeler: RecordingModeler) -> DesignProjectService:
    ontology_service = OntologyService(store=FilesystemOntologyStore(base_dir=os.path.join(tmp_dir, "ontologies")))
    store = FileSystemDesignProjectStore(
        ontology_service=ontology_service,
        base_dir=os.path.join(tmp_dir, "projects"),
    )
    kb_service = MagicMock()
    kb_service.load_legal_knowledge_documents.return_value = []
    kb_service.load_expert_knowledge_documents.return_value = []
    return DesignProjectService(
        store=store,
        knowledge_base_service=kb_service,
        ontology_service=ontology_service,
        knowledge_domain_area_analyzer_agent=MagicMock(),
        iteration_suggester_agent=MagicMock(),
        task_planner_agent=MagicMock(),
        modeler_agent=modeler,
    )


def _class_pattern() -> DesignTaskPattern:
    return DesignTaskPattern(
        id="pattern-class",
        name="Discover classes",
        category=DesignTaskCategory.CLASS,
        specification="Discover classes",
        whenApplicable=None,
        exampleTasks=[],
    )


def _task(task_id: str, name: str, pattern: DesignTaskPattern) -> DesignTask:
    return DesignTask(
        id=task_id,
        name=name,
        status=DesignTaskStatus.PLANNED,
        followedPattern=pattern,
        specification=f"Create classes for {name}",
        knowledgeResources=[],
        designedOntologyChangesSpecification=None,
    )


def _seed_project(service: DesignProjectService, task_ids: list[str]):
    ontology = Ontology(
        uri=URIRef("http://test.example.org/ontology"),
        label="Test Ontology",
        description="A test ontology",
        classes={},
        attributes={},
        relationships={},
    )
    service.ontology_service.store_ontology(ontology)
    project = service.initialize_new_project(
        project_name="Finalize-only project",
        working_ontology_uri=str(ontology.uri),
        knowledge_domain_name="Test Domain",
        knowledge_domain_description="A test domain",
    )
    domain = project.modeledKnowledgeDomain
    area = KnowledgeDomainArea(
        id="area-1",
        label="Area",
        description="An area",
        parent=domain,
        keyConcepts=[],
        modelingClasses=[],
        modelingAttributes=[],
        modelingRelationships=[],
        explainingKnowledgeResources=[],
    )
    domain.areas = [area]
    pattern = _class_pattern()
    project.patterns = [pattern]
    project.plannedIterations = [
        DesignIteration(
            id="it-1",
            name="Iteration 1",
            status=DesignIterationStatus.TASKS_PLANNED,
            specification="Add core classes",
            finishedTasks=[],
            currentTask=None,
            plannedTasks=[_task(task_id, f"Task {task_id}", pattern) for task_id in task_ids],
            focusedArea=area,
            plannedOperations=None,
            designedOntologyChangesSpecification=None,
        )
    ]
    service.store.store_project(project)
    return project


def test_prepare_task_does_not_change_designed_ontology():
    with tempfile.TemporaryDirectory() as tmp_dir:
        modeler = RecordingModeler()
        service = _make_service(tmp_dir, modeler)
        project = _seed_project(service, ["t-1", "t-2"])

        service.prepare_planned_iteration_task(project.id, "it-1", "t-1")

        reloaded = service.store.load_project(project.id)
        assert len(reloaded.designedOntology.classes) == 0
        persisted = service.ontology_service.load_ontology(str(reloaded.designedOntology.uri))
        assert len(persisted.classes) == 0
        assert modeler.seen_class_counts == [0]


def test_later_prepare_sees_only_finalized_ontology_not_pending_ops():
    with tempfile.TemporaryDirectory() as tmp_dir:
        modeler = RecordingModeler()
        service = _make_service(tmp_dir, modeler)
        project = _seed_project(service, ["t-1", "t-2"])

        first_ops = service.prepare_planned_iteration_task(project.id, "it-1", "t-1")
        service.prepare_planned_iteration_task(project.id, "it-1", "t-2")

        reloaded = service.store.load_project(project.id)
        assert len(reloaded.designedOntology.classes) == 0
        assert modeler.seen_class_counts == [0, 0]
        assert len(reloaded.currentIteration.plannedOperations) == 2

        service.apply_current_iteration_changes(project.id, first_ops)

        after_finalize = service.store.load_project(project.id)
        assert len(after_finalize.designedOntology.classes) == 1
        persisted = service.ontology_service.load_ontology(str(after_finalize.designedOntology.uri))
        assert len(persisted.classes) == 1


def test_bulk_prepare_does_not_apply_between_tasks():
    with tempfile.TemporaryDirectory() as tmp_dir:
        modeler = RecordingModeler()
        service = _make_service(tmp_dir, modeler)
        project = _seed_project(service, ["t-1", "t-2"])

        operations = service.prepare_planned_iteration(project.id, "it-1")

        reloaded = service.store.load_project(project.id)
        assert len(reloaded.designedOntology.classes) == 0
        assert modeler.seen_class_counts == [0, 0]
        assert len(operations) == 2
        persisted = service.ontology_service.load_ontology(str(reloaded.designedOntology.uri))
        assert len(persisted.classes) == 0
