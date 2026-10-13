import { apiFetch } from './client'
import type {
  CreateIterationRequest,
  DesignIterationModel,
  IterationsListResponse,
  SuccessResponse,
  SuggestIterationsRequest,
  UpdateIterationRequest,
} from './types'

export function listIterations(
  projectId: string,
  options: { areaId?: string; status?: string } = {},
  signal?: AbortSignal,
): Promise<IterationsListResponse> {
  return apiFetch<IterationsListResponse>(`/projects/${projectId}/iterations`, {
    signal,
    query: {
      area_id: options.areaId,
      status: options.status,
    },
  })
}

export function suggestIterations(
  projectId: string,
  body: SuggestIterationsRequest,
): Promise<DesignIterationModel[]> {
  return apiFetch<DesignIterationModel[]>(`/projects/${projectId}/iterations/suggest`, {
    method: 'POST',
    body,
  })
}

export function createIteration(
  projectId: string,
  body: CreateIterationRequest,
): Promise<DesignIterationModel> {
  return apiFetch<DesignIterationModel>(`/projects/${projectId}/iterations`, {
    method: 'POST',
    body,
  })
}

export function updateIteration(
  projectId: string,
  iterationId: string,
  body: UpdateIterationRequest,
): Promise<DesignIterationModel> {
  return apiFetch<DesignIterationModel>(`/projects/${projectId}/iterations/${iterationId}`, {
    method: 'PUT',
    body,
  })
}

export function deleteIteration(
  projectId: string,
  iterationId: string,
): Promise<SuccessResponse> {
  return apiFetch<SuccessResponse>(`/projects/${projectId}/iterations/${iterationId}`, {
    method: 'DELETE',
  })
}
