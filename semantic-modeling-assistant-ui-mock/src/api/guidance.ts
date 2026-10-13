import { apiFetch } from './client'
import type {
  CreateProjectGuidanceItemRequest,
  ProjectGuidanceItemModel,
  ProjectGuidanceListResponse,
  SuccessResponse,
  UpdateProjectGuidanceItemRequest,
} from './types'

export function listProjectGuidance(
  projectId: string,
  signal?: AbortSignal,
): Promise<ProjectGuidanceListResponse> {
  return apiFetch<ProjectGuidanceListResponse>(`/projects/${projectId}/guidance`, { signal })
}

export function addProjectGuidance(
  projectId: string,
  body: CreateProjectGuidanceItemRequest,
): Promise<ProjectGuidanceItemModel> {
  return apiFetch<ProjectGuidanceItemModel>(`/projects/${projectId}/guidance`, {
    method: 'POST',
    body,
  })
}

export function updateProjectGuidance(
  projectId: string,
  itemId: string,
  body: UpdateProjectGuidanceItemRequest,
): Promise<ProjectGuidanceItemModel> {
  return apiFetch<ProjectGuidanceItemModel>(`/projects/${projectId}/guidance/${itemId}`, {
    method: 'PATCH',
    body,
  })
}

export function deleteProjectGuidance(
  projectId: string,
  itemId: string,
): Promise<SuccessResponse> {
  return apiFetch<SuccessResponse>(`/projects/${projectId}/guidance/${itemId}`, {
    method: 'DELETE',
  })
}
