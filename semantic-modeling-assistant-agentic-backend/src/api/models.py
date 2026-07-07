"""
Pydantic models for API request/response validation.
"""
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


# ============================================================================
# Ontology Models
# ============================================================================

class OntologyMetadata(BaseModel):
    """Ontology metadata."""
    uri: str
    label: str
    description: str


class OntologyClassModel(BaseModel):
    """Ontology class."""
    uri: str
    label: str
    definition: Optional[str] = None
    description: Optional[str] = None
    parent_classes: List[str] = Field(default_factory=list)
    definition_references: List[str] = Field(default_factory=list)
    specification_references: List[str] = Field(default_factory=list)
    references: List[str] = Field(default_factory=list)


class OntologyAttributeModel(BaseModel):
    """Ontology attribute."""
    uri: str
    label: str
    definition: Optional[str] = None
    description: Optional[str] = None
    domain_class: str
    range_type: str
    definition_references: List[str] = Field(default_factory=list)
    specification_references: List[str] = Field(default_factory=list)
    references: List[str] = Field(default_factory=list)


class OntologyRelationshipModel(BaseModel):
    """Ontology relationship."""
    uri: str
    label: str
    definition: Optional[str] = None
    description: Optional[str] = None
    domain_class: str
    range_class: str
    definition_references: List[str] = Field(default_factory=list)
    specification_references: List[str] = Field(default_factory=list)
    references: List[str] = Field(default_factory=list)


class OntologyModel(BaseModel):
    """Complete ontology model."""
    uri: str
    label: str
    description: str
    classes: List[OntologyClassModel] = Field(default_factory=list)
    attributes: List[OntologyAttributeModel] = Field(default_factory=list)
    relationships: List[OntologyRelationshipModel] = Field(default_factory=list)


class CreateOntologyRequest(BaseModel):
    """Request to create a new ontology."""
    ontology_uri: str
    ontology_label: str
    ontology_description: str


class UpdateOntologyRequest(BaseModel):
    """Request to update ontology metadata."""
    ontology_label: Optional[str] = None
    ontology_description: Optional[str] = None


class ImportOntologyFromUrlRequest(BaseModel):
    """Request to import ontology from OWL/Turtle URL."""
    url: str
    external_vocabulary_urls: Optional[List[str]] = None


class ExportOntologyToDataSpecerRequest(BaseModel):
    """Request to export ontology to DataSpecer (PUT simplified-semantic-model)."""
    ontology_uri: str
    put_url: str


class ImportOntologyFromDataSpecerRequest(BaseModel):
    """Request to import ontology from DataSpecer simplified-semantic-model URL."""
    url: str
    base_uri: str


class GenerateOperationsRequest(BaseModel):
    """Request to generate ontology edit operations from a free-form instruction."""
    user_instruction: str


class ApplyProjectOperationsRequest(BaseModel):
    """Request to apply operations directly to project ontology (no iteration)."""
    operations: List["OntologyOperationModel"]


# ============================================================================
# Knowledge Base Models
# ============================================================================

class KnowledgeDocumentSummary(BaseModel):
    """Knowledge document summary for list views."""
    id: str
    title: str
    element_type: str
    content_summary: str


class OntologyElementReference(BaseModel):
    """Reference to an ontology element."""
    uri: str
    label: str
    element_type: Literal["class", "attribute", "relationship"]


class KnowledgeDocumentElementCoverage(BaseModel):
    """Coverage information for a knowledge document element."""
    defined_ontology_elements: List[OntologyElementReference] = Field(default_factory=list)
    specified_ontology_elements: List[OntologyElementReference] = Field(default_factory=list)
    referenced_ontology_elements: List[OntologyElementReference] = Field(default_factory=list)
    has_coverage: bool


class KnowledgeDocumentElement(BaseModel):
    """Knowledge document element (recursive structure)."""
    id: str
    title: str
    content: str
    content_summary: str
    element_type: str
    child_elements: List['KnowledgeDocumentElement'] = Field(default_factory=list)
    coverage: Optional[KnowledgeDocumentElementCoverage] = None


class KnowledgeDocument(BaseModel):
    """Complete knowledge document with hierarchical structure."""
    id: str
    title: str
    content: str
    content_summary: str
    element_type: str
    child_elements: List[KnowledgeDocumentElement] = Field(default_factory=list)
    coverage: Optional[KnowledgeDocumentElementCoverage] = None


class KnowledgeDocumentOutline(BaseModel):
    """Knowledge document outline."""
    id: str
    title: str
    content_summary: str
    outline: str  # XML format


# ============================================================================
# Design Project Models
# ============================================================================

