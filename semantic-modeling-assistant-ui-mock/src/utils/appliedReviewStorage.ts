import type { OntologyOperationModel } from '@/api/types'

export type AppliedRejectedOperation = OntologyOperationModel & {
  rejectionReason?: string
}

export type AppliedReviewSummary = {
  taskId: string
  taskName: string
  finalizedAt: string
  kept: OntologyOperationModel[]
  rejected: AppliedRejectedOperation[]
}

const STORAGE_PREFIX = 'sma-applied-review'

function storageKey(projectId: string, iterationId: string, taskId: string): string {
  return `${STORAGE_PREFIX}:${projectId}:${iterationId}:${taskId}`
}

export function saveAppliedReviewSummary(
  projectId: string,
  iterationId: string,
  summary: AppliedReviewSummary,
): void {
  try {
    localStorage.setItem(storageKey(projectId, iterationId, summary.taskId), JSON.stringify(summary))
  } catch {
    // Ignore storage errors.
  }
}

export function loadAppliedReviewSummary(
  projectId: string,
  iterationId: string,
  taskId: string,
): AppliedReviewSummary | null {
  try {
    const raw = localStorage.getItem(storageKey(projectId, iterationId, taskId))
    if (!raw) return null
    return JSON.parse(raw) as AppliedReviewSummary
  } catch {
    return null
  }
}

export function listAppliedReviewSummaries(
  projectId: string,
  iterationId: string,
): AppliedReviewSummary[] {
  const prefix = `${STORAGE_PREFIX}:${projectId}:${iterationId}:`
  const summaries: AppliedReviewSummary[] = []

  try {
    for (let index = 0; index < localStorage.length; index += 1) {
      const key = localStorage.key(index)
      if (!key?.startsWith(prefix)) continue
      const raw = localStorage.getItem(key)
      if (!raw) continue
      summaries.push(JSON.parse(raw) as AppliedReviewSummary)
    }
  } catch {
    return []
  }

  return summaries.sort(
    (left, right) => new Date(right.finalizedAt).getTime() - new Date(left.finalizedAt).getTime(),
  )
}

export type MergedAppliedReview = {
  summaries: AppliedReviewSummary[]
  kept: OntologyOperationModel[]
  rejected: AppliedRejectedOperation[]
}

export function listAppliedReviewSummariesForProject(projectId: string): AppliedReviewSummary[] {
  const prefix = `${STORAGE_PREFIX}:${projectId}:`
  const summaries: AppliedReviewSummary[] = []

  try {
    for (let index = 0; index < localStorage.length; index += 1) {
      const key = localStorage.key(index)
      if (!key?.startsWith(prefix)) continue
      const raw = localStorage.getItem(key)
      if (!raw) continue
      summaries.push(JSON.parse(raw) as AppliedReviewSummary)
    }
  } catch {
    return []
  }

  return summaries.sort(
    (left, right) => new Date(right.finalizedAt).getTime() - new Date(left.finalizedAt).getTime(),
  )
}

export function mergeAppliedReviewSummaries(summaries: AppliedReviewSummary[]): MergedAppliedReview {
  const kept: OntologyOperationModel[] = []
  const rejected: AppliedRejectedOperation[] = []

  for (const summary of summaries) {
    kept.push(...summary.kept)
    rejected.push(...summary.rejected)
  }

  return { summaries, kept, rejected }
}
