#!/usr/bin/env python3
"""
Interactive CLI tool for managing an ontology design project with AI agents.

Features:
  - Create a new design project (loads predefined legislation + expert knowledge docs)
  - Identify / re-identify knowledge domain areas using KnowledgeDomainAreaAnalyzerAgent_Simple_OpenAI
  - List knowledge domain areas
  - Suggest new iterations for a chosen area using IterationSuggesterAgent_Simple_OpenAI
  - List suggested (planned) iterations for an area
  - Plan tasks for a chosen iteration using TaskPlannerAgent_Simple_OpenAI
  - List planned tasks for an iteration

Used knowledge base (hard-coded for now):
  Legislation documents (ESEL):
    - 2001-56-2025-07-01 (also key knowledge document)
    - 2014-343-2025-07-01
  Expert knowledge documents (local):
    - silnicni-vozidla-expert-knowledge

Implementation components:
  - FileSystemDesignProjectStore
  - ESELKnowledgeDocumentLoader
  - LocalKnowledgeDocumentLoader
  - KnowledgeDomainAreaAnalyzerAgent_Simple_OpenAI
  - IterationSuggesterAgent_Simple_OpenAI
  - TaskPlannerAgent_Simple_OpenAI

Prerequisites:
  - OPENAI_API_KEY environment variable set
  - Ontology file accessible via ontology service (user must provide ontology URI when creating project)

Usage:
  python cli/design_project_tool.py
"""

import os
import sys
import uuid
from typing import List, Optional

# Make src importable
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC_PATH = os.path.join(PROJECT_ROOT, 'src')
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

# Imports from project
from design_project.domain import DesignProject
from design_project.service import DesignProjectService
from design_project.store import FileSystemDesignProjectStore
from ontology.service import OntologyService
from knowledge_base.service import KnowledgeBaseService
from knowledge_base.document_loaders.document_loader_esel import ESELKnowledgeDocumentLoader
from knowledge_base.document_loaders.document_loader_local import LocalKnowledgeDocumentLoader
from knowledge_base.document_summarizers.document_summarizer_simple_openai import SimpleOpenAIKnowledgeDocumentSummarizer
from knowledge_base_index.service import KnowledgeBaseIndexService
from knowledge_base_index.indexers.faiss_summary_openai_indexer import FAISSSummaryOpenAIKnowledgeDocumentIndexer
from agents.knowledge_domain_area_analyzers.knowledge_domain_area_analyzer_openai_simple import KnowledgeDomainAreaAnalyzerAgent_Simple_OpenAI
from agents.iteration_suggesters.iteration_suggester_openai_simple import IterationSuggesterAgent_Simple_OpenAI
from agents.task_planners.task_planner_openai_simple import TaskPlannerAgent_Simple_OpenAI
from agents.modelers.modeler_openai_basic import ModelerAgent_Simple_OpenAI

# Constants for configured knowledge bases
LEGISLATION_IDS = [
    "https://opendata.eselpoint.cz/esel-esb/eli/cz/sb/2001/56/2025-07-01",
    "https://opendata.eselpoint.cz/esel-esb/eli/cz/sb/2014/343/2025-07-01",
]
KEY_KNOWLEDGE_DOCUMENT_ID = LEGISLATION_IDS[0]
EXPERT_LOCAL_IDS = [
    "https://localhost/silnicni-vozidla-expert-knowledge.docx"
]

DEFAULT_PROJECT_ID = "f8dabe47-9c1d-4b86-b54e-e4cdcdb98cb9"

ESEL_SPARQL_ENDPOINT = "https://opendata.eselpoint.cz/sparql"
ESEL_BASE_DIR = "data/knowledge_base/esel"
LOCAL_BASE_DIR = "data/knowledge_base/local"
PROJECTS_BASE_DIR = "data/projects"


def ensure_openai_key():
    if not os.getenv('OPENAI_API_KEY'):
        print("ERROR: OPENAI_API_KEY environment variable is not set.")
        sys.exit(1)


