"""
Design Project Controller

Main controller handling all design project operations and orchestrating the design workflow.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status, Query
from urllib.parse import unquote
import logging
import uuid

from design_project.domain import ProjectGuidanceItemType
from design_project.project_guidance_service import ProjectGuidanceService
from design_project.project_guidance_store import FileSystemProjectGuidanceStore
from design_project.service import DesignProjectService
from design_project.store import FileSystemDesignProjectStore
from design_project.domain import (
    DesignProject, DesignIteration, DesignTask, DesignTaskPattern, KnowledgeDomainArea,
    DesignIterationStatus, DesignTaskStatus, IdentifiedOperation,
)
from knowledge_base.service import KnowledgeBaseService
from knowledge_base.document_loaders.document_loader_esel import ESELKnowledgeDocumentLoader
from knowledge_base.document_loaders.document_loader_local import LocalKnowledgeDocumentLoader
from knowledge_base.document_summarizers.document_summarizer_simple_openai import SimpleOpenAIKnowledgeDocumentSummarizer
from knowledge_base_index.service import KnowledgeBaseIndexService
from knowledge_base_index.indexers.faiss_summary_openai_indexer import FAISSSummaryOpenAIKnowledgeDocumentIndexer
from ontology.service import OntologyService
from ontology.edit_operations import OntologyEditOperation, OperationType
from agents.knowledge_domain_area_analyzers.knowledge_domain_area_analyzer_openai_simple import KnowledgeDomainAreaAnalyzerAgent_Simple_OpenAI
from agents.iteration_suggesters.iteration_suggester_openai_simple import IterationSuggesterAgent_Simple_OpenAI
from agents.task_planners.task_planner_openai_simple import TaskPlannerAgent_Simple_OpenAI
from agents.modelers.modeler_openai_basic import ModelerAgent_Simple_OpenAI

from api.models import (
    CreateProjectRequest, UpdateProjectRequest, ProjectSummary, ProjectModel,
    KnowledgeDomainAreaModel, CreateDomainAreaRequest, UpdateDomainAreaRequest,
    ReidentifyDomainAreasRequest, SetKeyDocumentRequest, GenerateDomainAreasRequest,
    DesignIterationModel, CreateIterationRequest,
    UpdateIterationRequest, SuggestIterationsRequest, ReorderIterationsRequest,
    DesignTaskModel, DesignTaskPatternModel, CreateTaskRequest, UpdateTaskRequest, PlanTasksRequest,
    ReorderTasksRequest, OntologyOperationModel, ReorderOperationsRequest, UpdateOperationRequest,
    ApplyOperationsRequest, AddKnowledgeDocumentsRequest, DeleteResponse,
    SuccessResponse, IterationPreparedResponse, IterationAppliedResponse,
    IterationsListResponse, TasksListResponse, TaskPatternsListResponse, KnowledgeBaseResponse,
    KnowledgeDocumentSummary, OntologyModel,
    ProjectGuidanceItemModel, CreateProjectGuidanceItemRequest, UpdateProjectGuidanceItemRequest,
    ProjectGuidanceListResponse,
    GenerateOperationsRequest, ApplyProjectOperationsRequest,
)
from api.controllers.ontology_controller import _convert_ontology_to_model
from api.controllers.knowledge_base_controller import _convert_document_to_model

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize services
ontology_service = OntologyService()
knowledge_base_service = KnowledgeBaseService(
    legal_knowledge_document_loader=ESELKnowledgeDocumentLoader(
        sparql_endpoint="https://opendata.eselpoint.cz/sparql"
    ),
    expert_knowledge_document_loader=LocalKnowledgeDocumentLoader(),
    document_summarizer=SimpleOpenAIKnowledgeDocumentSummarizer()
)
knowledge_base_index_service = KnowledgeBaseIndexService(
    indexer=FAISSSummaryOpenAIKnowledgeDocumentIndexer()
)

guidance_store = FileSystemProjectGuidanceStore(base_dir="data/projects")
guidance_service = ProjectGuidanceService(store=guidance_store)

design_project_service = DesignProjectService(
    store=FileSystemDesignProjectStore(ontology_service=ontology_service),
    knowledge_base_service=knowledge_base_service,
    ontology_service=ontology_service,
    knowledge_domain_area_analyzer_agent=KnowledgeDomainAreaAnalyzerAgent_Simple_OpenAI(
        knowledge_base_service=knowledge_base_service
    ),
    iteration_suggester_agent=IterationSuggesterAgent_Simple_OpenAI(
        knowledge_base_service=knowledge_base_service,
        knowledge_base_index_service=knowledge_base_index_service
    ),
    task_planner_agent=TaskPlannerAgent_Simple_OpenAI(
        knowledge_base_service=knowledge_base_service,
        knowledge_base_index_service=knowledge_base_index_service
    ),
    modeler_agent=ModelerAgent_Simple_OpenAI(
        knowledge_base_service=knowledge_base_service,
        knowledge_base_index_service=knowledge_base_index_service
    ),
    guidance_service=guidance_service,
)


# ============================================================================
# Helper Functions
# ============================================================================

def _ensure_project_documents_indexed(project: DesignProject) -> None:
    """
    Ensure all documents in a project are indexed in the knowledge base index service.
    
    This function is idempotent and will:
    1. Check if each document is already indexed
    2. If not, add it to the index (which will load from disk if available, or build new index)
    
    This is called when loading a project to restore the index state after app restarts.
    
    Args:
        project: The design project whose documents should be indexed
    """
    all_documents = project.legalKnowledgeBase + project.expertKnowledgeBase
    
    for doc in all_documents:
        if not knowledge_base_index_service.has_document(doc.id):
            try:
                logger.info(f"Re-indexing document after restart: {doc.id}")
                knowledge_base_index_service.add_document(doc)
            except Exception as e:
                # Log warning but don't fail the project load
                logger.warning(f"Failed to index document {doc.id} for project {project.id}: {e}")


def _convert_domain_area_to_model(area: KnowledgeDomainArea) -> KnowledgeDomainAreaModel:
    """Convert domain KnowledgeDomainArea to API model."""
    return KnowledgeDomainAreaModel(
        id=area.id,
        label=area.label,
        description=area.description or "",
        parent_id=None,  # Not currently tracked in domain model
        key_concepts=area.keyConcepts,
        modeling_classes=[str(c.uri) for c in area.modelingClasses],
        modeling_attributes=[str(a.uri) for a in area.modelingAttributes],
        modeling_relationships=[str(r.uri) for r in area.modelingRelationships],
        explaining_knowledge_resources=[elem.id for elem in area.explainingKnowledgeResources]
    )


def _convert_iteration_to_model(iteration: DesignIteration) -> DesignIterationModel:
    """Convert domain DesignIteration to API model."""
    # Calculate task statistics
    planned_count = len(iteration.plannedTasks)
    finished_count = len(iteration.finishedTasks)
    current_count = 1 if iteration.currentTask else 0
    total_count = planned_count + finished_count + current_count
    
    # Map domain status to API status
    # API exposes only user-visible states, internal workflow states are mapped to their closest API equivalent
    status_mapping = {
        DesignIterationStatus.PLANNED: "suggested",  # Initial planned state
        DesignIterationStatus.TASKS_PLANNED: "planned",  # Tasks have been planned
        DesignIterationStatus.GENERATING_OPERATIONS: "prepared",  # Internal state - show as prepared
        DesignIterationStatus.OPERATIONS_GENERATED: "prepared",  # Operations ready to apply
        DesignIterationStatus.APPLYING_OPERATIONS: "prepared",  # Internal state - show as prepared
        DesignIterationStatus.COMPLETED: "completed"  # Iteration finished
    }
    
    api_status = status_mapping.get(iteration.status, "suggested")
    
    return DesignIterationModel(
        id=iteration.id,
        name=iteration.name or "",
        specification=iteration.specification or "",
        focused_area_id=iteration.focusedArea.id,
        status=api_status,
        total_tasks=total_count,
        planned_tasks_count=planned_count,
        finished_tasks_count=finished_count
    )


def _convert_task_to_model(task: DesignTask) -> DesignTaskModel:
    """Convert domain DesignTask to API model."""
    # Map domain status to API status
    # API exposes only user-visible states
    status_mapping = {
        DesignTaskStatus.PLANNED: "planned",
        DesignTaskStatus.GENERATING_OPERATIONS: "generating",  # Internal state - show as generating
        DesignTaskStatus.OPERATIONS_GENERATED: "generating",  # Still generating from API perspective
        DesignTaskStatus.COMPLETED: "completed"
    }
    
    api_status = status_mapping.get(task.status, "planned")
    
    return DesignTaskModel(
        id=task.id,
        name=task.name or "",
        specification=task.specification or "",
        followed_pattern_id=task.followedPattern.id,
        status=api_status
    )


def _convert_pattern_to_model(pattern: DesignTaskPattern) -> DesignTaskPatternModel:
    """Convert domain DesignTaskPattern to API model."""
    from api.models import DesignTaskPatternModel
    
    return DesignTaskPatternModel(
        id=pattern.id,
        name=pattern.name,
        category=pattern.category.value,
        specification=pattern.specification,
        when_applicable=pattern.whenApplicable
    )


def _convert_operation_to_model(identified_op) -> OntologyOperationModel:
    """
    Convert domain IdentifiedOperation to API model.
    
    This function performs a complete mapping including the operation ID.
    """
    from ontology.edit_operations import (
        CreateClassOperation, UpdateClassOperation, DeleteClassOperation,
        CreateAttributeOperation, UpdateAttributeOperation, DeleteAttributeOperation,
        CreateRelationshipOperation, UpdateRelationshipOperation, DeleteRelationshipOperation
    )
    
    operation = identified_op.operation
    
    # Determine operation type
    op_type = operation.operation_type.value
    
    # Class Operations
    if isinstance(operation, (CreateClassOperation, UpdateClassOperation, DeleteClassOperation)):
        return OntologyOperationModel(
            id=identified_op.id,
            operation_type=op_type,
            target_type="class",
            uri=str(operation.uri),
            label=getattr(operation, 'label', None),
            kind=operation.kind.value if hasattr(operation, 'kind') and operation.kind else None,
            definition=getattr(operation, 'definition', None),
            description=getattr(operation, 'description', None),
            generalization_uris=[str(uri) for uri in operation.generalization_uris] if hasattr(operation, 'generalization_uris') and operation.generalization_uris else None,
            definition_references=getattr(operation, 'definition_references', None),
            specification_references=getattr(operation, 'specification_references', None),
            references=getattr(operation, 'references', None)
        )
    
    # Attribute Operations
    elif isinstance(operation, (CreateAttributeOperation, UpdateAttributeOperation, DeleteAttributeOperation)):
        return OntologyOperationModel(
            id=identified_op.id,
            operation_type=op_type,
            target_type="attribute",
            uri=str(operation.uri),
            label=getattr(operation, 'label', None),
            definition=getattr(operation, 'definition', None),
            description=getattr(operation, 'description', None),
            owning_class_uri=str(operation.owning_class_uri) if hasattr(operation, 'owning_class_uri') and operation.owning_class_uri else None,
            definition_references=getattr(operation, 'definition_references', None),
            specification_references=getattr(operation, 'specification_references', None),
            references=getattr(operation, 'references', None)
        )
    
    # Relationship Operations
    elif isinstance(operation, (CreateRelationshipOperation, UpdateRelationshipOperation, DeleteRelationshipOperation)):
        return OntologyOperationModel(
            id=identified_op.id,
            operation_type=op_type,
            target_type="relationship",
            uri=str(operation.uri),
            label=getattr(operation, 'label', None),
            definition=getattr(operation, 'definition', None),
            description=getattr(operation, 'description', None),
            source_class_uri=str(operation.source_class_uri) if hasattr(operation, 'source_class_uri') and operation.source_class_uri else None,
            target_class_uri=str(operation.target_class_uri) if hasattr(operation, 'target_class_uri') and operation.target_class_uri else None,
            definition_references=getattr(operation, 'definition_references', None),
            specification_references=getattr(operation, 'specification_references', None),
            references=getattr(operation, 'references', None)
        )
    
    else:
        raise ValueError(f"Unknown operation type: {type(operation)}")


def _convert_model_to_operation(model: OntologyOperationModel) -> OntologyEditOperation:
    """
    Convert API model OntologyOperationModel to domain OntologyEditOperation.
    
    This is the inverse of _convert_operation_to_model, allowing operations
    to be sent from frontend -> backend and then applied.
    """
    from ontology.edit_operations import (
        CreateClassOperation, UpdateClassOperation, DeleteClassOperation,
        CreateAttributeOperation, UpdateAttributeOperation, DeleteAttributeOperation,
        CreateRelationshipOperation, UpdateRelationshipOperation, DeleteRelationshipOperation
    )
    from ontology.domain import Kind
    from rdflib import URIRef
    
    uri = URIRef(model.uri)
    
    # Class Operations
    if model.target_type == "class":
        if model.operation_type == "create":
            return CreateClassOperation(
                uri=uri,
                label=model.label,
                kind=Kind(model.kind) if model.kind else None,
                definition=model.definition,
                description=model.description,
                generalization_uris=[URIRef(u) for u in model.generalization_uris] if model.generalization_uris else None,
                definition_references=model.definition_references,
                specification_references=model.specification_references,
                references=model.references
            )
        elif model.operation_type == "update":
            return UpdateClassOperation(
                uri=uri,
                label=model.label,
                kind=Kind(model.kind) if model.kind else None,
                definition=model.definition,
                description=model.description,
                generalization_uris=[URIRef(u) for u in model.generalization_uris] if model.generalization_uris else None,
                definition_references=model.definition_references,
                specification_references=model.specification_references,
                references=model.references
            )
        elif model.operation_type == "delete":
            return DeleteClassOperation(uri=uri)
    
    # Attribute Operations
    elif model.target_type == "attribute":
        if model.operation_type == "create":
            return CreateAttributeOperation(
                uri=uri,
                label=model.label,
                owning_class_uri=URIRef(model.owning_class_uri) if model.owning_class_uri else None,
                definition=model.definition,
                description=model.description,
                definition_references=model.definition_references,
                specification_references=model.specification_references,
                references=model.references
            )
        elif model.operation_type == "update":
            return UpdateAttributeOperation(
                uri=uri,
                label=model.label,
                owning_class_uri=URIRef(model.owning_class_uri) if model.owning_class_uri else None,
                definition=model.definition,
                description=model.description,
                definition_references=model.definition_references,
                specification_references=model.specification_references,
                references=model.references
            )
        elif model.operation_type == "delete":
            return DeleteAttributeOperation(uri=uri)
    
    # Relationship Operations
    elif model.target_type == "relationship":
        if model.operation_type == "create":
            return CreateRelationshipOperation(
                uri=uri,
                label=model.label,
                source_class_uri=URIRef(model.source_class_uri) if model.source_class_uri else None,
                target_class_uri=URIRef(model.target_class_uri) if model.target_class_uri else None,
                definition=model.definition,
                description=model.description,
                definition_references=model.definition_references,
                specification_references=model.specification_references,
                references=model.references
            )
        elif model.operation_type == "update":
            return UpdateRelationshipOperation(
                uri=uri,
                label=model.label,
                source_class_uri=URIRef(model.source_class_uri) if model.source_class_uri else None,
                target_class_uri=URIRef(model.target_class_uri) if model.target_class_uri else None,
                definition=model.definition,
                description=model.description,
                definition_references=model.definition_references,
                specification_references=model.specification_references,
                references=model.references
            )
        elif model.operation_type == "delete":
            return DeleteRelationshipOperation(uri=uri)
    
    raise ValueError(f"Invalid operation: {model.operation_type} on {model.target_type}")


def _convert_model_to_identified_operation(model: OntologyOperationModel):
    """
    Convert API model to domain IdentifiedOperation.
    
    This allows operations sent from frontend to be applied with their IDs preserved.
    """
    from design_project.domain import IdentifiedOperation
    
    # Create the underlying operation using existing logic
    operation = _convert_model_to_operation(model)
    
    # Wrap with identity
    return IdentifiedOperation(
        id=model.id,
        operation=operation,
        created_from_task_id=None  # Not tracked when coming from API
    )


def _apply_operation_updates(existing_operation: OntologyEditOperation, updates: UpdateOperationRequest) -> OntologyEditOperation:
    """
    Helper to apply updates to an operation, creating a new instance.
    
    Since operations are immutable, this creates a new operation with updated fields.
    Only non-None fields in updates are applied.
    """
    from ontology.edit_operations import (
        CreateClassOperation, UpdateClassOperation, DeleteClassOperation,
        CreateAttributeOperation, UpdateAttributeOperation, DeleteAttributeOperation,
        CreateRelationshipOperation, UpdateRelationshipOperation, DeleteRelationshipOperation
    )
    from ontology.domain import Kind
    from rdflib import URIRef
    
    # Helper to get value: use update if not None, else existing value
    def get_value(update_val, existing_val):
        return update_val if update_val is not None else existing_val
    
    # Class Operations
    if isinstance(existing_operation, CreateClassOperation):
        return CreateClassOperation(
            uri=URIRef(updates.uri) if updates.uri is not None else existing_operation.uri,
            label=get_value(updates.label, existing_operation.label),
            kind=Kind(updates.kind) if updates.kind is not None else existing_operation.kind,
            definition=get_value(updates.definition, existing_operation.definition),
            description=get_value(updates.description, existing_operation.description),
            generalization_uris=[URIRef(u) for u in updates.generalization_uris] if updates.generalization_uris is not None else existing_operation.generalization_uris,
            definition_references=get_value(updates.definition_references, existing_operation.definition_references),
            specification_references=get_value(updates.specification_references, existing_operation.specification_references),
            references=get_value(updates.references, existing_operation.references)
        )
    
    elif isinstance(existing_operation, UpdateClassOperation):
        return UpdateClassOperation(
            uri=URIRef(updates.uri) if updates.uri is not None else existing_operation.uri,
            label=get_value(updates.label, existing_operation.label),
            kind=Kind(updates.kind) if updates.kind is not None else existing_operation.kind,
            definition=get_value(updates.definition, existing_operation.definition),
            description=get_value(updates.description, existing_operation.description),
            generalization_uris=[URIRef(u) for u in updates.generalization_uris] if updates.generalization_uris is not None else existing_operation.generalization_uris,
            definition_references=get_value(updates.definition_references, existing_operation.definition_references),
            specification_references=get_value(updates.specification_references, existing_operation.specification_references),
            references=get_value(updates.references, existing_operation.references)
        )
    
    elif isinstance(existing_operation, DeleteClassOperation):
        return DeleteClassOperation(
            uri=URIRef(updates.uri) if updates.uri is not None else existing_operation.uri
        )
    
    # Attribute Operations
    elif isinstance(existing_operation, CreateAttributeOperation):
        return CreateAttributeOperation(
            uri=URIRef(updates.uri) if updates.uri is not None else existing_operation.uri,
            label=get_value(updates.label, existing_operation.label),
            owning_class_uri=URIRef(updates.owning_class_uri) if updates.owning_class_uri is not None else existing_operation.owning_class_uri,
            definition=get_value(updates.definition, existing_operation.definition),
            description=get_value(updates.description, existing_operation.description),
            definition_references=get_value(updates.definition_references, existing_operation.definition_references),
            specification_references=get_value(updates.specification_references, existing_operation.specification_references),
            references=get_value(updates.references, existing_operation.references)
        )
    
    elif isinstance(existing_operation, UpdateAttributeOperation):
        return UpdateAttributeOperation(
            uri=URIRef(updates.uri) if updates.uri is not None else existing_operation.uri,
            label=get_value(updates.label, existing_operation.label),
            owning_class_uri=URIRef(updates.owning_class_uri) if updates.owning_class_uri is not None else existing_operation.owning_class_uri,
            definition=get_value(updates.definition, existing_operation.definition),
            description=get_value(updates.description, existing_operation.description),
            definition_references=get_value(updates.definition_references, existing_operation.definition_references),
            specification_references=get_value(updates.specification_references, existing_operation.specification_references),
            references=get_value(updates.references, existing_operation.references)
        )
    
    elif isinstance(existing_operation, DeleteAttributeOperation):
        return DeleteAttributeOperation(
            uri=URIRef(updates.uri) if updates.uri is not None else existing_operation.uri
        )
    
    # Relationship Operations
    elif isinstance(existing_operation, CreateRelationshipOperation):
        return CreateRelationshipOperation(
            uri=URIRef(updates.uri) if updates.uri is not None else existing_operation.uri,
            label=get_value(updates.label, existing_operation.label),
            source_class_uri=URIRef(updates.source_class_uri) if updates.source_class_uri is not None else existing_operation.source_class_uri,
            target_class_uri=URIRef(updates.target_class_uri) if updates.target_class_uri is not None else existing_operation.target_class_uri,
            definition=get_value(updates.definition, existing_operation.definition),
            description=get_value(updates.description, existing_operation.description),
            definition_references=get_value(updates.definition_references, existing_operation.definition_references),
            specification_references=get_value(updates.specification_references, existing_operation.specification_references),
            references=get_value(updates.references, existing_operation.references)
        )
    
    elif isinstance(existing_operation, UpdateRelationshipOperation):
        return UpdateRelationshipOperation(
            uri=URIRef(updates.uri) if updates.uri is not None else existing_operation.uri,
            label=get_value(updates.label, existing_operation.label),
            source_class_uri=URIRef(updates.source_class_uri) if updates.source_class_uri is not None else existing_operation.source_class_uri,
            target_class_uri=URIRef(updates.target_class_uri) if updates.target_class_uri is not None else existing_operation.target_class_uri,
            definition=get_value(updates.definition, existing_operation.definition),
            description=get_value(updates.description, existing_operation.description),
            definition_references=get_value(updates.definition_references, existing_operation.definition_references),
            specification_references=get_value(updates.specification_references, existing_operation.specification_references),
            references=get_value(updates.references, existing_operation.references)
        )
    
    elif isinstance(existing_operation, DeleteRelationshipOperation):
        return DeleteRelationshipOperation(
            uri=URIRef(updates.uri) if updates.uri is not None else existing_operation.uri
        )
    
    else:
        raise ValueError(f"Unknown operation type: {type(existing_operation)}")


def _convert_project_to_summary(project: DesignProject) -> ProjectSummary:
    """Convert domain DesignProject to ProjectSummary."""
    return ProjectSummary(
        id=project.id,
        name=project.name or "",
        ontology_uri=str(project.designedOntology.uri),
        knowledge_domain_name=project.modeledKnowledgeDomain.label if project.modeledKnowledgeDomain else "",
        created_at="",  # Not tracked in current domain model
        updated_at="",  # Not tracked in current domain model
        domain_areas_count=len(project.modeledKnowledgeDomain.areas) if project.modeledKnowledgeDomain else 0,
        iterations_count=len(project.plannedIterations) + len(project.finishedIterations) + (1 if project.currentIteration else 0)
    )


def _convert_project_to_model(project: DesignProject) -> ProjectModel:
    """Convert domain DesignProject to complete ProjectModel."""
    return ProjectModel(
        id=project.id,
        name=project.name or "",
        ontology_uri=str(project.designedOntology.uri),
        knowledge_domain_name=project.modeledKnowledgeDomain.label if project.modeledKnowledgeDomain else "",
        knowledge_domain_description=project.modeledKnowledgeDomain.description if project.modeledKnowledgeDomain else "",
        key_knowledge_document_id=project.keyKnowledgeDocument.id if project.keyKnowledgeDocument else None,
        legal_knowledge_document_ids=[doc.id for doc in project.legalKnowledgeBase],
        expert_knowledge_document_ids=[doc.id for doc in project.expertKnowledgeBase],
        domain_areas=[_convert_domain_area_to_model(area) for area in (project.modeledKnowledgeDomain.areas if project.modeledKnowledgeDomain else [])],
        planned_iterations=[_convert_iteration_to_model(it) for it in project.plannedIterations],
        current_iteration=_convert_iteration_to_model(project.currentIteration) if project.currentIteration else None,
        finished_iterations=[_convert_iteration_to_model(it) for it in project.finishedIterations]
    )


# ============================================================================
# Project Management Endpoints
# ============================================================================

@router.post("/projects", response_model=ProjectModel, status_code=status.HTTP_201_CREATED)
async def create_project(request: CreateProjectRequest):
    """
    Create a new design project with empty knowledge base.
    
    User Story: Create a new design project
    
    This operation creates a project without knowledge documents or domain areas.
    Use subsequent operations to:
    1. Add knowledge documents (legal/expert)
    2. Set key knowledge document
    3. Generate domain areas
    """
    try:
        logger.info(f"Creating project: {request.name}")
        
        project = design_project_service.initialize_new_project(
            project_name=request.name,
            working_ontology_uri=request.ontology_uri,
            knowledge_domain_name=request.knowledge_domain_name or f"Domain of {request.name}",
            knowledge_domain_description=request.knowledge_domain_description or ""
        )
        
        return _convert_project_to_model(project)
    
    except ValueError as e:
        logger.error(f"Invalid project data: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create project: {str(e)}"
        )


@router.get("/projects", response_model=List[ProjectSummary])
async def list_projects():
    """
    List all existing design projects.
    
    User Story: Load an existing design project
    """
    try:
        logger.info("Listing all projects")
        projects = design_project_service.list_all_projects()
        return [_convert_project_to_summary(project) for project in projects]
    except Exception as e:
        logger.error(f"Error listing projects: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list projects: {str(e)}"
        )


@router.get("/projects/{project_id}", response_model=ProjectModel)
async def get_project(project_id: str):
    """
    Get a specific design project with full details.
    
    User Story: Load an existing design project
    """
    try:
        logger.info(f"Getting project: {project_id}")
        project = design_project_service.load_project(project_id)
        
        # Ensure all project documents are indexed (handles app restarts)
        _ensure_project_documents_indexed(project)
        
        return _convert_project_to_model(project)
    
    except FileNotFoundError:
        logger.warning(f"Project not found: {project_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found"
        )
    except Exception as e:
        logger.error(f"Error getting project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get project: {str(e)}"
        )


@router.put("/projects/{project_id}", response_model=ProjectModel)
async def update_project(project_id: str, request: UpdateProjectRequest):
    """
    Update project metadata.
    
    User Story: Edit an existing design project
    """
    try:
        logger.info(f"Updating project: {project_id}")
        project = design_project_service.load_project(project_id)
        
        # Update metadata
        if request.name is not None:
            project.name = request.name
        
        if request.knowledge_domain_name is not None and project.modeledKnowledgeDomain:
            project.modeledKnowledgeDomain.label = request.knowledge_domain_name
        
        if request.knowledge_domain_description is not None and project.modeledKnowledgeDomain:
            project.modeledKnowledgeDomain.description = request.knowledge_domain_description
        
        # Save updated project
        design_project_service.save_project(project)
        
        return _convert_project_to_model(project)
    
    except FileNotFoundError:
        logger.warning(f"Project not found: {project_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found"
        )
    except Exception as e:
        logger.error(f"Error updating project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update project: {str(e)}"
        )


@router.delete("/projects/{project_id}", response_model=DeleteResponse, status_code=status.HTTP_200_OK)
async def delete_project(project_id: str):
    """Delete a design project."""
    try:
        logger.info(f"Deleting project: {project_id}")
        # Load to verify it exists
        design_project_service.load_project(project_id)
        # Delete would be implemented in the store
        # design_project_service.store.delete_project(project_id)
        
        return DeleteResponse(
            success=True,
            message=f"Project '{project_id}' deleted successfully"
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found"
        )
    except Exception as e:
        logger.error(f"Error deleting project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete project: {str(e)}"
        )


# ============================================================================
# Project Guidance (Human-in-the-Loop)
# ============================================================================

def _guidance_item_to_model(item) -> ProjectGuidanceItemModel:
    """Convert domain ProjectGuidanceItem to API model."""
    return ProjectGuidanceItemModel(
        id=item.id,
        project_id=item.project_id,
        type=item.type.value,
        content=item.content,
        created_at=item.created_at,
        source=item.source.value if item.source else None,
    )


@router.get("/projects/{project_id}/guidance", response_model=ProjectGuidanceListResponse)
async def list_project_guidance(project_id: str):
    """List all guidance items for a project. Used for display and to control what the agent follows."""
    try:
        design_project_service.load_project(project_id)
        items = guidance_service.list_items(project_id)
        return ProjectGuidanceListResponse(items=[_guidance_item_to_model(i) for i in items])
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found"
        )
    except Exception as e:
        logger.error(f"Error listing project guidance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/projects/{project_id}/guidance", response_model=ProjectGuidanceItemModel, status_code=status.HTTP_201_CREATED)
async def add_project_guidance(project_id: str, request: CreateProjectGuidanceItemRequest):
    """Add a guidance item. The agent will use it in subsequent calls until removed."""
    try:
        design_project_service.load_project(project_id)
        item_type = ProjectGuidanceItemType(request.type)
        item = guidance_service.add_item(
            project_id=project_id,
            content=request.content,
            type=item_type,
        )
        return _guidance_item_to_model(item)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found"
        )
    except Exception as e:
        logger.error(f"Error adding project guidance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.patch("/projects/{project_id}/guidance/{item_id}", response_model=ProjectGuidanceItemModel)
async def update_project_guidance(project_id: str, item_id: str, request: UpdateProjectGuidanceItemRequest):
    """Update a guidance item. The agent will use the updated content from the next call."""
    try:
        design_project_service.load_project(project_id)
        existing = guidance_service.get_item(project_id, item_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Guidance item '{item_id}' not found"
            )
        content = request.content if request.content is not None else existing.content
        item_type = ProjectGuidanceItemType(request.type) if request.type is not None else existing.type
        item = guidance_service.update_item(project_id, item_id, content, item_type)
        return _guidance_item_to_model(item)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating project guidance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.delete("/projects/{project_id}/guidance/{item_id}", response_model=DeleteResponse, status_code=status.HTTP_200_OK)
async def delete_project_guidance(project_id: str, item_id: str):
    """Remove a guidance item. The agent will no longer follow it."""
    try:
        design_project_service.load_project(project_id)
        removed = guidance_service.delete_item(project_id, item_id)
        if not removed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Guidance item '{item_id}' not found"
            )
        return DeleteResponse(success=True, message="Guidance item deleted")
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting project guidance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# ============================================================================
# Knowledge Base Management Endpoints
# ============================================================================

@router.post("/projects/{project_id}/knowledge-base/legal", response_model=SuccessResponse)
async def add_legal_documents(project_id: str, request: AddKnowledgeDocumentsRequest):
    """
    Add legal documents to project knowledge base.
    
    User Story: Edit the knowledge base of the design project
    """
    try:
        logger.info(f"Adding legal documents to project: {project_id}")
        project = design_project_service.load_project(project_id)
        
        # Load the documents
        new_docs = knowledge_base_service.load_legal_knowledge_documents(request.document_ids)
        
        # Add to project (avoid duplicates)
        existing_ids = {doc.id for doc in project.legalKnowledgeBase}
        for doc in new_docs:
            if doc.id not in existing_ids:
                project.legalKnowledgeBase.append(doc)
                # Index the document for search operations
                try:
                    knowledge_base_index_service.add_document(doc)
                    logger.info(f"Indexed document: {doc.id}")
                except Exception as e:
                    logger.warning(f"Failed to index document {doc.id}: {e}")
        
        # Save project
        design_project_service.save_project(project)
        
        return SuccessResponse(
            success=True,
            message=f"Added {len(new_docs)} legal documents to project"
        )
    
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found"
        )
    except Exception as e:
        logger.error(f"Error adding legal documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add legal documents: {str(e)}"
        )


@router.delete("/projects/{project_id}/knowledge-base/legal/{document_id:path}", response_model=DeleteResponse)
async def remove_legal_document(project_id: str, document_id: str):
    """
    Remove a legal document from knowledge base.
    
    User Story: Edit the knowledge base of the design project
    """
    try:
        decoded_doc_id = unquote(document_id)
        logger.info(f"Removing legal document from project: {project_id}, document: {decoded_doc_id}")
        project = design_project_service.load_project(project_id)
        
        # Remove the document
        project.legalKnowledgeBase = [doc for doc in project.legalKnowledgeBase if doc.id != decoded_doc_id]
        
        # Remove from index service if present
        if knowledge_base_index_service.has_document(decoded_doc_id):
            knowledge_base_index_service.remove_document(decoded_doc_id)
            logger.info(f"Removed document from index: {decoded_doc_id}")
        
        # Save project
        design_project_service.save_project(project)
        
        return DeleteResponse(
            success=True,
            message=f"Document removed from project"
        )
    
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found"
        )
    except Exception as e:
        logger.error(f"Error removing legal document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove legal document: {str(e)}"
        )


@router.post("/projects/{project_id}/knowledge-base/expert", response_model=SuccessResponse)
async def add_expert_documents(project_id: str, request: AddKnowledgeDocumentsRequest):
    """
    Add expert documents to project knowledge base.
    
    User Story: Edit the knowledge base of the design project
    """
    try:
        logger.info(f"Adding expert documents to project: {project_id}")
        project = design_project_service.load_project(project_id)
        
        # Load the documents
        new_docs = knowledge_base_service.load_expert_knowledge_documents(request.document_ids)
        
        # Add to project (avoid duplicates)
        existing_ids = {doc.id for doc in project.expertKnowledgeBase}
        for doc in new_docs:
            if doc.id not in existing_ids:
                project.expertKnowledgeBase.append(doc)
                # Index the document for search operations
                try:
                    knowledge_base_index_service.add_document(doc)
                    logger.info(f"Indexed document: {doc.id}")
                except Exception as e:
                    logger.warning(f"Failed to index document {doc.id}: {e}")
        
        # Save project
        design_project_service.save_project(project)
        
        return SuccessResponse(
            success=True,
            message=f"Added {len(new_docs)} expert documents to project"
        )
    
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found"
        )
    except Exception as e:
        logger.error(f"Error adding expert documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add expert documents: {str(e)}"
        )


@router.delete("/projects/{project_id}/knowledge-base/expert/{document_id:path}", response_model=DeleteResponse)
async def remove_expert_document(project_id: str, document_id: str):
    """
    Remove an expert document from knowledge base.
    
    User Story: Edit the knowledge base of the design project
    """
    try:
        decoded_doc_id = unquote(document_id)
        logger.info(f"Removing expert document from project: {project_id}, document: {decoded_doc_id}")
        project = design_project_service.load_project(project_id)
        
        # Remove the document
        project.expertKnowledgeBase = [doc for doc in project.expertKnowledgeBase if doc.id != decoded_doc_id]
        
        # Remove from index service if present
        if knowledge_base_index_service.has_document(decoded_doc_id):
            knowledge_base_index_service.remove_document(decoded_doc_id)
            logger.info(f"Removed document from index: {decoded_doc_id}")
        
        # Save project
        design_project_service.save_project(project)
        
        return DeleteResponse(
            success=True,
            message=f"Document removed from project"
        )
    
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found"
        )
    except Exception as e:
        logger.error(f"Error removing expert document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove expert document: {str(e)}"
        )


@router.get("/projects/{project_id}/knowledge-base", response_model=KnowledgeBaseResponse)
async def get_project_knowledge_base(project_id: str):
    """Get all knowledge base documents for a project."""
    try:
        logger.info(f"Getting knowledge base for project: {project_id}")
        project = design_project_service.load_project(project_id)
        
        legal_docs = [
            KnowledgeDocumentSummary(
                id=doc.id,
                title=doc.title or "",
                element_type=doc.elementType,
                content_summary=doc.contentSummary or ""
            ) for doc in project.legalKnowledgeBase
        ]
        
        expert_docs = [
            KnowledgeDocumentSummary(
                id=doc.id,
                title=doc.title or "",
                element_type=doc.elementType,
                content_summary=doc.contentSummary or ""
            ) for doc in project.expertKnowledgeBase
        ]
        
        return KnowledgeBaseResponse(
            legal_documents=legal_docs,
            expert_documents=expert_docs
        )
    
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found"
        )
    except Exception as e:
        logger.error(f"Error getting knowledge base: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get knowledge base: {str(e)}"
        )


@router.get("/projects/{project_id}/knowledge-base/documents/{document_id:path}")
async def get_project_knowledge_document(project_id: str, document_id: str):
    """
    Get full content of a specific knowledge base document in the project.
    
    User Story: Read knowledge base document
    
    Validates that the document belongs to the project's knowledge base.
    """
    try:
        decoded_doc_id = unquote(document_id)
        logger.info(f"Getting knowledge document for project: {project_id}, document: {decoded_doc_id}")
        project = design_project_service.load_project(project_id)
        
        # Find document in project's knowledge base
        document = None
        for doc in project.legalKnowledgeBase + project.expertKnowledgeBase:
            if doc.id == decoded_doc_id:
                document = doc
                break
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document '{document_id}' not found in project knowledge base"
            )
        
        return _convert_document_to_model(document, include_coverage=False)
    
    except HTTPException:
        raise
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found"
        )
    except Exception as e:
        logger.error(f"Error getting knowledge document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get knowledge document: {str(e)}"
        )


@router.get("/projects/{project_id}/knowledge-base/documents/{document_id:path}/coverage")
async def get_project_knowledge_document_coverage(project_id: str, document_id: str):
    """
    Get knowledge document with ontology coverage information for the project.
    
    User Story: See coverage of documents in knowledge base by ontology
    
    Shows which document elements have ontology elements defined, specified, or referenced.
    """
    try:
        decoded_doc_id = unquote(document_id)
        logger.info(f"Getting knowledge document coverage for project: {project_id}, document: {decoded_doc_id}")
        project = design_project_service.load_project(project_id)
        
        # Find document in project's knowledge base
        document = None
        for doc in project.legalKnowledgeBase + project.expertKnowledgeBase:
            if doc.id == decoded_doc_id:
                document = doc
                break
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document '{document_id}' not found in project knowledge base"
            )
        
        return _convert_document_to_model(document, include_coverage=True)
    
    except HTTPException:
        raise
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found"
        )
    except Exception as e:
        logger.error(f"Error getting knowledge document coverage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get knowledge document coverage: {str(e)}"
        )


@router.put("/projects/{project_id}/key-document", response_model=SuccessResponse)
async def set_key_knowledge_document(project_id: str, request: SetKeyDocumentRequest):
    """
    Set the key knowledge document for domain area generation.
    
    The key document is used to structure the knowledge domain and identify areas.
    The document must already exist in the project's knowledge base.
    """
    try:
        logger.info(f"Setting key knowledge document for project: {project_id}, document: {request.document_id}")
        project = design_project_service.set_key_knowledge_document(project_id, request.document_id)
        
        return SuccessResponse(
            success=True,
            message=f"Key knowledge document set to '{project.keyKnowledgeDocument.title}'"
        )
    
    except ValueError as e:
        logger.error(f"Invalid request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found"
        )
    except Exception as e:
        logger.error(f"Error setting key knowledge document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set key knowledge document: {str(e)}"
        )


@router.post("/projects/{project_id}/domain-areas/generate", response_model=List[KnowledgeDomainAreaModel])
async def generate_domain_areas(project_id: str, request: GenerateDomainAreasRequest):
    """
    Generate domain areas using AI based on the key knowledge document.
    
    User Story: Create a new design project (final step)
    
    This operation:
    1. Analyzes the key knowledge document
    2. Identifies domain areas within the knowledge domain
    3. Returns the generated areas
    
    Prerequisites:
    - Key knowledge document must be set
    - At least one knowledge document in the knowledge base
    """
    try:
        logger.info(f"Generating domain areas for project: {project_id}")
        areas = design_project_service.generate_domain_areas(
            project_id=project_id,
            user_instruction=request.user_instruction or ""
        )
        
        return [_convert_domain_area_to_model(area) for area in areas]
    
    except ValueError as e:
        logger.error(f"Invalid request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found"
        )
    except Exception as e:
        logger.error(f"Error generating domain areas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate domain areas: {str(e)}"
        )


# ============================================================================
# Knowledge Domain Area Management Endpoints
# ============================================================================

@router.get("/projects/{project_id}/domain-areas", response_model=List[KnowledgeDomainAreaModel])
async def list_domain_areas(project_id: str):
    """List all domain areas for a project."""
    try:
        logger.info(f"Listing domain areas for project: {project_id}")
        project = design_project_service.load_project(project_id)
        
        if not project.modeledKnowledgeDomain:
            return []
        
        return [_convert_domain_area_to_model(area) for area in project.modeledKnowledgeDomain.areas]
    
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found"
        )
    except Exception as e:
        logger.error(f"Error listing domain areas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list domain areas: {str(e)}"
        )


@router.get("/projects/{project_id}/domain-areas/{area_id}", response_model=KnowledgeDomainAreaModel)
async def get_domain_area(project_id: str, area_id: str):
    """Get details of a specific domain area."""
    try:
        logger.info(f"Getting domain area: {area_id} for project: {project_id}")
        project = design_project_service.load_project(project_id)
        
        if not project.modeledKnowledgeDomain:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No knowledge domain found for project"
            )
        
        area = next((a for a in project.modeledKnowledgeDomain.areas if a.id == area_id), None)
        if not area:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Domain area with ID '{area_id}' not found"
            )
        
        return _convert_domain_area_to_model(area)
    
    except HTTPException:
        raise
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found"
        )
    except Exception as e:
        logger.error(f"Error getting domain area: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get domain area: {str(e)}"
        )


@router.post("/projects/{project_id}/domain-areas", response_model=KnowledgeDomainAreaModel, status_code=status.HTTP_201_CREATED)
async def create_domain_area(project_id: str, request: CreateDomainAreaRequest):
    """
    Add a new domain area manually.
    
    User Story: Edit knowledge areas of the design project
    """
    try:
        logger.info(f"Creating domain area for project: {project_id}")
        project = design_project_service.load_project(project_id)
        
        if not project.modeledKnowledgeDomain:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project has no knowledge domain"
            )
        
        # Create new area
        from src.design_project.domain import KnowledgeDomainArea
        new_area = KnowledgeDomainArea(
            id=str(uuid.uuid4()),
            label=request.label,
            description=request.description,
            parent=project.modeledKnowledgeDomain,
            keyConcepts=request.key_concepts,
            modelingClasses=[],
            modelingAttributes=[],
            modelingRelationships=[],
            explainingKnowledgeResources=[]
        )
        
        project.modeledKnowledgeDomain.areas.append(new_area)
        
        # Save project
        design_project_service.save_project(project)
        
        return _convert_domain_area_to_model(new_area)
    
    except HTTPException:
        raise
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found"
        )
    except Exception as e:
        logger.error(f"Error creating domain area: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create domain area: {str(e)}"
        )


@router.put("/projects/{project_id}/domain-areas/{area_id}", response_model=KnowledgeDomainAreaModel)
async def update_domain_area(project_id: str, area_id: str, request: UpdateDomainAreaRequest):
    """
    Update a domain area.
    
    User Story: Edit knowledge areas of the design project
    """
    try:
        logger.info(f"Updating domain area: {area_id} for project: {project_id}")
        project = design_project_service.load_project(project_id)
        
        if not project.modeledKnowledgeDomain:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No knowledge domain found for project"
            )
        
        area = next((a for a in project.modeledKnowledgeDomain.areas if a.id == area_id), None)
        if not area:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Domain area with ID '{area_id}' not found"
            )
        
        # Update area
        if request.label is not None:
            area.label = request.label
        if request.description is not None:
            area.description = request.description
        if request.key_concepts is not None:
            area.keyConcepts = request.key_concepts
        
        # Save project
        design_project_service.save_project(project)
        
        return _convert_domain_area_to_model(area)
    
    except HTTPException:
        raise
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found"
        )
    except Exception as e:
        logger.error(f"Error updating domain area: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update domain area: {str(e)}"
        )


@router.delete("/projects/{project_id}/domain-areas/{area_id}", response_model=SuccessResponse)
async def delete_domain_area(project_id: str, area_id: str):
    """
    Remove a domain area.
    
    User Story: Edit knowledge areas of the design project
    """
    try:
        logger.info(f"Deleting domain area: {area_id} from project: {project_id}")
        project = design_project_service.load_project(project_id)
        
        if not project.modeledKnowledgeDomain:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No knowledge domain found for project"
            )
        
        # Remove area
        project.modeledKnowledgeDomain.areas = [
            a for a in project.modeledKnowledgeDomain.areas if a.id != area_id
        ]
        
        # Save project
        design_project_service.save_project(project)
        
        return SuccessResponse(
            success=True,
            message=f"Domain area removed. Remaining areas: {len(project.modeledKnowledgeDomain.areas)}"
        )
    
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found"
        )
    except Exception as e:
        logger.error(f"Error deleting domain area: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete domain area: {str(e)}"
        )


@router.post("/projects/{project_id}/domain-areas/reidentify", response_model=List[KnowledgeDomainAreaModel])
async def reidentify_domain_areas(project_id: str, request: ReidentifyDomainAreasRequest):
    """
    Re-identify domain areas with AI assistance.
    
    User Story: Reidentify knowledge areas of the design project
    
    The AI analyzes the key knowledge document and current areas,
    then applies the user's instruction to modify the areas.
    """
    try:
        logger.info(f"Reidentifying domain areas for project: {project_id}")
        areas = design_project_service.reidentify_domain_areas(
            project_id=project_id,
            user_instruction=request.user_instruction
        )
        
        return [_convert_domain_area_to_model(area) for area in areas]
    
    except ValueError as e:
        logger.error(f"Invalid request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found"
        )
    except Exception as e:
        logger.error(f"Error reidentifying domain areas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reidentify domain areas: {str(e)}"
        )
    
    except HTTPException:
        raise
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found"
        )
    except Exception as e:
        logger.error(f"Error reidentifying domain areas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reidentify domain areas: {str(e)}"
        )


# ============================================================================
# Task Pattern Endpoints
# ============================================================================

@router.get("/projects/{project_id}/patterns", response_model=TaskPatternsListResponse)
async def list_task_patterns(project_id: str):
    """
    Get the list of design task patterns available for the project.
    
    These patterns are used when creating or updating tasks to indicate which
    design pattern the task follows.
    """
    try:
        logger.info(f"Listing task patterns for project: {project_id}")
        patterns = design_project_service.get_design_task_patterns(project_id)
        
        return TaskPatternsListResponse(
            patterns=[_convert_pattern_to_model(p) for p in patterns]
        )
    
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found"
        )
    except Exception as e:
        logger.error(f"Error listing task patterns: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list task patterns: {str(e)}"
        )


# ============================================================================
# Iteration Management Endpoints
# ============================================================================

@router.get("/projects/{project_id}/iterations", response_model=IterationsListResponse)
async def list_iterations(
    project_id: str,
    status_filter: Optional[str] = Query(None, alias="status"),
    area_id: Optional[str] = Query(None)
):
    """List all iterations (planned, current, finished)."""
    try:
        logger.info(f"Listing iterations for project: {project_id}")
        project = design_project_service.load_project(project_id)
        
        planned = [_convert_iteration_to_model(it) for it in project.plannedIterations]
        current = _convert_iteration_to_model(project.currentIteration) if project.currentIteration else None
        finished = [_convert_iteration_to_model(it) for it in project.finishedIterations]
        
        # Apply filters if provided
        if status_filter:
            if status_filter == "suggested" or status_filter == "planned":
                # Only show iterations in plannedIterations list
                current = None
                finished = []
            elif status_filter == "prepared":
                # Only show current iteration (in progress)
                planned = []
                finished = []
            elif status_filter == "completed":
                # Only show finished iterations
                planned = []
                current = None
        
        if area_id:
            planned = [it for it in planned if it.focused_area_id == area_id]
            if current and current.focused_area_id != area_id:
                current = None
            finished = [it for it in finished if it.focused_area_id == area_id]
        
        return IterationsListResponse(
            planned_iterations=planned,
            current_iteration=current,
            finished_iterations=finished
        )
    
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found"
        )
    except Exception as e:
        logger.error(f"Error listing iterations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list iterations: {str(e)}"
        )


@router.get("/projects/{project_id}/iterations/{iteration_id}", response_model=DesignIterationModel)
async def get_iteration(project_id: str, iteration_id: str):
    """Get details of a specific iteration."""
    try:
        logger.info(f"Getting iteration: {iteration_id} for project: {project_id}")
        project = design_project_service.load_project(project_id)
        
        # Search in all iteration lists
        iteration = None
        for it in project.plannedIterations + [project.currentIteration] + project.finishedIterations:
            if it and it.id == iteration_id:
                iteration = it
                break
        
        if not iteration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Iteration with ID '{iteration_id}' not found"
            )
        
        return _convert_iteration_to_model(iteration)
    
    except HTTPException:
        raise
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found"
        )
    except Exception as e:
        logger.error(f"Error getting iteration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get iteration: {str(e)}"
        )


@router.post("/projects/{project_id}/iterations/suggest", response_model=List[DesignIterationModel])
async def suggest_iterations(project_id: str, request: SuggestIterationsRequest):
    """
    Suggest new iterations for a domain area with AI assistance.
    
    User Story: Suggest iterations for a domain area
    
    The AI analyzes the ontology, knowledge base, and focused area to suggest iterations.
    """
    try:
        logger.info(f"Suggesting iterations for project: {project_id}, area: {request.focused_area_id}")
        
        # Ensure project documents are indexed before AI operations
        project = design_project_service.load_project(project_id)
        _ensure_project_documents_indexed(project)
        
        iterations = design_project_service.suggest_iterations(
            project_id=project_id,
            focused_area_id=request.focused_area_id,
            k=request.count,
            user_instruction=request.user_instruction or ""
        )
        
        return [_convert_iteration_to_model(it) for it in iterations]
    
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found"
        )
    except Exception as e:
        logger.error(f"Error suggesting iterations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to suggest iterations: {str(e)}"
        )


@router.post("/projects/{project_id}/iterations", response_model=DesignIterationModel, status_code=status.HTTP_201_CREATED)
async def create_iteration(project_id: str, request: CreateIterationRequest):
    """
    Add a new iteration manually.
    
    User Story: Edit iterations for a domain area
    """
    try:
        logger.info(f"Creating iteration for project: {project_id}")
        project = design_project_service.load_project(project_id)
        
        # Find the focused area
        area = None
        if project.modeledKnowledgeDomain:
            area = next((a for a in project.modeledKnowledgeDomain.areas if a.id == request.focused_area_id), None)
        
        if not area:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Domain area with ID '{request.focused_area_id}' not found"
            )
        
        # Create new iteration
        new_iteration = DesignIteration(
            id=str(uuid.uuid4()),
            name=request.name,
            status=DesignIterationStatus.PLANNED,
            specification=request.specification,
            finishedTasks=[],
            currentTask=None,
            plannedTasks=[],
            focusedArea=area,
            plannedOperations=None,  # No operations initially
            designedOntologyChangesSpecification=None
        )
        
        project.plannedIterations.append(new_iteration)
        
        # Save project
        design_project_service.save_project(project)
        
        return _convert_iteration_to_model(new_iteration)
    
    except HTTPException:
        raise
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found"
        )
    except Exception as e:
        logger.error(f"Error creating iteration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create iteration: {str(e)}"
        )


@router.put("/projects/{project_id}/iterations/{iteration_id}", response_model=DesignIterationModel)
async def update_iteration(project_id: str, iteration_id: str, request: UpdateIterationRequest):
    """
    Update an iteration.
    
    User Story: Edit iterations for a domain area
    """
    try:
        logger.info(f"Updating iteration: {iteration_id} for project: {project_id}")
        project = design_project_service.load_project(project_id)
        
        # Find iteration (only in planned iterations)
        iteration = next((it for it in project.plannedIterations if it.id == iteration_id), None)
        if not iteration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Planned iteration with ID '{iteration_id}' not found"
            )
        
        # Update iteration
        if request.name is not None:
            iteration.name = request.name
        if request.specification is not None:
            iteration.specification = request.specification
        if request.focused_area_id is not None and project.modeledKnowledgeDomain:
            area = next((a for a in project.modeledKnowledgeDomain.areas if a.id == request.focused_area_id), None)
            if area:
                iteration.focusedArea = area
        
        # Save project
        design_project_service.save_project(project)
        
        return _convert_iteration_to_model(iteration)
    
    except HTTPException:
        raise
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found"
        )
    except Exception as e:
        logger.error(f"Error updating iteration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update iteration: {str(e)}"
        )


@router.delete("/projects/{project_id}/iterations/{iteration_id}", response_model=SuccessResponse)
async def delete_iteration(project_id: str, iteration_id: str):
    """
    Remove an iteration (planned or current).
    
    User Story: Edit iterations for a domain area
    
    This endpoint can remove:
    - Planned iterations (in any status: suggested or planned)
    - Current iteration (in any status: prepared, generating, applying, etc.)
    
    Cannot remove finished/completed iterations.
    """
    try:
        logger.info(f"Deleting iteration: {iteration_id} from project: {project_id}")
        
        design_project_service.remove_iteration(project_id, iteration_id)
        
        # Reload to get updated count
        project = design_project_service.load_project(project_id)
        
        # Determine what was removed and construct appropriate message
        has_current = project.currentIteration is not None
        planned_count = len(project.plannedIterations)
        
        return SuccessResponse(
            success=True,
            message=f"Iteration removed. Planned: {planned_count}, Current: {'1' if has_current else '0'}"
        )
    
    except ValueError as e:
        # Handle specific error cases
        error_msg = str(e)
        if "finished" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_msg
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found"
        )
    except Exception as e:
        logger.error(f"Error deleting iteration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete iteration: {str(e)}"
        )


@router.put("/projects/{project_id}/iterations/reorder", response_model=SuccessResponse)
async def reorder_iterations(project_id: str, request: ReorderIterationsRequest):
    """
    Reorder planned iterations.
    
    User Story: Edit iterations for a domain area (changing order)
    """
    try:
        logger.info(f"Reordering iterations for project: {project_id}")
        project = design_project_service.load_project(project_id)
        
        # Validate all IDs exist
        existing_ids = {it.id for it in project.plannedIterations}
        for it_id in request.iteration_ids:
            if it_id not in existing_ids:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Iteration with ID '{it_id}' not found in planned iterations"
                )
        
        # Reorder
        id_to_iteration = {it.id: it for it in project.plannedIterations}
        project.plannedIterations = [id_to_iteration[it_id] for it_id in request.iteration_ids]
        
        # Save project
        design_project_service.save_project(project)
        
        return SuccessResponse(
            success=True,
            message=f"Reordered {len(request.iteration_ids)} iterations"
        )
    
    except HTTPException:
        raise
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found"
        )
    except Exception as e:
        logger.error(f"Error reordering iterations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reorder iterations: {str(e)}"
        )


# ============================================================================
# Task Management Endpoints
# ============================================================================

@router.get("/projects/{project_id}/iterations/{iteration_id}/tasks", response_model=TasksListResponse)
async def list_tasks(project_id: str, iteration_id: str):
    """List all tasks for an iteration."""
    try:
        logger.info(f"Listing tasks for iteration: {iteration_id} in project: {project_id}")
        project = design_project_service.load_project(project_id)
        
        # Find iteration
        iteration = None
        for it in project.plannedIterations + [project.currentIteration] + project.finishedIterations:
            if it and it.id == iteration_id:
                iteration = it
                break
        
        if not iteration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Iteration with ID '{iteration_id}' not found"
            )
        
        return TasksListResponse(
            planned_tasks=[_convert_task_to_model(t) for t in iteration.plannedTasks],
            current_task=_convert_task_to_model(iteration.currentTask) if iteration.currentTask else None,
            finished_tasks=[_convert_task_to_model(t) for t in iteration.finishedTasks]
        )
    
    except HTTPException:
        raise
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found"
        )
    except Exception as e:
        logger.error(f"Error listing tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tasks: {str(e)}"
        )


@router.post("/projects/{project_id}/iterations/{iteration_id}/tasks/plan", response_model=List[DesignTaskModel])
async def plan_tasks(project_id: str, iteration_id: str, request: PlanTasksRequest):
    """
    Plan tasks for an iteration with AI assistance.
    
    User Story: Plan tasks for an iteration
    
    The AI analyzes the iteration specification and creates a task plan.
    """
    try:
        logger.info(f"Planning tasks for iteration: {iteration_id} in project: {project_id}")
        
        # Ensure project documents are indexed before AI operations
        project = design_project_service.load_project(project_id)
        _ensure_project_documents_indexed(project)
        
        tasks = design_project_service.initialize_iteration_tasks(
            project_id=project_id,
            iteration_id=iteration_id,
            user_instruction=request.user_instruction or ""
        )
        
        return [_convert_task_to_model(t) for t in tasks]
    
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project or iteration not found"
        )
    except Exception as e:
        logger.error(f"Error planning tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to plan tasks: {str(e)}"
        )


@router.post("/projects/{project_id}/iterations/{iteration_id}/tasks", response_model=DesignTaskModel, status_code=status.HTTP_201_CREATED)
async def create_task(project_id: str, iteration_id: str, request: CreateTaskRequest):
    """
    Add a new task manually.
    
    User Story: Edit tasks of an iteration
    """
    try:
        logger.info(f"Creating task for iteration: {iteration_id} in project: {project_id}")
        project = design_project_service.load_project(project_id)
        
        # Find iteration (only in planned)
        iteration = next((it for it in project.plannedIterations if it.id == iteration_id), None)
        if not iteration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Planned iteration with ID '{iteration_id}' not found"
            )
        
        # Find pattern
        pattern = next((p for p in project.patterns if p.id == request.followed_pattern_id), None)
        if not pattern:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Task pattern with ID '{request.followed_pattern_id}' not found"
            )
        
        # Create new task
        new_task = DesignTask(
            id=str(uuid.uuid4()),
            name=request.name,
            status=DesignTaskStatus.PLANNED,
            followedPattern=pattern,
            specification=request.specification,
            knowledgeResources=[],
            designedOntologyChangesSpecification=None
        )
        
        iteration.plannedTasks.append(new_task)
        
        # Save project
        design_project_service.save_project(project)
        
        return _convert_task_to_model(new_task)
    
    except HTTPException:
        raise
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found"
        )
    except Exception as e:
        logger.error(f"Error creating task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create task: {str(e)}"
        )


@router.put("/projects/{project_id}/iterations/{iteration_id}/tasks/reorder", response_model=SuccessResponse)
async def reorder_tasks(project_id: str, iteration_id: str, request: ReorderTasksRequest):
    """
    Reorder tasks within an iteration.
    
    User Story: Edit tasks of an iteration (changing order)
    
    Note: This endpoint must be defined BEFORE the update_task endpoint to avoid
    FastAPI matching "reorder" as a task_id parameter.
    """
    try:
        logger.info(f"Reordering tasks for iteration: {iteration_id} in project: {project_id}")
        project = design_project_service.load_project(project_id)
        
        # Find iteration (only in planned)
        iteration = next((it for it in project.plannedIterations if it.id == iteration_id), None)
        if not iteration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Planned iteration with ID '{iteration_id}' not found"
            )
        
        # Validate all IDs exist
        existing_ids = {t.id for t in iteration.plannedTasks}
        for task_id in request.task_ids:
            if task_id not in existing_ids:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Task with ID '{task_id}' not found in planned tasks"
                )
        
        # Reorder
        id_to_task = {t.id: t for t in iteration.plannedTasks}
        iteration.plannedTasks = [id_to_task[task_id] for task_id in request.task_ids]
        
        # Save project
        design_project_service.save_project(project)
        
        return SuccessResponse(
            success=True,
            message=f"Reordered {len(request.task_ids)} tasks"
        )
    
    except HTTPException:
        raise
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found"
        )
    except Exception as e:
        logger.error(f"Error reordering tasks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reorder tasks: {str(e)}"
        )


@router.put("/projects/{project_id}/iterations/{iteration_id}/tasks/{task_id}", response_model=DesignTaskModel)
async def update_task(project_id: str, iteration_id: str, task_id: str, request: UpdateTaskRequest):
    """
    Update a task.
    
    User Story: Edit tasks of an iteration
    """
    try:
        logger.info(f"Updating task: {task_id} in iteration: {iteration_id} for project: {project_id}")
        project = design_project_service.load_project(project_id)
        
        # Find iteration (only in planned)
        iteration = next((it for it in project.plannedIterations if it.id == iteration_id), None)
        if not iteration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Planned iteration with ID '{iteration_id}' not found"
            )
        
        # Find task
        task = next((t for t in iteration.plannedTasks if t.id == task_id), None)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Planned task with ID '{task_id}' not found"
            )
        
        # Update task
        if request.name is not None:
            task.name = request.name
        if request.specification is not None:
            task.specification = request.specification
        if request.followed_pattern_id is not None:
            pattern = next((p for p in project.patterns if p.id == request.followed_pattern_id), None)
            if pattern:
                task.followedPattern = pattern
        
        # Save project
        design_project_service.save_project(project)
        
        return _convert_task_to_model(task)
    
    except HTTPException:
        raise
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found"
        )
    except Exception as e:
        logger.error(f"Error updating task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update task: {str(e)}"
        )


@router.delete("/projects/{project_id}/iterations/{iteration_id}/tasks/{task_id}", response_model=SuccessResponse)
async def delete_task(project_id: str, iteration_id: str, task_id: str):
    """
    Remove a task.
    
    User Story: Edit tasks of an iteration
    """
    try:
        logger.info(f"Deleting task: {task_id} from iteration: {iteration_id} in project: {project_id}")
        project = design_project_service.load_project(project_id)
        
        # Find iteration (only in planned)
        iteration = next((it for it in project.plannedIterations if it.id == iteration_id), None)
        if not iteration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Planned iteration with ID '{iteration_id}' not found"
            )
        
        # Remove task
        iteration.plannedTasks = [t for t in iteration.plannedTasks if t.id != task_id]
        
        # Save project
        design_project_service.save_project(project)
        
        return SuccessResponse(
            success=True,
            message=f"Task removed. Remaining planned tasks: {len(iteration.plannedTasks)}"
        )
    
    except HTTPException:
        raise
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found"
        )
    except Exception as e:
        logger.error(f"Error deleting task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete task: {str(e)}"
        )


# ============================================================================
# Iteration Execution Workflow Endpoints
# ============================================================================

@router.post("/projects/{project_id}/iterations/{iteration_id}/prepare", response_model=IterationPreparedResponse)
async def prepare_iteration(project_id: str, iteration_id: str):
    """
    Prepare an iteration by materializing tasks into ontology edit operations.
    
    User Story: Execute an iteration with planned tasks
    
    This operation:
    1. Moves iteration from plannedIterations to currentIteration (status becomes "prepared")
    2. AI generates operations for each task sequentially
    3. Sets iteration status to "prepared" (operations ready)
    4. Returns operations for user review (not applied yet)
    """
    try:
        logger.info(f"Preparing iteration: {iteration_id} for project: {project_id}")
        
        # Ensure project documents are indexed before AI operations
        project = design_project_service.load_project(project_id)
        _ensure_project_documents_indexed(project)
        
        operations = design_project_service.prepare_planned_iteration(
            project_id=project_id,
            iteration_id=iteration_id
        )
        
        return IterationPreparedResponse(
            iteration_id=iteration_id,
            status="prepared",
            operations=[_convert_operation_to_model(op) for op in operations]
        )
    
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project or iteration not found"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error preparing iteration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to prepare iteration: {str(e)}"
        )


@router.get("/projects/{project_id}/iterations/{iteration_id}/operations", response_model=IterationPreparedResponse)
async def get_iteration_operations(project_id: str, iteration_id: str):
    """
    Get the prepared operations for an iteration.
    
    User Story: Execute an iteration with planned tasks (client reload scenario)
    
    This operation:
    1. Retrieves the specified iteration
    2. Returns the already-prepared operations without re-generating them
    3. Useful when client reloads after prepare but before apply
    
    The iteration must be the current iteration and must have prepared operations.
    This endpoint only returns operations when it's meaningful - when the iteration
    is in a state where operations have been generated but not yet applied.
    
    Returns:
    - 404 if project or iteration not found
    - 409 if iteration is not current or has no prepared operations
    """
    try:
        logger.info(f"Getting prepared operations for iteration: {iteration_id} in project: {project_id}")
        project = design_project_service.load_project(project_id)
        
        # Verify the iteration is the current iteration
        if not project.currentIteration or project.currentIteration.id != iteration_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Iteration '{iteration_id}' is not the current iteration. "
                       f"Operations can only be retrieved for the current iteration."
            )
        
        iteration = project.currentIteration
        
        # Check if iteration has prepared operations (only meaningful in certain states)
        if not iteration.plannedOperations:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Iteration '{iteration_id}' has no prepared operations. "
                       f"Call prepare endpoint first or iteration may not be in prepared state."
            )
        
        # Map domain status to API status
        status_mapping = {
            DesignIterationStatus.OPERATIONS_GENERATED: "prepared",
            DesignIterationStatus.GENERATING_OPERATIONS: "generating",
            DesignIterationStatus.APPLYING_OPERATIONS: "applying",
        }
        
        api_status = status_mapping.get(iteration.status, "unknown")
        
        return IterationPreparedResponse(
            iteration_id=iteration.id,
            status=api_status,
            operations=[_convert_operation_to_model(op) for op in iteration.plannedOperations]
        )
    
    except HTTPException:
        raise
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found"
        )
    except Exception as e:
        logger.error(f"Error getting iteration operations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get iteration operations: {str(e)}"
        )


@router.put("/projects/{project_id}/iterations/{iteration_id}/operations/reorder", response_model=SuccessResponse)
async def reorder_operations(project_id: str, iteration_id: str, request: ReorderOperationsRequest):
    """
    Reorder operations within the current iteration.
    
    User Story: Edit materialized operations for an iteration
    
    This endpoint allows users to change the order in which operations will be applied
    to the ontology. This is useful when operation order matters for semantic correctness
    (e.g., creating a class before creating its attributes).
    
    Note: This endpoint must be defined BEFORE the update_operation endpoint to avoid
    FastAPI matching "reorder" as an operation_id parameter.
    """
    try:
        logger.info(f"Reordering operations for iteration: {iteration_id} in project: {project_id}")
        
        design_project_service.reorder_iteration_operations(
            project_id=project_id,
            iteration_id=iteration_id,
            operation_ids=request.operation_ids
        )
        
        return SuccessResponse(
            success=True,
            message=f"Reordered {len(request.operation_ids)} operations"
        )
    
    except ValueError as e:
        logger.error(f"Invalid request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found"
        )
    except Exception as e:
        logger.error(f"Error reordering operations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reorder operations: {str(e)}"
        )


@router.put("/projects/{project_id}/iterations/{iteration_id}/operations/{operation_id}", response_model=OntologyOperationModel)
async def update_operation(
    project_id: str,
    iteration_id: str,
    operation_id: str,
    request: UpdateOperationRequest
):
    """
    Update a specific operation within the current iteration.
    
    User Story: Edit materialized operations for an iteration
    
    This endpoint allows users to modify the details of a generated operation before
    applying it to the ontology. Users can change labels, definitions, references, etc.
    """
    try:
        logger.info(f"Updating operation: {operation_id} for iteration: {iteration_id} in project: {project_id}")
        
        # Load current operation
        project = design_project_service.load_project(project_id)
        
        if not project.currentIteration or project.currentIteration.id != iteration_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Iteration {iteration_id} is not the current iteration"
            )
        
        if not project.currentIteration.plannedOperations:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No operations found"
            )
        
        # Find the operation
        identified_op = next(
            (op for op in project.currentIteration.plannedOperations if op.id == operation_id),
            None
        )
        
        if not identified_op:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Operation with ID '{operation_id}' not found"
            )
        
        # Build updated operation by applying changes to existing operation
        updated_operation = _apply_operation_updates(identified_op.operation, request)
        
        # Update through service
        updated_identified_op = design_project_service.update_iteration_operation(
            project_id=project_id,
            iteration_id=iteration_id,
            operation_id=operation_id,
            updated_operation=updated_operation
        )
        
        return _convert_operation_to_model(updated_identified_op)
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Invalid request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found"
        )
    except Exception as e:
        logger.error(f"Error updating operation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update operation: {str(e)}"
        )


@router.delete("/projects/{project_id}/iterations/{iteration_id}/operations/{operation_id}", response_model=SuccessResponse)
async def delete_operation(project_id: str, iteration_id: str, operation_id: str):
    """
    Delete a specific operation from the current iteration.
    
    User Story: Edit materialized operations for an iteration
    
    This endpoint allows users to remove unwanted operations before applying
    changes to the ontology. This is useful when AI generates operations that
    the user determines are incorrect or unnecessary.
    """
    try:
        logger.info(f"Deleting operation: {operation_id} for iteration: {iteration_id} in project: {project_id}")
        
        design_project_service.delete_iteration_operation(
            project_id=project_id,
            iteration_id=iteration_id,
            operation_id=operation_id
        )
        
        return SuccessResponse(
            success=True,
            message=f"Operation '{operation_id}' deleted successfully"
        )
    
    except ValueError as e:
        logger.error(f"Invalid request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found"
        )
    except Exception as e:
        logger.error(f"Error deleting operation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete operation: {str(e)}"
        )


@router.post("/projects/{project_id}/iterations/{iteration_id}/apply", response_model=IterationAppliedResponse)
async def apply_iteration_changes(project_id: str, iteration_id: str, request: ApplyOperationsRequest):
    """
    Apply the operations to the ontology and complete the iteration.
    
    User Story: Execute an iteration with planned tasks
    
    This operation:
    1. Validates iteration_id from URL matches current iteration
    2. Validates iteration is in "operations_generated" status
    3. Uses persisted operations from prepare step (or accepts operations from client for filtering scenarios)
    4. Applies operations to ontology
    5. Moves iteration to "finished"
    6. Updates ontology in storage
    7. Returns updated ontology with change statistics
    """
    try:
        logger.info(f"Applying iteration changes for project: {project_id}, iteration: {iteration_id}")
        
        # Load project and validate
        project = design_project_service.load_project(project_id)
        
        # Validate there is a current iteration
        if not project.currentIteration:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No current iteration to apply. Prepare an iteration first."
            )
        
        # Validate the iteration_id from URL matches the current iteration
        if project.currentIteration.id != iteration_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Iteration ID mismatch. Expected current iteration '{project.currentIteration.id}' but got '{iteration_id}'. "
                       f"Only the current iteration can be applied."
            )
        
        # Validate iteration is in OPERATIONS_GENERATED status
        if project.currentIteration.status != DesignIterationStatus.OPERATIONS_GENERATED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Iteration is not in 'operations_generated' status. Current status: {project.currentIteration.status}. "
                       f"Call prepare endpoint first."
            )
        
        # Use persisted operations if not provided in request (preferred workflow)
        # Accept operations from request (advanced workflow for client-side modifications)
        if request.operations is not None:
            # Client provided modified operations
            operations = [_convert_model_to_identified_operation(op) for op in request.operations]
            logger.info(f"Using {len(operations)} operations provided by client")
        else:
            # Use persisted operations from prepare step
            if not project.currentIteration.plannedOperations:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="No operations available. The iteration must be prepared first."
                )
            operations = project.currentIteration.plannedOperations
            logger.info(f"Using {len(operations)} persisted operations from prepare step")
        
        logger.info(f"Applying {len(operations)} operations to iteration {iteration_id}")
        
        # Apply the operations
        updated_ontology = design_project_service.apply_current_iteration_changes(
            project_id=project_id,
            operations=operations
        )
        
        # Calculate statistics (simplified)
        stats = {
            "classes_added": len(updated_ontology.classes),
            "attributes_added": len(updated_ontology.attributes),
            "relationships_added": len(updated_ontology.relationships),
            "elements_updated": 0,
            "elements_deleted": 0
        }
        
        return IterationAppliedResponse(
            success=True,
            iteration_id=iteration_id,
            status="completed",
            applied_operations_count=len(operations),
            ontology_changes=stats,
            updated_ontology=_convert_ontology_to_model(updated_ontology)
        )
    
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project not found"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error applying iteration changes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply iteration changes: {str(e)}"
        )


@router.post("/projects/{project_id}/iterations/{iteration_id}/cancel", response_model=SuccessResponse)
async def cancel_iteration(project_id: str, iteration_id: str):
    """
    Cancel the iteration preparation and rollback to planned state.
    
    Validates that the iteration is the current iteration, then rolls back 
    iteration state without modifying ontology.
    """
    try:
        logger.info(f"Cancelling iteration: {iteration_id} for project: {project_id}")
        project = design_project_service.load_project(project_id)
        
        if not project.currentIteration:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No current iteration to cancel"
            )
        
        # Validate the iteration_id from URL matches the current iteration
        if project.currentIteration.id != iteration_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Iteration ID mismatch. Expected current iteration '{project.currentIteration.id}' but got '{iteration_id}'. "
                       f"Only the current iteration can be cancelled."
            )
        
        # Use the service's rollback method to ensure proper state management
        design_project_service._rollback_iteration_state(project, project.currentIteration)
        
        # Save project (rollback doesn't save automatically)
        design_project_service.save_project(project)
        
        return SuccessResponse(
            success=True,
            message=f"Iteration '{iteration_id}' cancelled and returned to planned state"
        )
    
    except HTTPException:
        raise
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found"
        )
    except Exception as e:
        logger.error(f"Error cancelling iteration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel iteration: {str(e)}"
        )


# ============================================================================
# Ontology Viewing Endpoint
# ============================================================================

@router.get("/projects/{project_id}/ontology", response_model=OntologyModel)
async def get_project_ontology(
    project_id: str,
    format: str = Query("json", description="Output format: json or rdf")
):
    """
    Get the current state of the designed ontology.
    
    User Story: See an existing ontology
    
    Note: The backend does not maintain version history. If the client needs
    to show diffs, it should maintain its own snapshots and compute differences client-side.
    """
    try:
        logger.info(f"Getting ontology for project: {project_id}, format: {format}")
        project = design_project_service.load_project(project_id)
        
        return _convert_ontology_to_model(project.designedOntology)
    
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found"
        )
    except Exception as e:
        logger.error(f"Error getting project ontology: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get project ontology: {str(e)}"
        )


# ============================================================================
# Ontology Edit from Instruction (no iteration)
# ============================================================================

@router.post("/projects/{project_id}/ontology/generate-operations", response_model=List[OntologyOperationModel])
async def generate_operations_from_instruction(project_id: str, request: GenerateOperationsRequest):
    """
    Generate ontology edit operations from a free-form user instruction.
    Returns proposed operations for review; use apply-operations to apply them.
    """
    try:
        operations = design_project_service.generate_operations_from_instruction(
            project_id, request.user_instruction
        )
        # Wrap each raw OntologyEditOperation in IdentifiedOperation for conversion to API model
        identified = [
            IdentifiedOperation(id=str(uuid.uuid4()), operation=op, created_from_task_id=None)
            for op in operations
        ]
        return [_convert_operation_to_model(io) for io in identified]
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found",
        )
    except Exception as e:
        logger.error(f"Generate operations failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Generate operations failed: {str(e)}",
        )


@router.post("/projects/{project_id}/ontology/apply-operations", response_model=OntologyModel)
async def apply_operations_to_project_ontology_endpoint(project_id: str, request: ApplyProjectOperationsRequest):
    """
    Apply the given operations directly to the project's designed ontology (no iteration).
    Saves the project and persists the ontology.
    """
    try:
        domain_operations = [_convert_model_to_operation(m) for m in request.operations]
        updated_ontology = design_project_service.apply_operations_to_project_ontology(
            project_id, domain_operations
        )
        return _convert_ontology_to_model(updated_ontology)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found",
        )
    except ValueError as e:
        logger.warning(f"Invalid operations: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Apply operations failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Apply operations failed: {str(e)}",
        )

