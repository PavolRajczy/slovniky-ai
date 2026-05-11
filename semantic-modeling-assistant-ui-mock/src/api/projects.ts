import { apiFetch } from './client'
import type {
  CreateProjectRequest,
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

export function updateProject(projectId: string, body: UpdateProjectRequest): Promise<ProjectModel> {
  return apiFetch<ProjectModel>(`/projects/${projectId}`, { method: 'PUT', body })
}

export function deleteProject(projectId: string): Promise<SuccessResponse> {
  return apiFetch<SuccessResponse>(`/projects/${projectId}`, { method: 'DELETE' })
}