class CreateProjectRequest(BaseModel):
    """Request to create a new design project."""
    name: str
    ontology_uri: str
    knowledge_domain_name: Optional[str] = None
    knowledge_domain_description: Optional[str] = None


class UpdateProjectRequest(BaseModel):
    """Request to update project metadata."""
    name: Optional[str] = None
    knowledge_domain_name: Optional[str] = None
    knowledge_domain_description: Optional[str] = None


class ProjectSummary(BaseModel):
    """Project summary for list views."""
    id: str
    name: str
    ontology_uri: str
    knowledge_domain_name: str
    created_at: str
    updated_at: str
    domain_areas_count: int
    iterations_count: int


class KnowledgeDomainAreaModel(BaseModel):
    """Knowledge domain area."""
    id: str
    label: str
    description: str
    parent_id: Optional[str] = None
    key_concepts: List[str] = Field(default_factory=list)
    modeling_classes: List[str] = Field(default_factory=list)
    modeling_attributes: List[str] = Field(default_factory=list)
    modeling_relationships: List[str] = Field(default_factory=list)
    explaining_knowledge_resources: List[str] = Field(default_factory=list)


class CreateDomainAreaRequest(BaseModel):
    """Request to create a new domain area."""
    label: str
    description: str
    parent_id: Optional[str] = None
    key_concepts: List[str] = Field(default_factory=list)


class UpdateDomainAreaRequest(BaseModel):
    """Request to update a domain area."""
    label: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[str] = None
    key_concepts: Optional[List[str]] = None


class ReidentifyDomainAreasRequest(BaseModel):
    """Request to re-identify domain areas."""
    user_instruction: str


class SetKeyDocumentRequest(BaseModel):
    """Request to set the key knowledge document."""
    document_id: str


class GenerateDomainAreasRequest(BaseModel):
    """Request to generate domain areas."""
    user_instruction: Optional[str] = None


class DesignIterationModel(BaseModel):
    """Design iteration."""
    id: str
    name: str
    specification: str
    focused_area_id: str
    status: Literal["suggested", "planned", "prepared", "completed"]
    total_tasks: int = 0
    planned_tasks_count: int = 0
    finished_tasks_count: int = 0


class CreateIterationRequest(BaseModel):
    """Request to create a new iteration."""
    name: str
    specification: str
    focused_area_id: str


class UpdateIterationRequest(BaseModel):
    """Request to update an iteration."""
    name: Optional[str] = None
    specification: Optional[str] = None
    focused_area_id: Optional[str] = None


class SuggestIterationsRequest(BaseModel):
    """Request to suggest iterations for a domain area."""
    focused_area_id: str
    count: int = Field(default=5, ge=1, le=20)
    user_instruction: Optional[str] = None


class ReorderIterationsRequest(BaseModel):
    """Request to reorder planned iterations."""
    iteration_ids: List[str]


class DesignTaskPatternModel(BaseModel):
    """Design task pattern."""
    id: str
    name: str
    category: str
    specification: Optional[str] = None
    when_applicable: Optional[str] = None


class DesignTaskModel(BaseModel):
    """Design task."""
    id: str
    name: str
    specification: str
    followed_pattern_id: str
    status: Literal["planned", "generating", "completed"]


class CreateTaskRequest(BaseModel):
    """Request to create a new task."""
    name: str
    specification: str
    followed_pattern_id: str


class UpdateTaskRequest(BaseModel):
    """Request to update a task."""
    name: Optional[str] = None
    specification: Optional[str] = None
    followed_pattern_id: Optional[str] = None


class PlanTasksRequest(BaseModel):
    """Request to plan tasks for an iteration."""
    user_instruction: Optional[str] = None


class ReorderTasksRequest(BaseModel):
    """Request to reorder tasks."""
    task_ids: List[str]


class OntologyOperationModel(BaseModel):
    """
    Ontology edit operation - complete representation with identity.
    
    This model must contain all fields from all OntologyEditOperation subclasses
    to allow full round-trip serialization (backend -> frontend -> backend).
    """
    id: str  # Unique identifier for this operation instance
    operation_type: Literal["create", "update", "delete"]
    target_type: Literal["class", "attribute", "relationship"]
    created_from_task_id: Optional[str] = None
    
    # Required for all operations
    uri: str
    
    # Common fields (optional for delete operations)
    label: Optional[str] = None
    definition: Optional[str] = None
    description: Optional[str] = None
    definition_references: Optional[List[str]] = None
    specification_references: Optional[List[str]] = None
    references: Optional[List[str]] = None
    
    # Class-specific fields
    kind: Optional[str] = None  # "object-type", "event-type", etc.
    generalization_uris: Optional[List[str]] = None
    
    # Attribute-specific fields
    owning_class_uri: Optional[str] = None
    
    # Relationship-specific fields
    source_class_uri: Optional[str] = None
    target_class_uri: Optional[str] = None


