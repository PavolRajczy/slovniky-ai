/**
 * TypeScript mirrors of the backend Pydantic models from
 * `semantic-modeling-assistant-agentic-backend/src/api/models.py`.
 *
 * Only the fields the UI consumes are listed; the structures match the wire
 * format so they can be cast directly from `response.json()`.
 */

export type ApiErrorBody = {
  error: boolean
  message: string
  status_code: number
  details?: unknown
}

export type HealthResponse = {
  status: string
  version: string
}

export type OntologyMetadata = {
  uri: string
  label: string
  description: string
}

export type OntologyClassModel = {
  uri: string
  label: string
  definition?: string | null
  description?: string | null
  parent_classes: string[]
  definition_references: string[]
  specification_references: string[]
  references: string[]
}

export type OntologyAttributeModel = {
  uri: string
  label: string
  definition?: string | null
  description?: string | null
  domain_class: string
  range_type: string
  definition_references: string[]
  specification_references: string[]
  references: string[]
}

export type OntologyRelationshipModel = {
  uri: string
  label: string
  definition?: string | null
  description?: string | null
  domain_class: string
  range_class: string
  definition_references: string[]
  specification_references: string[]
  references: string[]
}

export type OntologyModel = {
  uri: string
  label: string
  description: string
  classes: OntologyClassModel[]
  attributes: OntologyAttributeModel[]
  relationships: OntologyRelationshipModel[]
}

export type ImportOntologyFromDataSpecerRequest = {
  url: string
  base_uri: string
}

export type ExportOntologyToDataSpecerRequest = {
  ontology_uri: string
  put_url: string
}

export type ExportOntologyToOfnRequest = {
  ontology_uri: string
  vocabulary_iri?: string
}

export type OfnMultilingualText = {
  cs?: string
  en?: string
}

export type OfnPojem = {
  iri: string
  typ: string[]
  název: OfnMultilingualText
  popis?: OfnMultilingualText
  definice?: OfnMultilingualText
  'definiční-obor'?: string
  'obor-hodnot'?: string
  'nadřazená-třída'?: string[]
  'nadřazený-vztah'?: string[]
  'nadřazená-vlastnost'?: string[]
  'definující-ustanovení-právního-předpisu'?: string[]
  'související-ustanovení-právního-předpisu'?: string[]
  [key: string]: unknown
}

export type OfnDocument = {
  '@context': string | string[]
  iri: string
  typ: string[]
  název: OfnMultilingualText
  popis?: OfnMultilingualText
  vytvořeno?: {
    typ: string
    datum?: string
    datum_a_čas?: string
  }
  aktualizováno?: {
    typ: string
    datum?: string
    datum_a_čas?: string
  }
  pojmy?: OfnPojem[]
}

export type ProjectSummary = {
  id: string
  name: string
  ontology_uri: string
  knowledge_domain_name: string
  created_at: string
  updated_at: string
  domain_areas_count: number
  iterations_count: number
}

export type KnowledgeDomainAreaModel = {
  id: string
  label: string
  description: string
  parent_id?: string | null
  key_concepts: string[]
  modeling_classes: string[]
  modeling_attributes: string[]
  modeling_relationships: string[]
  explaining_knowledge_resources: string[]
}

export type DesignIterationStatus = 'suggested' | 'planned' | 'prepared' | 'completed'

export type DesignIterationModel = {
  id: string
  name: string
  specification: string
  focused_area_id: string
  status: DesignIterationStatus
  total_tasks: number
  planned_tasks_count: number
  finished_tasks_count: number
}

export type DesignTaskStatus = 'planned' | 'generating' | 'completed'

export type DesignTaskModel = {
  id: string
  name: string
  specification: string
  followed_pattern_id: string
  status: DesignTaskStatus
}

export type DesignTaskPatternModel = {
  id: string
  name: string
  category: string
  specification?: string | null
  when_applicable?: string | null
}

export type OntologyOperationType = 'create' | 'update' | 'delete'
export type OntologyOperationTarget = 'class' | 'attribute' | 'relationship'

export type OntologyOperationModel = {
  id: string
  operation_type: OntologyOperationType
  target_type: OntologyOperationTarget
  created_from_task_id?: string | null
  uri: string
  label?: string | null
  definition?: string | null
  description?: string | null
  definition_references?: string[] | null
  specification_references?: string[] | null
  references?: string[] | null
  kind?: string | null
  generalization_uris?: string[] | null
  owning_class_uri?: string | null
  source_class_uri?: string | null
  target_class_uri?: string | null
}

