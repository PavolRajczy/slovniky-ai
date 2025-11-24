import axios from 'axios'

export const http = axios.create({ baseURL: '/api' })

// Types (subset) aligned with backend-openapi.json
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

export type ProjectModel = {
  id: string
  name: string
  ontology_uri: string
  knowledge_domain_name: string
  knowledge_domain_description: string
  key_knowledge_document_id?: string | null
}

export type OntologyMetadata = {
  uri: string
  label: string
  description: string
}

export type OntologyClassModel = {
  uri: string
  label: string
  description?: string | null
  definition?: string | null  // May be provided by backend in future
  parent_classes?: string[]
  definition_references?: string[]
  specification_references?: string[]
  references?: string[]
}

export type OntologyAttributeModel = {
  uri: string
  label: string
  description?: string | null
  definition?: string | null  // May be provided by backend in future
  domain_class: string
  range_type: string
  definition_references?: string[]
  specification_references?: string[]
  references?: string[]
}

export type OntologyRelationshipModel = {
  uri: string
  label: string
  description?: string | null
  definition?: string | null
  domain_class: string
  range_class: string
  definition_references?: string[]
  specification_references?: string[]
  references?: string[]
}

export type OntologyModel = {
  uri: string
  label: string
  description: string
  classes?: OntologyClassModel[]
  attributes?: OntologyAttributeModel[]
  relationships?: OntologyRelationshipModel[]
}

export type KnowledgeDomainAreaModel = {
  id: string
  label: string
  description: string
  parent_id?: string | null
  key_concepts?: string[]
}

export type DesignIterationModel = {
  id: string
  name: string
  specification: string
  focused_area_id: string
  status: 'suggested' | 'planned' | 'prepared' | 'completed'
  total_tasks?: number
  planned_tasks_count?: number
  finished_tasks_count?: number
}

export type DesignTaskModel = {
  id: string
  name: string
  specification: string
  followed_pattern_id: string
  status: 'planned' | 'generating' | 'completed'
}

export type PatternModel = {
  id: string
  name: string
  category: string
  specification?: string | null
  when_applicable?: string | null
}

export type TaskPatternsListResponse = {
  patterns: PatternModel[]
}

export type TasksListResponse = {
  planned_tasks: DesignTaskModel[]
  current_task: DesignTaskModel | null
  finished_tasks: DesignTaskModel[]
}

export type IterationsListResponse = {
  planned_iterations: DesignIterationModel[]
  current_iteration: DesignIterationModel | null
  finished_iterations: DesignIterationModel[]
}