def build_services():
    # Loaders
    esel_loader = ESELKnowledgeDocumentLoader(sparql_endpoint=ESEL_SPARQL_ENDPOINT, base_dir=ESEL_BASE_DIR)
    local_loader = LocalKnowledgeDocumentLoader(base_dir=LOCAL_BASE_DIR)

    # Summarizer (can raise if key missing; we already validated)
    summarizer = SimpleOpenAIKnowledgeDocumentSummarizer()

    # Knowledge base services
    kb_service = KnowledgeBaseService(legal_knowledge_document_loader=esel_loader, expert_knowledge_document_loader=local_loader, document_summarizer=summarizer)

    # Index service (shared for agents needing search)
    kb_index_service = KnowledgeBaseIndexService(indexer=FAISSSummaryOpenAIKnowledgeDocumentIndexer())

    # Ontology service
    ontology_service = OntologyService()

    # Agents
    area_agent = KnowledgeDomainAreaAnalyzerAgent_Simple_OpenAI(knowledge_base_service=kb_service)
    iteration_agent = IterationSuggesterAgent_Simple_OpenAI(knowledge_base_service=kb_service, knowledge_base_index_service=kb_index_service)
    task_planner_agent = TaskPlannerAgent_Simple_OpenAI(knowledge_base_service=kb_service, knowledge_base_index_service=kb_index_service)
    modeler_agent = ModelerAgent_Simple_OpenAI(knowledge_base_service=kb_service, knowledge_base_index_service=kb_index_service)

    design_project_store = FileSystemDesignProjectStore(ontology_service=ontology_service, base_dir=PROJECTS_BASE_DIR)

    # Design project service
    design_service = DesignProjectService(
        store=design_project_store,
        knowledge_base_service=kb_service,
        ontology_service=ontology_service,
        knowledge_domain_area_analyzer_agent=area_agent,
        iteration_suggester_agent=iteration_agent,
        task_planner_agent=task_planner_agent,
        modeler_agent=modeler_agent
    )

    return design_service, kb_index_service, kb_service


def index_documents(kb_index_service: KnowledgeBaseIndexService, kb_service: KnowledgeBaseService, legal_ids: List[str], expert_ids: List[str]):
    """Index specified legal and expert knowledge documents (idempotent)."""
    docs = kb_service.load_knowledge_documents(legal_ids, expert_ids)
    for doc in docs:
        try:
            kb_index_service.add_document(doc)
        except Exception as e:
            print(f"Warning: indexing failed for {doc.id}: {e}")


def create_project(design_service: DesignProjectService):
    print("\n=== Create New Design Project ===")
    project_name = input("Project name: ").strip()
    if not project_name:
        project_name = "Návrh ontologie silničních vozidel"

    ontology_uri = input("Working ontology URI (must exist in data/ontologies): ").strip()
    if not ontology_uri:
        ontology_uri = "https://example.org/silnicni-vozidla#"
    if not ontology_uri:
        print("Ontology URI is required.")
        return None

    domain_name = input("Knowledge domain name (blank to auto): ").strip()
    if not domain_name:
        domain_name = "Silniční vozidla a jejich provoz"

    domain_desc = input("Knowledge domain description (optional): ").strip()
    if not domain_desc:
        domain_desc = "Doména silničních vozidel a jejich provozu"

    print("\nLoading and summarizing knowledge documents (may take a while)...")
    project = design_service.initialize_new_project(
        project_name=project_name,
        working_ontology_uri=ontology_uri,
        legal_act_ids=LEGISLATION_IDS,
        expert_knowledge_documents_ids=EXPERT_LOCAL_IDS,
        key_knowledge_document_id=KEY_KNOWLEDGE_DOCUMENT_ID,
        knowledge_domain_name=domain_name,
        knowledge_domain_description=domain_desc
    )
    print(f"Created project with ID: {project.id}")
    print(f"Identified {len(project.modeledKnowledgeDomain.areas)} domain areas.")
    return project.id


