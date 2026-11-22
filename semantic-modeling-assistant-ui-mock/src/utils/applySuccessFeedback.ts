export type ApplySuccessFeedback = {
  projectId: string
  appliedCount: number
  rejectedCount: number
  taskName: string | null
  ofnSaved: boolean
  /** Null when the project is not linked to Dataspecer. */
  dataspecerSynced: boolean | null
  dataspecerError: string | null
  at: string
}

const STORAGE_KEY = 'apply-success-feedback'

export function saveApplySuccessFeedback(feedback: ApplySuccessFeedback): void {
  try {
    window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(feedback))
  } catch {
    // sessionStorage may be unavailable
  }
}

export function readApplySuccessFeedback(projectId?: string): ApplySuccessFeedback | null {
  try {
    const raw = window.sessionStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as ApplySuccessFeedback
    if (projectId && parsed.projectId !== projectId) return null
    return parsed
  } catch {
    return null
  }
}

export function clearApplySuccessFeedback(): void {
  try {
    window.sessionStorage.removeItem(STORAGE_KEY)
  } catch {
    // ignore
  }
}