export const api = {
  async health() {
    const { data } = await http.get('/health')
    return data as { ok?: boolean }
  },
  async listProjects() {
    const { data } = await http.get('/projects')
    return data as ProjectSummary[]
  },
  async getProject(projectId: string) {
    const { data } = await http.get(`/projects/${projectId}`)
    return data as ProjectModel
  },
  async createProject(req: {
    name: string
    ontology_uri: string
    knowledge_domain_name?: string | null
    knowledge_domain_description?: string | null
  }) {
    const { data } = await http.post('/projects', req)
    return data as ProjectModel
  },
  async updateProject(projectId: string, req: Partial<{ name: string; knowledge_domain_name: string; knowledge_domain_description: string }>) {
    const { data } = await http.put(`/projects/${projectId}`, req)
    return data as ProjectModel
  },
  async setKeyDocument(projectId: string, document_id: string) {
    const { data } = await http.put(`/projects/${projectId}/key-document`, { document_id })
    return data as { success: boolean; message: string }
  },
  async generateDomainAreas(projectId: string, user_instruction?: string | null) {
    const { data } = await http.post(`/projects/${projectId}/domain-areas/generate`, { user_instruction })
    return data as KnowledgeDomainAreaModel[]
  },
  async listOntologies() {
    const { data } = await http.get('/ontologies')
    return data as OntologyMetadata[]
  },
  async createOntology(req: { ontology_uri: string; ontology_label: string; ontology_description: string }) {
    const { data } = await http.post('/ontologies', req)
    return data as OntologyMetadata
  },
  async updateOntology(uri: string, req: { ontology_label?: string | null; ontology_description?: string | null }) {
    const { data } = await http.put(`/ontologies/${encodeURIComponent(uri)}`, req)
    return data as OntologyMetadata
  },
  async listAreas(projectId: string) {
    const { data } = await http.get(`/projects/${projectId}/domain-areas`)
    return data as KnowledgeDomainAreaModel[]
  },
  async getArea(projectId: string, areaId: string) {
    const { data } = await http.get(`/projects/${projectId}/domain-areas/${areaId}`)
    return data as KnowledgeDomainAreaModel
  },
  async reidentifyAreas(projectId: string, user_instruction: string) {
    const { data } = await http.post(`/projects/${projectId}/domain-areas/reidentify`, { user_instruction })
    return data as KnowledgeDomainAreaModel[]
  },
  async createArea(projectId: string, req: { label: string; description: string; parent_id?: string | null; key_concepts?: string[] }) {
    const { data } = await http.post(`/projects/${projectId}/domain-areas`, req)
    return data as KnowledgeDomainAreaModel
  },
  async updateArea(projectId: string, areaId: string, req: Partial<{ label: string; description: string; parent_id: string | null; key_concepts: string[] }>) {
    const { data } = await http.put(`/projects/${projectId}/domain-areas/${areaId}`, req)
    return data as KnowledgeDomainAreaModel
  },
  async deleteArea(projectId: string, areaId: string) {
    const { data } = await http.delete(`/projects/${projectId}/domain-areas/${areaId}`)
    return data as { success: boolean; message: string }
  },
  async listIterations(projectId: string, areaId?: string, status?: string) {
    const { data } = await http.get(`/projects/${projectId}/iterations`, {
      params: { area_id: areaId, status },
    })
    return data as IterationsListResponse
  },
  async getIteration(projectId: string, iterationId: string) {
    const { data } = await http.get(`/projects/${projectId}/iterations/${iterationId}`)
    return data as DesignIterationModel
  },
  async getProjectOntology(projectId: string, format: 'json' | 'rdf' = 'json') {
    const { data } = await http.get(`/projects/${projectId}/ontology`, { params: { format } })
    // When format is 'rdf', data will be a string; when 'json', it's OntologyModel
    return format === 'json' ? (data as OntologyModel) : (data as string)
  },
  async getProjectKnowledgeBase(projectId: string) {
    const { data } = await http.get(`/projects/${projectId}/knowledge-base`)
    return data as any
  },
  async suggestIterations(projectId: string, req: { focused_area_id: string; count?: number; user_instruction?: string | null }) {
    const { data } = await http.post(`/projects/${projectId}/iterations/suggest`, req)
    return data as DesignIterationModel[]
  },
  async createIteration(projectId: string, req: { name: string; specification: string; focused_area_id: string }) {
    const { data } = await http.post(`/projects/${projectId}/iterations`, req)
    return data as DesignIterationModel
  },
  async updateIteration(projectId: string, iterationId: string, req: Partial<{ name: string; specification: string; focused_area_id: string }>) {
    const { data } = await http.put(`/projects/${projectId}/iterations/${iterationId}`, req)
    return data as DesignIterationModel
  },
  async deleteIteration(projectId: string, iterationId: string) {
    const { data } = await http.delete(`/projects/${projectId}/iterations/${iterationId}`)
    return data as { success: boolean; message: string }
  },
  async prepareIteration(projectId: string, iterationId: string) {
    const { data } = await http.post(`/projects/${projectId}/iterations/${iterationId}/prepare`)
    return data as { iteration_id: string; status: string; operations: OntologyOperationModel[] }
  },
  async getIterationOperations(projectId: string, iterationId: string) {
    const { data } = await http.get(`/projects/${projectId}/iterations/${iterationId}/operations`)
    return data as { operations: OntologyOperationModel[] }
  },
  async updateOperation(projectId: string, iterationId: string, operationId: string, operation: Partial<OntologyOperationModel>) {
    const { data} = await http.put(`/projects/${projectId}/iterations/${iterationId}/operations/${operationId}`, operation)
    return data as OntologyOperationModel
  },
  async deleteOperation(projectId: string, iterationId: string, operationId: string) {
    const { data } = await http.delete(`/projects/${projectId}/iterations/${iterationId}/operations/${operationId}`)
    return data as { success: boolean; message: string }
  },
  async reorderOperations(projectId: string, iterationId: string, operationIds: string[]) {
    const { data } = await http.put(`/projects/${projectId}/iterations/${iterationId}/operations/reorder`, { operation_ids: operationIds })
    return data as { success: boolean; message: string }
  },
  async filterOperations(projectId: string, rejected_operation_indices: number[]) {
    const { data } = await http.post(`/projects/${projectId}/iterations/current/operations/filter`, { rejected_operation_indices })
    return data as { success: boolean; message: string }
  },
  async applyIteration(projectId: string, iterationId: string, operations?: OntologyOperationModel[]) {
    const { data } = await http.post(`/projects/${projectId}/iterations/${iterationId}/apply`, { operations })
    return data as any
  },
  async cancelIteration(projectId: string, iterationId: string) {
    const { data } = await http.post(`/projects/${projectId}/iterations/${iterationId}/cancel`)
    return data as { success: boolean; message: string }
  },
  async listLegalDocuments() {
    const { data } = await http.get('/knowledge-base/legal')
    return data as any[]
  },
  async listExpertDocuments() {
    const { data } = await http.get('/knowledge-base/expert')
    return data as any[]
  },
  async addLegalDocuments(projectId: string, document_ids: string[]) {
    const { data } = await http.post(`/projects/${projectId}/knowledge-base/legal`, { document_ids })
    return data as { success: boolean; message: string }
  },
  async addExpertDocuments(projectId: string, document_ids: string[]) {
    const { data } = await http.post(`/projects/${projectId}/knowledge-base/expert`, { document_ids })
    return data as { success: boolean; message: string }
  },
  async removeLegalDocument(projectId: string, docId: string) {
    const { data } = await http.delete(`/projects/${projectId}/knowledge-base/legal/${docId}`)
    return data as { success: boolean; message: string }
  },
  async removeExpertDocument(projectId: string, docId: string) {
    const { data } = await http.delete(`/projects/${projectId}/knowledge-base/expert/${docId}`)
    return data as { success: boolean; message: string }
  },
  async getProjectDocument(projectId: string, documentId: string) {
    const { data } = await http.get(`/projects/${projectId}/knowledge-base/documents/${documentId}`)
    return data as any
  },
  async getProjectDocumentCoverage(projectId: string, documentId: string) {
    const { data } = await http.get(`/projects/${projectId}/knowledge-base/documents/${documentId}/coverage`)
    return data as any
  },
  async getKnowledgeDocument(documentId: string) {
    const { data } = await http.get(`/knowledge-base/documents/${documentId}`)
    return data as any
  },
  async getKnowledgeDocumentOutline(documentId: string) {
    const { data } = await http.get(`/knowledge-base/documents/${documentId}/outline`)
    return data as any
  },
  async listPatterns(projectId: string) {
    const { data } = await http.get(`/projects/${projectId}/patterns`)
    return data as TaskPatternsListResponse
  },
  async listTasks(projectId: string, iterationId: string) {
    const { data } = await http.get(`/projects/${projectId}/iterations/${iterationId}/tasks`)
    return data as TasksListResponse
  },
  async planTasks(projectId: string, iterationId: string, user_instruction?: string) {
    const { data } = await http.post(`/projects/${projectId}/iterations/${iterationId}/tasks/plan`, { user_instruction })
    return data as any[]
  },
  async createTask(projectId: string, iterationId: string, req: { name: string; specification: string; followed_pattern_id: string }) {
    const { data } = await http.post(`/projects/${projectId}/iterations/${iterationId}/tasks`, req)
    return data as any
  },
  async updateTask(projectId: string, iterationId: string, taskId: string, req: Partial<{ name: string; specification: string; followed_pattern_id: string }>) {
    const { data } = await http.put(`/projects/${projectId}/iterations/${iterationId}/tasks/${taskId}`, req)
    return data as any
  },
  async deleteTask(projectId: string, iterationId: string, taskId: string) {
    const { data } = await http.delete(`/projects/${projectId}/iterations/${iterationId}/tasks/${taskId}`)
    return data as { success: boolean; message: string }
  },
  async reorderTasks(projectId: string, iterationId: string, taskIds: string[]) {
    const { data } = await http.put(`/projects/${projectId}/iterations/${iterationId}/tasks/reorder`, { task_ids: taskIds })
    return data as { success: boolean; message: string }
  },
}

// Additional types used by operations
export type OntologyOperationModel = {
  id?: string  // Added for operation manipulation in UI
  operation_type: 'create' | 'update' | 'delete'
  target_type: 'class' | 'attribute' | 'relationship'
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