export type ProjectModel = {
  id: string
  name: string
  ontology_uri: string
  knowledge_domain_name: string
  knowledge_domain_description: string
  key_knowledge_document_id?: string | null
  legal_knowledge_document_ids: string[]
  expert_knowledge_document_ids: string[]
  domain_areas: KnowledgeDomainAreaModel[]
  planned_iterations: DesignIterationModel[]
  current_iteration?: DesignIterationModel | null
  finished_iterations: DesignIterationModel[]
}

export type GuidanceItemType = 'instruction' | 'correction' | 'preference' | 'constraint'
export type GuidanceItemSource = 'manual' | 'correction' | 'saved_from_request'

export type ProjectGuidanceItemModel = {
  id: string
  project_id: string
  type: GuidanceItemType
  content: string
  created_at?: string | null
  source?: GuidanceItemSource | null
}

export type ProjectGuidanceListResponse = {
  items: ProjectGuidanceItemModel[]
}

export type KnowledgeDocumentSummary = {
  id: string
  title: string
  element_type: string
  content_summary: string
}

export type KnowledgeBaseResponse = {
  legal_documents: KnowledgeDocumentSummary[]
  expert_documents: KnowledgeDocumentSummary[]
}

export type IterationsListResponse = {
  planned_iterations: DesignIterationModel[]
  current_iteration: DesignIterationModel | null
  finished_iterations: DesignIterationModel[]
}

export type TasksListResponse = {
  planned_tasks: DesignTaskModel[]
  current_task: DesignTaskModel | null
  finished_tasks: DesignTaskModel[]
}

export type TaskPatternsListResponse = {
  patterns: DesignTaskPatternModel[]
}

export type IterationPreparedResponse = {
  iteration_id: string
  status: string
  operations: OntologyOperationModel[]
}

export type IterationAppliedResponse = {
  success: boolean
  iteration_id: string
  status: string
  applied_operations_count: number
  ontology_changes: Record<string, number>
  updated_ontology: OntologyModel
  ofn_saved?: boolean
  ofn_path?: string | null
  ofn_absolute_path?: string | null
  ofn_pojmy_count?: number | null
  ofn_overwrote_existing?: boolean | null
}

export type SuccessResponse = {
  success: boolean
  message: string
}

export type DeleteResponse = SuccessResponse

export type CreateProjectRequest = {
  name: string
  ontology_uri: string
  knowledge_domain_name?: string
  knowledge_domain_description?: string
}

export type UpdateProjectRequest = {
  name?: string
  knowledge_domain_name?: string
  knowledge_domain_description?: string
}

export type CreateDomainAreaRequest = {
  label: string
  description: string
  parent_id?: string | null
  key_concepts?: string[]
}

export type UpdateDomainAreaRequest = {
  label?: string
  description?: string
  parent_id?: string | null
  key_concepts?: string[]
}

export type GenerateDomainAreasRequest = {
  user_instruction?: string | null
}

export type ReidentifyDomainAreasRequest = {
  user_instruction: string
}

export type SetKeyDocumentRequest = {
  document_id: string
}

export type SuggestIterationsRequest = {
  focused_area_id: string
  count?: number
  user_instruction?: string | null
}

export type CreateIterationRequest = {
  name: string
  specification: string
  focused_area_id: string
}

export type UpdateIterationRequest = {
  name?: string
  specification?: string
  focused_area_id?: string
}

export type CreateTaskRequest = {
  name: string
  specification: string
  followed_pattern_id: string
}

export type UpdateTaskRequest = {
  name?: string
  specification?: string
  followed_pattern_id?: string
}

export type PlanTasksRequest = {
  user_instruction?: string | null
}

export type ApplyOperationsRequest = {
  operations?: OntologyOperationModel[]
}

export type AddKnowledgeDocumentsRequest = {
  document_ids: string[]
}

export type CreateProjectGuidanceItemRequest = {
  content: string
  type?: GuidanceItemType
}

export type UpdateProjectGuidanceItemRequest = {
  content?: string
  type?: GuidanceItemType
}
