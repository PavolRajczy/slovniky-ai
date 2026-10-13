import { apiFetch } from './client'
import type {
  ProjectActivityEventType,
  ProjectActivityListResponse,
  RecordOperationDecisionsRequest,
} from './types'

export type ListProjectActivityOptions = {
  types?: ProjectActivityEventType[]
  iterationId?: string
  taskId?: string
  limit?: number
}

export function listProjectActivity(
  projectId: string,
  options: ListProjectActivityOptions = {},
  signal?: AbortSignal,
): Promise<ProjectActivityListResponse> {
  const params = new URLSearchParams()
  for (const type of options.types ?? []) {
    params.append('type', type)
  }
  if (options.iterationId) {
    params.set('iteration_id', options.iterationId)
  }
  if (options.taskId) {
    params.set('task_id', options.taskId)
  }
  if (options.limit !== undefined) {
    params.set('limit', String(options.limit))
  }

  const query = params.toString()
  return apiFetch<ProjectActivityListResponse>(
    `/projects/${projectId}/activity${query ? `?${query}` : ''}`,
    { signal },
  )
}

export function recordOperationDecisions(
  projectId: string,
  body: RecordOperationDecisionsRequest,
): Promise<ProjectActivityListResponse> {
  return apiFetch<ProjectActivityListResponse>(`/projects/${projectId}/activity/decisions`, {
    method: 'POST',
    body,
  })
}
