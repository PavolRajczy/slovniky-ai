import { useCallback, useEffect, useState } from 'react'
import { useNavigate, useRouterState } from '@tanstack/react-router'

const STORAGE_KEY = 'sma.currentProjectId'

function readStored(): string | undefined {
  if (typeof window === 'undefined') {
    return undefined
  }
  const value = window.localStorage.getItem(STORAGE_KEY)
  return value ?? undefined
}

function writeStored(projectId: string | undefined): void {
  if (typeof window === 'undefined') {
    return
  }
  if (projectId === undefined || projectId === '') {
    window.localStorage.removeItem(STORAGE_KEY)
  } else {
    window.localStorage.setItem(STORAGE_KEY, projectId)
  }
}

/**
 * Source of truth for "which project is currently selected".
 *
 * Resolution order:
 *   1. `projectId` URL search param on the current route (if present).
 *   2. localStorage entry written by an earlier session/page.
 *
 * `setProjectId` updates the URL (so deep links keep the selection) and also
 * mirrors to localStorage as a fallback for routes that don't carry the param.
 */
export function useCurrentProject(): {
  projectId: string | undefined
  setProjectId: (next: string | undefined) => void
} {
  const navigate = useNavigate()
  const searchFromUrl = useRouterState({
    select: (state) => {
      const last = state.location.search as Record<string, unknown>
      const value = last?.projectId
      return typeof value === 'string' && value.length > 0 ? value : undefined
    },
  })

  const [stored, setStored] = useState<string | undefined>(() => readStored())

  useEffect(() => {
    if (searchFromUrl && searchFromUrl !== stored) {
      writeStored(searchFromUrl)
      setStored(searchFromUrl)
    }
  }, [searchFromUrl, stored])

  const projectId = searchFromUrl ?? stored

  const setProjectId = useCallback(
    (next: string | undefined) => {
      writeStored(next)
      setStored(next)
      navigate({
        to: '.',
        search: (prev: Record<string, unknown>) => ({ ...prev, projectId: next }),
        replace: true,
      })
    },
    [navigate],
  )

  return { projectId, setProjectId }
}
