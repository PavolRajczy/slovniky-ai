import { apiFetch } from './client'
import type { TaskPatternsListResponse } from './types'

export function listTaskPatterns(
  projectId: string,
  signal?: AbortSignal,
): Promise<TaskPatternsListResponse> {
  return apiFetch<TaskPatternsListResponse>(`/projects/${projectId}/patterns`, { signal })
}
