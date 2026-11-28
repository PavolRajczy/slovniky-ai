import { createContext, useContext, useMemo, type ReactNode } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getProject, listProjects } from '@/api/projects'
import type { ProjectModel, ProjectSummary } from '@/api/types'
import { useCurrentProject } from '@/hooks/useCurrentProject'

type CurrentProjectContextValue = {
  projectId: string | undefined
  project: ProjectModel | undefined
  projects: ProjectSummary[] | undefined
  isLoading: boolean
  isError: boolean
  setProjectId: (next: string | undefined) => void
}

const CurrentProjectContext = createContext<CurrentProjectContextValue | undefined>(undefined)

export function CurrentProjectProvider({ children }: { children: ReactNode }) {
  const { projectId, setProjectId } = useCurrentProject()

  const projectsQuery = useQuery({
    queryKey: ['projects'],
    queryFn: ({ signal }) => listProjects(signal),
  })

  const projectQuery = useQuery({
    queryKey: ['project', projectId],
    queryFn: ({ signal }) => getProject(projectId!, signal),
    enabled: Boolean(projectId),
  })

  const value = useMemo<CurrentProjectContextValue>(
    () => ({
      projectId,
      project: projectQuery.data,
      projects: projectsQuery.data,
      isLoading: projectQuery.isLoading || projectsQuery.isLoading,
      isError: projectQuery.isError || projectsQuery.isError,
      setProjectId,
    }),
    [
      projectId,
      projectQuery.data,
      projectQuery.isError,
      projectQuery.isLoading,
      projectsQuery.data,
      projectsQuery.isError,
      projectsQuery.isLoading,
      setProjectId,
    ],
  )

  return <CurrentProjectContext.Provider value={value}>{children}</CurrentProjectContext.Provider>
}

export function useCurrentProjectContext(): CurrentProjectContextValue {
  const ctx = useContext(CurrentProjectContext)
  if (!ctx) {
    throw new Error('useCurrentProjectContext must be used within CurrentProjectProvider')
  }
  return ctx
}
