export type ReviewDraftState = 'pending' | 'approved' | 'rejected'

export type ReviewDraft = {
  reviewById: Record<string, ReviewDraftState>
  rejectionReasonById: Record<string, string>
  savedGuidanceIds: Record<string, string>
}

const STORAGE_PREFIX = 'sma-review-draft'

function storageKey(projectId: string, iterationId: string, taskId: string): string {
  return `${STORAGE_PREFIX}:${projectId}:${iterationId}:${taskId}`
}

function filterByOperationIds<T extends Record<string, unknown>>(
  record: T,
  operationIds: Set<string>,
): T {
  const next = {} as T
  for (const [key, value] of Object.entries(record)) {
    if (operationIds.has(key)) {
      ;(next as Record<string, unknown>)[key] = value
    }
  }
  return next
}

export function loadReviewDraft(
  projectId: string,
  iterationId: string,
  taskId: string,
  operationIds: Set<string>,
): ReviewDraft | null {
  try {
    const raw = localStorage.getItem(storageKey(projectId, iterationId, taskId))
    if (!raw) return null
    const parsed = JSON.parse(raw) as Partial<ReviewDraft>
    return {
      reviewById: filterByOperationIds(parsed.reviewById ?? {}, operationIds),
      rejectionReasonById: filterByOperationIds(parsed.rejectionReasonById ?? {}, operationIds),
      savedGuidanceIds: filterByOperationIds(parsed.savedGuidanceIds ?? {}, operationIds),
    }
  } catch {
    return null
  }
}

export function saveReviewDraft(
  projectId: string,
  iterationId: string,
  taskId: string,
  draft: ReviewDraft,
  operationIds: Set<string>,
): void {
  try {
    const payload: ReviewDraft = {
      reviewById: filterByOperationIds(draft.reviewById, operationIds),
      rejectionReasonById: filterByOperationIds(draft.rejectionReasonById, operationIds),
      savedGuidanceIds: filterByOperationIds(draft.savedGuidanceIds, operationIds),
    }
    localStorage.setItem(storageKey(projectId, iterationId, taskId), JSON.stringify(payload))
  } catch {
    // Ignore quota or private-mode storage errors.
  }
}

export function clearReviewDraft(projectId: string, iterationId: string, taskId: string): void {
  try {
    localStorage.removeItem(storageKey(projectId, iterationId, taskId))
  } catch {
    // Ignore storage errors.
  }
}