def load_existing_project(design_service: DesignProjectService) -> Optional[str]:
    print("\n=== Load Existing Project ===")
    entered_id = input(f"Project ID (leave blank for default {DEFAULT_PROJECT_ID}): ").strip()
    project_id = entered_id or DEFAULT_PROJECT_ID
    try:
        project = design_service.load_project(project_id)
        print(f"Loaded project '{project.name}' with ID {project.id}")
        if project.modeledKnowledgeDomain and project.modeledKnowledgeDomain.areas:
            print(f"Domain areas: {len(project.modeledKnowledgeDomain.areas)}")
        else:
            print("No domain areas identified yet.")
        return project.id
    except Exception as e:
        print(f"Failed to load project: {e}")
        return None


def list_domain_areas(design_service: DesignProjectService, project_id: str):
    project = design_service.load_project(project_id)
    if not project.modeledKnowledgeDomain or not project.modeledKnowledgeDomain.areas:
        print("No domain areas identified yet.")
        return
    print("\n=== Knowledge Domain Areas ===")
    for idx, area in enumerate(project.modeledKnowledgeDomain.areas, 1):
        print(f"{idx}. {area.label} - {area.description}")
        if area.keyConcepts:
            print(f"    Key concepts: {', '.join(area.keyConcepts)}")


def reidentify_domain_areas(design_service: DesignProjectService, project_id: str):
    project: DesignProject = design_service.load_project(project_id)
    print("Re-identifying domain areas using key knowledge document...")
    user_instruction = input("How do you want to change the domain areas? (Press Enter to continue)")

    new_areas = design_service.knowledge_domain_area_analyzer_agent.identify_domain_areas(
        knowledge_domain=project.modeledKnowledgeDomain,
        knowledge_document=project.keyKnowledgeDocument,
        consider_existing_areas=True,
        user_instruction=user_instruction if user_instruction else ""
    )

    project.modeledKnowledgeDomain.areas = new_areas
    design_service.store.store_project(project)
    print("Updated domain areas.")


def suggest_iterations(design_service: DesignProjectService, project_id: str):
    project = design_service.load_project(project_id)
    if not project.modeledKnowledgeDomain.areas:
        print("No areas. Identify areas first.")
        return
    list_domain_areas(design_service, project_id)
    try:
        selection = int(input("Select area number: "))
    except ValueError:
        print("Invalid selection.")
        return
    if selection < 1 or selection > len(project.modeledKnowledgeDomain.areas):
        print("Out of range.")
        return
    area = project.modeledKnowledgeDomain.areas[selection - 1]
    try:
        k = int(input("Number of iterations to suggest (k): "))
    except ValueError:
        print("Invalid k.")
        return
    user_instruction = input("Optional user instruction: ").strip()
    iterations = design_service.suggest_iterations(project.id, area.id, k, user_instruction)
    # Assign real IDs if placeholder
    changed = False
    for it in iterations:
        if it.id == 'to-be-generated':
            it.id = str(uuid.uuid4())
            changed = True
    if changed:
        design_service.store.store_project(project)
    print(f"Suggested {len(iterations)} iterations for area '{area.label}'.")


def list_iterations(design_service: DesignProjectService, project_id: str):
    project = design_service.load_project(project_id)
    if not project.plannedIterations:
        print("No planned iterations.")
        return
    print("\n=== Planned Iterations ===")
    for idx, it in enumerate(project.plannedIterations, 1):
        print(f"{idx}. [{it.id}] {it.name} (Status: {it.status})")
        if it.specification:
            print(f"    Spec: {it.specification}")


