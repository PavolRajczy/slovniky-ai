import {
  createRootRoute,
  createRoute,
  createRouter,
  Navigate,
} from '@tanstack/react-router'
import { AppShell } from '@/shell/AppShell'
import { ProjectSetupPage } from '@/pages/ProjectSetupPage'
import { DomainAreasPage } from '@/pages/DomainAreasPage'
import { IterationsPage } from '@/pages/IterationsPage'
import { TasksPage } from '@/pages/TasksPage'
import { OperationsReviewPage } from '@/pages/OperationsReviewPage'
import { GuidancePage } from '@/pages/GuidancePage'
import { ExportResultPage } from '@/pages/ExportResultPage'

function readString(value: unknown): string | undefined {
  return typeof value === 'string' && value.length > 0 ? value : undefined
}

const rootRoute = createRootRoute({
  component: AppShell,
})

const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: () => <Navigate to="/project" replace search={{ projectId: undefined }} />,
})

const projectRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/project',
  validateSearch: (search: Record<string, unknown>) => ({
    projectId: readString(search.projectId),
  }),
  component: ProjectSetupPage,
})

const domainAreasRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/domain-areas',
  validateSearch: (search: Record<string, unknown>) => ({
    projectId: readString(search.projectId),
  }),
  component: DomainAreasPage,
})

const iterationsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/iterations',
  validateSearch: (search: Record<string, unknown>) => ({
    projectId: readString(search.projectId),
    domainId: readString(search.domainId),
  }),
  component: IterationsPage,
})

const tasksRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/tasks',
  validateSearch: (search: Record<string, unknown>) => ({
    projectId: readString(search.projectId),
    domainId: readString(search.domainId),
    iterationId: readString(search.iterationId),
    taskId: readString(search.taskId),
  }),
  component: TasksPage,
})

const operationsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/operations',
  validateSearch: (search: Record<string, unknown>) => ({
    projectId: readString(search.projectId),
    domainId: readString(search.domainId),
    iterationId: readString(search.iterationId),
    taskId: readString(search.taskId),
  }),
  component: OperationsReviewPage,
})

const guidanceRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/guidance',
  validateSearch: (search: Record<string, unknown>) => ({
    projectId: readString(search.projectId),
  }),
  component: GuidancePage,
})

function parseOptionalNumber(value: unknown): number | undefined {
  if (value === undefined || value === null || value === '') {
    return undefined
  }
  const n = Number(value)
  return Number.isFinite(n) ? n : undefined
}

function parseOptionalBool(value: unknown): boolean | undefined {
  if (value === true || value === 'true') {
    return true
  }
  if (value === false || value === 'false') {
    return false
  }
  return undefined
}

const exportResultRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/export-result',
  validateSearch: (search: Record<string, unknown>) => ({
    projectId: readString(search.projectId),
    domainId: readString(search.domainId),
    iterationId: readString(search.iterationId),
    taskId: readString(search.taskId),
    approved: parseOptionalNumber(search.approved),
    pending: parseOptionalNumber(search.pending),
    rejected: parseOptionalNumber(search.rejected),
    regenerated: parseOptionalNumber(search.regenerated),
    guidanceUpdated: parseOptionalBool(search.guidanceUpdated),
  }),
  component: ExportResultPage,
})

const routeTree = rootRoute.addChildren([
  indexRoute,
  projectRoute,
  domainAreasRoute,
  iterationsRoute,
  tasksRoute,
  operationsRoute,
  guidanceRoute,
  exportResultRoute,
])

export const router = createRouter({ routeTree })

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}
