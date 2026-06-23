import { apiFetch } from './client'
import type {
  ApplyOperationsRequest,
  IterationAppliedResponse,
  IterationPreparedResponse,
  OntologyOperationModel,
  SuccessResponse,
} from './types'

export function getIterationOperations(
  projectId: string,
  iterationId: string,
  signal?: AbortSignal,
): Promise<IterationPreparedResponse> {
  return apiFetch<IterationPreparedResponse>(
    `/projects/${projectId}/iterations/${iterationId}/operations`,
    { signal },
  )
}

export function deleteIterationOperation(
  projectId: string,
  iterationId: string,
  operationId: string,
): Promise<SuccessResponse> {
  return apiFetch<SuccessResponse>(
    `/projects/${projectId}/iterations/${iterationId}/operations/${encodeURIComponent(operationId)}`,
    { method: 'DELETE' },
  )
}

export function applyIteration(
  projectId: string,
  iterationId: string,
  body: ApplyOperationsRequest,
): Promise<IterationAppliedResponse> {
  return apiFetch<IterationAppliedResponse>(
    `/projects/${projectId}/iterations/${iterationId}/apply`,
    { method: 'POST', body },
  )
}

export function cancelIteration(
  projectId: string,
  iterationId: string,
): Promise<SuccessResponse> {
  return apiFetch<SuccessResponse>(
    `/projects/${projectId}/iterations/${iterationId}/cancel`,
    { method: 'POST' },
  )
}

export type DiffSummary = {
  classesAdded: string[]
  attributesAdded: string[]
  relationshipsAdded: string[]
  classesUpdated: string[]
  attributesUpdated: string[]
  relationshipsUpdated: string[]
  classesDeleted: string[]
  attributesDeleted: string[]
  relationshipsDeleted: string[]
}

const EMPTY_DIFF: DiffSummary = {
  classesAdded: [],
  attributesAdded: [],
  relationshipsAdded: [],
  classesUpdated: [],
  attributesUpdated: [],
  relationshipsUpdated: [],
  classesDeleted: [],
  attributesDeleted: [],
  relationshipsDeleted: [],
}

/**
 * Build a client-side diff projection over the selected operations,
 * grouped by target type and operation type.
 */
export function buildDiffSummary(operations: OntologyOperationModel[]): DiffSummary {
  const out: DiffSummary = {
    classesAdded: [],
    attributesAdded: [],
    relationshipsAdded: [],
    classesUpdated: [],
    attributesUpdated: [],
    relationshipsUpdated: [],
    classesDeleted: [],
    attributesDeleted: [],
    relationshipsDeleted: [],
  }
  for (const op of operations) {
    const label = op.label?.trim() || op.uri
    if (op.target_type === 'class') {
      if (op.operation_type === 'create') out.classesAdded.push(label)
      else if (op.operation_type === 'update') out.classesUpdated.push(label)
      else if (op.operation_type === 'delete') out.classesDeleted.push(label)
    } else if (op.target_type === 'attribute') {
      const owner = op.owning_class_uri ? ` (on ${shortUri(op.owning_class_uri)})` : ''
      const labelWithOwner = `${label}${owner}`
      if (op.operation_type === 'create') out.attributesAdded.push(labelWithOwner)
      else if (op.operation_type === 'update') out.attributesUpdated.push(labelWithOwner)
      else if (op.operation_type === 'delete') out.attributesDeleted.push(labelWithOwner)
    } else if (op.target_type === 'relationship') {
      const endpoints =
        op.source_class_uri && op.target_class_uri
          ? ` (${shortUri(op.source_class_uri)} → ${shortUri(op.target_class_uri)})`
          : ''
      const labelWithEndpoints = `${label}${endpoints}`
      if (op.operation_type === 'create') out.relationshipsAdded.push(labelWithEndpoints)
      else if (op.operation_type === 'update') out.relationshipsUpdated.push(labelWithEndpoints)
      else if (op.operation_type === 'delete') out.relationshipsDeleted.push(labelWithEndpoints)
    }
  }
  return out
}

export function emptyDiff(): DiffSummary {
  return EMPTY_DIFF
}

function shortUri(uri: string): string {
  const hash = uri.lastIndexOf('#')
  if (hash >= 0) return uri.slice(hash + 1)
  const slash = uri.lastIndexOf('/')
  if (slash >= 0) return uri.slice(slash + 1)
  return uri
}