def plan_tasks(design_service: DesignProjectService, project_id: str):
    project = design_service.load_project(project_id)
    if not project.plannedIterations:
        print("No planned iterations to plan tasks for.")
        return
    list_iterations(design_service, project_id)
    try:
        number = int(input("Enter iteration number to plan tasks for: ").strip())
    except ValueError:
        print("Invalid number.")
        return
    if number < 1 or number > len(project.plannedIterations):
        print("Number out of range.")
        return
    iteration = project.plannedIterations[number - 1]
    if iteration.plannedTasks or iteration.finishedTasks or iteration.currentTask:
        print("Iteration already has tasks. (Re)planning not yet implemented here - remove tasks manually if needed.)")
        return
    user_instruction = input("Optional user instruction for task planning: ").strip()
    tasks = design_service.initialize_iteration_tasks(project.id, iteration.id, user_instruction)
    print(f"Planned {len(tasks)} tasks.")


def list_tasks(design_service: DesignProjectService, project_id: str):
    project = design_service.load_project(project_id)
    if not project.plannedIterations:
        print("No planned iterations.")
        return
    list_iterations(design_service, project_id)
    try:
        number = int(input("Enter iteration number to list tasks for: ").strip())
    except ValueError:
        print("Invalid number.")
        return
    if number < 1 or number > len(project.plannedIterations):
        print("Number out of range.")
        return
    iteration = project.plannedIterations[number - 1]
    if not iteration.plannedTasks:
        print("No planned tasks.")
        return
    print(f"\n=== Planned Tasks for Iteration {iteration.id} ===")
    for idx, t in enumerate(iteration.plannedTasks, 1):
        print(f"{idx}. {t.name} (Pattern: {t.followedPattern.name if t.followedPattern else 'N/A'})")
        if t.specification:
            print(f"    Spec: {t.specification[:200]}{'...' if len(t.specification) > 200 else ''}")


def prepare_iteration(design_service: DesignProjectService, project_id: str):
    """Prepare an iteration by generating operations without applying them."""
    project = design_service.load_project(project_id)
    if not project.plannedIterations:
        print("No planned iterations to prepare.")
        return None
    
    # Show iterations with task counts
    print("\n=== Planned Iterations ===")
    performable_iterations = []
    for idx, it in enumerate(project.plannedIterations, 1):
        task_count = len(it.plannedTasks) if it.plannedTasks else 0
        status_str = f"Status: {it.status}, Tasks: {task_count}"
        print(f"{idx}. [{it.id}] {it.name} ({status_str})")
        if it.specification:
            print(f"    Spec: {it.specification}")
        if task_count > 0:
            performable_iterations.append(idx)
    
    if not performable_iterations:
        print("No iterations have planned tasks. Plan tasks for an iteration first.")
        return None
    
    try:
        number = int(input("Enter iteration number to prepare: ").strip())
    except ValueError:
        print("Invalid number.")
        return None
    
    if number < 1 or number > len(project.plannedIterations):
        print("Number out of range.")
        return None
    
    if number not in performable_iterations:
        print("Selected iteration has no planned tasks. Plan tasks first.")
        return None
    
    iteration = project.plannedIterations[number - 1]
    
    print(f"\nAbout to prepare iteration '{iteration.name}' with {len(iteration.plannedTasks)} planned tasks.")
    confirm = input("This will execute AI agents to generate operations. Continue? (y/N): ").strip().lower()
    
    if confirm != 'y':
        print("Cancelled.")
        return None
    
    try:
        operations = design_service.prepare_planned_iteration(project.id, iteration.id)
        print(f"Successfully prepared iteration '{iteration.name}' with {len(operations)} operations.")
        
        # Show operations to user
        print(f"\nGenerated operations:")
        for i, op in enumerate(operations, 1):
            op_type = type(op).__name__
            if hasattr(op, 'label'):
                print(f"{i}. {op_type}: {op.label}")
            elif hasattr(op, 'uri'):
                print(f"{i}. {op_type}: {op.uri}")
            else:
                print(f"{i}. {op_type}")
        
        return operations
    except Exception as e:
        print(f"Failed to prepare iteration: {e}")
        return None