class ReorderOperationsRequest(BaseModel):
    """Request to reorder operations within an iteration."""
    operation_ids: List[str]


class UpdateOperationRequest(BaseModel):
    """Request to update an operation."""
    # All fields optional - only provided fields are updated
    operation_type: Optional[Literal["create", "update", "delete"]] = None
    target_type: Optional[Literal["class", "attribute", "relationship"]] = None
    uri: Optional[str] = None
    label: Optional[str] = None
    definition: Optional[str] = None
    description: Optional[str] = None
    definition_references: Optional[List[str]] = None
    specification_references: Optional[List[str]] = None
    references: Optional[List[str]] = None
    
    # Class-specific fields
    kind: Optional[str] = None
    generalization_uris: Optional[List[str]] = None
    
    # Attribute-specific fields
    owning_class_uri: Optional[str] = None
    
    # Relationship-specific fields
    source_class_uri: Optional[str] = None
    target_class_uri: Optional[str] = None


class ApplyOperationsRequest(BaseModel):
    """Request to apply operations to ontology. The iteration_id is provided in the URL path."""
    operations: Optional[List[OntologyOperationModel]] = None  # Optional: uses persisted operations if not provided


class AddKnowledgeDocumentsRequest(BaseModel):
    """Request to add knowledge documents."""
    document_ids: List[str]


class ProjectModel(BaseModel):
    """Complete project model."""
    id: str
    name: str
    ontology_uri: str
    knowledge_domain_name: str
    knowledge_domain_description: str
    key_knowledge_document_id: Optional[str] = None
    legal_knowledge_document_ids: List[str] = Field(default_factory=list)
    expert_knowledge_document_ids: List[str] = Field(default_factory=list)
    domain_areas: List[KnowledgeDomainAreaModel] = Field(default_factory=list)
    planned_iterations: List[DesignIterationModel] = Field(default_factory=list)
    current_iteration: Optional[DesignIterationModel] = None
    finished_iterations: List[DesignIterationModel] = Field(default_factory=list)


# ============================================================================
# Project Guidance (Human-in-the-Loop)
# ============================================================================

class ProjectGuidanceItemModel(BaseModel):
    """Project-scoped guidance item for human-in-the-loop."""
    id: str
    project_id: str
    type: Literal["instruction", "correction", "preference", "constraint"]
    content: str
    created_at: Optional[str] = None
    source: Optional[Literal["manual", "correction", "saved_from_request"]] = None


class CreateProjectGuidanceItemRequest(BaseModel):
    """Request to add a project guidance item."""
    content: str
    type: Literal["instruction", "correction", "preference", "constraint"] = "instruction"


class UpdateProjectGuidanceItemRequest(BaseModel):
    """Request to update a project guidance item."""
    content: Optional[str] = None
    type: Optional[Literal["instruction", "correction", "preference", "constraint"]] = None


class ProjectGuidanceListResponse(BaseModel):
    """Response with list of project guidance items."""
    items: List[ProjectGuidanceItemModel]


# ============================================================================
# Response Models
# ============================================================================

class SuccessResponse(BaseModel):
    """Generic success response."""
    success: bool = True
    message: str


class DeleteResponse(BaseModel):
    """Response for delete operations."""
    success: bool = True
    message: str


class IterationPreparedResponse(BaseModel):
    """Response after preparing an iteration."""
    iteration_id: str
    status: str
    operations: List[OntologyOperationModel]


class IterationAppliedResponse(BaseModel):
    """Response after applying iteration changes."""
    success: bool
    iteration_id: str
    status: str
    applied_operations_count: int
    ontology_changes: Dict[str, int]
    updated_ontology: OntologyModel


class IterationsListResponse(BaseModel):
    """Response with iterations list."""
    planned_iterations: List[DesignIterationModel]
    current_iteration: Optional[DesignIterationModel]
    finished_iterations: List[DesignIterationModel]


class TasksListResponse(BaseModel):
    """Response with tasks list."""
    planned_tasks: List[DesignTaskModel]
    current_task: Optional[DesignTaskModel]
    finished_tasks: List[DesignTaskModel]


class TaskPatternsListResponse(BaseModel):
    """Response with task patterns list."""
    patterns: List[DesignTaskPatternModel]


class KnowledgeBaseResponse(BaseModel):
    """Response with knowledge base documents."""
    legal_documents: List[KnowledgeDocumentSummary]
    expert_documents: List[KnowledgeDocumentSummary]


# Resolve forward reference for ApplyProjectOperationsRequest
ApplyProjectOperationsRequest.model_rebuild()
