import { apiFetch } from './client'
import type {
  CreateProjectRequest,
  OfnDocument,
  ProjectModel,
  ProjectSummary,
  UpdateProjectRequest,
  SuccessResponse,
} from './types'

export function listProjects(signal?: AbortSignal): Promise<ProjectSummary[]> {
  return apiFetch<ProjectSummary[]>('/projects', { signal })
}

export function getProject(projectId: string, signal?: AbortSignal): Promise<ProjectModel> {
  return apiFetch<ProjectModel>(`/projects/${projectId}`, { signal })
}

export function createProject(body: CreateProjectRequest): Promise<ProjectModel> {
  return apiFetch<ProjectModel>('/projects', { method: 'POST', body })
}

export function getDataspecerExportUrl(projectId: string): Promise<{ put_url: string }> {
  return apiFetch<{ put_url: string }>(`/projects/${projectId}/dataspecer-export-url`)
}

export function openProjectFromDataspecer(packageIri: string): Promise<ProjectModel> {
  return apiFetch<ProjectModel>('/projects/open-from-dataspecer', {
    method: 'POST',
    body: { package_iri: packageIri },
  })
}

export function updateProject(projectId: string, body: UpdateProjectRequest): Promise<ProjectModel> {
  return apiFetch<ProjectModel>(`/projects/${projectId}`, { method: 'PUT', body })
}

export function deleteProject(projectId: string): Promise<SuccessResponse> {
  return apiFetch<SuccessResponse>(`/projects/${projectId}`, { method: 'DELETE' })
}

export type ProjectOfnMeta = {
  project_id?: string
  saved_at?: string
  overwrote_existing?: boolean
}

export type ProjectOfnDocument = OfnDocument & {
  _meta?: ProjectOfnMeta
}

export type RegenerateProjectOfnResponse = {
  success: boolean
  ofn_path: string
  ofn_absolute_path: string
  ofn_turtle_path?: string
  ofn_turtle_absolute_path?: string
  ofn_pojmy_count: number
  ofn_overwrote_existing: boolean
  document: OfnDocument
}

export function getProjectOfn(
  projectId: string,
  signal?: AbortSignal,
): Promise<ProjectOfnDocument> {
  return apiFetch<ProjectOfnDocument>(`/projects/${projectId}/ofn`, { signal })
}

export function getProjectOfnTurtle(
  projectId: string,
  signal?: AbortSignal,
): Promise<string> {
  return apiFetch<string>(`/projects/${projectId}/ofn`, {
    signal,
    query: { format: 'turtle' },
  })
}

export function regenerateProjectOfn(projectId: string): Promise<RegenerateProjectOfnResponse> {
  return apiFetch<RegenerateProjectOfnResponse>(`/projects/${projectId}/ofn/regenerate`, {
    method: 'POST',
  })
}