def apply_prepared_operations(design_service: DesignProjectService, project_id: str, operations):
    """Apply the prepared operations to complete the iteration."""
    if not operations:
        print("No prepared operations available. Prepare an iteration first.")
        return False
    
    project = design_service.load_project(project_id)
    if not project.currentIteration:
        print("No current iteration to apply operations to.")
        return False
    
    if project.currentIteration.status.value != 'prepared':
        print(f"Current iteration is not in PREPARED status: {project.currentIteration.status}")
        return False
    
    print(f"\nAbout to apply {len(operations)} operations to iteration '{project.currentIteration.name}'.")
    print("This will modify the ontology and complete the iteration.")
    confirm = input("Continue? (y/N): ").strip().lower()
    
    if confirm != 'y':
        print("Cancelled.")
        return False
    
    try:
        design_service.apply_current_iteration_changes(project.id, operations)
        print(f"Successfully applied operations and completed iteration.")
        return True
    except Exception as e:
        print(f"Failed to apply operations: {e}")
        return False


def main():
    ensure_openai_key()
    design_service, kb_index_service, kb_service = build_services()

    project_id: Optional[str] = None
    prepared_operations = None  # Store operations between prepare and apply phases
    prepared_operations = None  # Store operations between prepare and apply phases


    MENU = (
        "\n=== Ontology Design Project Tool ===\nCurrent project: {proj}\n"
        "Prepared operations: {ops}\n"
        "----------------------------------\n"
        "1. Create new project\n"
        "2. Load existing project\n"
        "3. List domain areas\n"
        "4. Re-identify domain areas\n"
        "5. Suggest iterations for area\n"
        "6. List planned iterations\n"
        "7. Plan tasks for iteration\n"
        "8. List planned tasks for iteration\n"
        "9. Prepare planned iteration (get operations)\n"
        "10. Apply prepared operations (execute operations)\n"
        "0. Exit\n"
        "Choice: "
    )

    while True:
        try:
            ops_count = len(prepared_operations) if prepared_operations else 0
            choice = input(MENU.format(proj=project_id or 'None', ops=f"{ops_count} operations" if ops_count > 0 else "None")).strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if choice == '1':
            project_id = create_project(design_service)
            if project_id:
                index_documents(kb_index_service, kb_service, LEGISLATION_IDS, EXPERT_LOCAL_IDS)
        elif choice == '2':
            project_id = load_existing_project(design_service) or project_id
            if project_id:
                index_documents(kb_index_service, kb_service, LEGISLATION_IDS, EXPERT_LOCAL_IDS)
        elif choice == '3':
            if not project_id:
                print("Create or load a project first.")
            else:
                list_domain_areas(design_service, project_id)
        elif choice == '4':
            if not project_id:
                print("Create or load a project first.")
            else:
                reidentify_domain_areas(design_service, project_id)
        elif choice == '5':
            if not project_id:
                print("Create or load a project first.")
            else:
                suggest_iterations(design_service, project_id)
        elif choice == '6':
            if not project_id:
                print("Create or load a project first.")
            else:
                list_iterations(design_service, project_id)
        elif choice == '7':
            if not project_id:
                print("Create or load a project first.")
            else:
                plan_tasks(design_service, project_id)
        elif choice == '8':
            if not project_id:
                print("Create or load a project first.")
            else:
                list_tasks(design_service, project_id)
        elif choice == '9':
            if not project_id:
                print("Create or load a project first.")
            else:
                prepared_operations = prepare_iteration(design_service, project_id)
        elif choice == '10':
            if not project_id:
                print("Create or load a project first.")
            else:
                if apply_prepared_operations(design_service, project_id, prepared_operations):
                    prepared_operations = None  # Clear operations after successful application
        elif choice == '0':
            print("Goodbye!")
            break
        else:
            print("Invalid choice.")


if __name__ == '__main__':
    main()
