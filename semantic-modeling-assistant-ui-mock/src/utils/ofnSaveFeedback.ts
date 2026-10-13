export type OfnSaveFeedback = {
  projectId: string
  path: string
  absolutePath: string
  pojmyCount: number
  overwroteExisting: boolean
  savedAt: string
}

const STORAGE_KEY = 'ofn-save-feedback'

export function saveOfnSaveFeedback(feedback: OfnSaveFeedback): void {
  try {
    window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(feedback))
  } catch {
    // sessionStorage may be unavailable
  }
}

export function readOfnSaveFeedback(projectId?: string): OfnSaveFeedback | null {
  try {
    const raw = window.sessionStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as OfnSaveFeedback
    if (projectId && parsed.projectId !== projectId) return null
    return parsed
  } catch {
    return null
  }
}

export function clearOfnSaveFeedback(): void {
  try {
    window.sessionStorage.removeItem(STORAGE_KEY)
  } catch {
    // ignore
  }
}
