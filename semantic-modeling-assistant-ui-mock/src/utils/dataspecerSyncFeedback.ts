export type DataspecerSyncFeedback = {
  projectId: string
  synced: boolean
  error: string | null
  at: string
}

const STORAGE_KEY = 'dataspecer-sync-feedback'

export function saveDataspecerSyncFeedback(feedback: DataspecerSyncFeedback): void {
  try {
    window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(feedback))
  } catch {
    // sessionStorage may be unavailable
  }
}

export function readDataspecerSyncFeedback(projectId?: string): DataspecerSyncFeedback | null {
  try {
    const raw = window.sessionStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as DataspecerSyncFeedback
    if (projectId && parsed.projectId !== projectId) return null
    return parsed
  } catch {
    return null
  }
}
