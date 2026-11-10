"""Deterministic stand-ins for the LLM agents and knowledge loaders, for offline service tests."""
import os
from typing import List, Optional

from rdflib import URIRef

from agents.iteration_suggesters.iteration_suggester import IterationSuggesterAgent, IterationSuggesterAgentFake
from agents.knowledge_domain_area_analyzers.knowledge_domain_area_analyzer import KnowledgeDomainAreaAnalyzerAgent
from agents.modelers.modeler import ModelerAgent
from agents.task_planners.task_planner import TaskPlannerAgent
from design_project.domain import (
    DesignIteration,
    DesignProject,
    DesignTask,
    DesignTaskCategory,
    DesignTaskStatus,
    KnowledgeDomain,
    KnowledgeDomainArea,
)
from design_project.service import DesignProjectService
from design_project.store import FileSystemDesignProjectStore
from knowledge_base.domain import KnowledgeDocument
from knowledge_base.service import KnowledgeBaseService
from knowledge_base.store import KnowledgeDocumentLoader, KnowledgeDocumentSummarizer
from ontology.domain import Kind, Ontology
from ontology.edit_operations import CreateClassOperation, OntologyEditOperation
from ontology.service import OntologyService
from ontology.store import FilesystemOntologyStore


class FakeKnowledgeDocumentLoader(KnowledgeDocumentLoader):
    """Returns a one-paragraph document for any ID."""

    def load_document(self, document_id: str) -> KnowledgeDocument:
        return KnowledgeDocument(id=document_id, title="Fake", content="Fake content", contentSummary=None)


class FakeKnowledgeDocumentSummarizer(KnowledgeDocumentSummarizer):
    def summarize_document(self, document: KnowledgeDocument) -> None:
        document.contentSummary = "Fake summary"


class KnowledgeDomainAreaAnalyzerAgentFake(KnowledgeDomainAreaAnalyzerAgent):
    """Returns one area named after the knowledge document."""

    def __init__(self, model_name: str = "fake"):
        super().__init__(model_name)

    def identify_domain_areas(self, knowledge_domain: KnowledgeDomain, knowledge_document: KnowledgeDocument, consider_existing_areas: bool = False, user_instruction: str = "") -> List[KnowledgeDomainArea]:
        return [
            KnowledgeDomainArea(
                id="fake-area-1",
                label=f"Area of {knowledge_document.title}",
                description=user_instruction or None,
                parent=knowledge_domain,
                keyConcepts=["concept"],
                modelingClasses=[],
                modelingAttributes=[],
                modelingRelationships=[],
                explainingKnowledgeResources=[],
            )
        ]


class TaskPlannerAgentFake(TaskPlannerAgent):
    """Plans one task following the project's first class pattern."""

    def __init__(self, model_name: str = "fake"):
        self.model_name = model_name

    def build_iteration_plan(self, design_project: DesignProject, iteration: DesignIteration, user_instruction: str = "") -> List[DesignTask]:
        pattern = next(p for p in design_project.patterns if p.category == DesignTaskCategory.CLASS)
        return [
            DesignTask(
                id=f"{iteration.id}-task-1",
                name=f"Classes for {iteration.name}",
                status=DesignTaskStatus.PLANNED,
                followedPattern=pattern,
                specification=user_instruction or f"Discover classes for {iteration.name}",
                knowledgeResources=[],
                designedOntologyChangesSpecification=None,
            )
        ]

    def update_iteration_plan(self, design_project: DesignProject, iteration: DesignIteration, user_instruction: str = "") -> List[DesignTask]:
        return iteration.plannedTasks


class ModelerAgentFake(ModelerAgent):
    """Creates one class per task, named after the task ID."""

    def __init__(self, model_name: str = "fake"):
        self.model_name = model_name

    def get_operations_for_design_task(self, design_project: DesignProject, current_ontology: Ontology, iteration: DesignIteration, task: DesignTask, project_guidance_text: Optional[str] = None) -> List[OntologyEditOperation]:
        return [
            CreateClassOperation(
                uri=URIRef(f"{current_ontology.uri}#{task.id}"),
                label=f"Class for {task.name}",
                kind=Kind.SUBJECT,
                definition="A fake class.",
                description="A fake class.",
            )
        ]

    def get_operations_from_instruction(self, design_project: DesignProject, current_ontology: Ontology, user_instruction: str) -> List[OntologyEditOperation]:
        return []


def create_fake_design_project_service(base_dir: str, iteration_suggester_agent: Optional[IterationSuggesterAgent] = None) -> DesignProjectService:
    """Build a DesignProjectService with fake agents that stores everything under base_dir."""
    ontology_service = OntologyService(store=FilesystemOntologyStore(base_dir=os.path.join(base_dir, "ontologies")))
    knowledge_base_service = KnowledgeBaseService(
        legal_knowledge_document_loader=FakeKnowledgeDocumentLoader(),
        expert_knowledge_document_loader=FakeKnowledgeDocumentLoader(),
        document_summarizer=FakeKnowledgeDocumentSummarizer(),
    )
    return DesignProjectService(
        store=FileSystemDesignProjectStore(ontology_service=ontology_service, base_dir=os.path.join(base_dir, "projects")),
        knowledge_base_service=knowledge_base_service,
        ontology_service=ontology_service,
        knowledge_domain_area_analyzer_agent=KnowledgeDomainAreaAnalyzerAgentFake(),
        iteration_suggester_agent=iteration_suggester_agent or IterationSuggesterAgentFake(),
        task_planner_agent=TaskPlannerAgentFake(),
        modeler_agent=ModelerAgentFake(),
    )
