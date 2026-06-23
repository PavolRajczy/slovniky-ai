import { apiFetch } from './client'
import type {
  CreateTaskRequest,
  DesignTaskModel,
  IterationPreparedResponse,
  PlanTasksRequest,
  SuccessResponse,
  TasksListResponse,
  UpdateTaskRequest,
} from './types'

export function listTasks(
  projectId: string,
  iterationId: string,
  signal?: AbortSignal,
): Promise<TasksListResponse> {
  return apiFetch<TasksListResponse>(
    `/projects/${projectId}/iterations/${iterationId}/tasks`,
    { signal },
  )
}

export function planTasks(
  projectId: string,
  iterationId: string,
  body: PlanTasksRequest,
): Promise<DesignTaskModel[]> {
  return apiFetch<DesignTaskModel[]>(
    `/projects/${projectId}/iterations/${iterationId}/tasks/plan`,
    { method: 'POST', body },
  )
}

export function createTask(
  projectId: string,
  iterationId: string,
  body: CreateTaskRequest,
): Promise<DesignTaskModel> {
  return apiFetch<DesignTaskModel>(
    `/projects/${projectId}/iterations/${iterationId}/tasks`,
    { method: 'POST', body },
  )
}

export function updateTask(
  projectId: string,
  iterationId: string,
  taskId: string,
  body: UpdateTaskRequest,
): Promise<DesignTaskModel> {
  return apiFetch<DesignTaskModel>(
    `/projects/${projectId}/iterations/${iterationId}/tasks/${taskId}`,
    { method: 'PUT', body },
  )
}

export function deleteTask(
  projectId: string,
  iterationId: string,
  taskId: string,
): Promise<SuccessResponse> {
  return apiFetch<SuccessResponse>(
    `/projects/${projectId}/iterations/${iterationId}/tasks/${taskId}`,
    { method: 'DELETE' },
  )
}

export function prepareIteration(
  projectId: string,
  iterationId: string,
): Promise<IterationPreparedResponse> {
  return apiFetch<IterationPreparedResponse>(
    `/projects/${projectId}/iterations/${iterationId}/prepare`,
    { method: 'POST' },
  )
}
