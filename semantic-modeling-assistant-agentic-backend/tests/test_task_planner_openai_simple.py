#!/usr/bin/env python3
"""
Live test for TaskPlannerAgent_Simple_OpenAI.

Loads a real e-Sbírka act and asks the LLM to plan the tasks of one design
iteration that has a goal.
"""

import pytest

from agents.task_planners.task_planner_openai_simple import TaskPlannerAgent_Simple_OpenAI
from design_project.domain import DesignIteration, DesignIterationStatus, DesignTask, DesignTaskStatus
from knowledge_base_index.indexers.faiss_summary_openai_indexer import FAISSSummaryOpenAIKnowledgeDocumentIndexer
from knowledge_base_index.service import KnowledgeBaseIndexService
from live_support import (
    LIVE_LEGAL_DOCUMENT_ID,
    create_live_knowledge_base_service,
    create_registration_area,
    create_vehicle_domain,
    create_vehicle_project,
)


@pytest.mark.live
def test_task_planner_with_real_document():
    """Test the task planner with a real e-Sbírka document and a goal-directed iteration."""
    kb_service = create_live_knowledge_base_service()
    kb_index_service = KnowledgeBaseIndexService(indexer=FAISSSummaryOpenAIKnowledgeDocumentIndexer())
    planner = TaskPlannerAgent_Simple_OpenAI(kb_service, kb_index_service)

    documents = kb_service.load_legal_knowledge_documents([LIVE_LEGAL_DOCUMENT_ID])
    assert len(documents) > 0, "Should load at least one document"

    knowledge_domain = create_vehicle_domain()
    focused_area = create_registration_area(knowledge_domain)
    design_project = create_vehicle_project(documents[0], knowledge_domain)
    iteration = DesignIteration(
        id="iteration-registration",
        name="Základní pojmy registrace vozidel",
        status=DesignIterationStatus.PLANNED,
        specification="Navrhnout třídy pro vozidlo, jeho provozovatele a registr silničních vozidel.",
        finishedTasks=[],
        currentTask=None,
        plannedTasks=[],
        focusedArea=focused_area,
        plannedOperations=None,
        designedOntologyChangesSpecification=None,
        goal="Model what a vehicle registration record contains.",
    )
    design_project.plannedIterations.append(iteration)

    tasks = planner.build_iteration_plan(design_project, iteration)

    assert isinstance(tasks, list), "Should return a list of design tasks"
    assert len(tasks) > 0, "Should plan at least one task"
    for i, task in enumerate(tasks):
        assert isinstance(task, DesignTask), f"Task {i} should be a DesignTask instance"
        assert task.name, f"Task {i} should have a non-empty name"
        assert task.status == DesignTaskStatus.PLANNED, f"Task {i} should have PLANNED status"
