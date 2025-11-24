import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { RouterProvider, createRootRoute, createRoute, createRouter, Outlet, Link } from '@tanstack/react-router'
import './index.css'
import { AppShell } from './shell/AppShell'
import { StoryboardPage } from './pages/StoryboardPage'
import { WorkbenchPage } from './pages/WorkbenchPage'
import { CompareCoverPage } from './pages/CompareCoverPage'
import { OntologyPage } from './pages/OntologyPage'
import { KnowledgeBasePage } from './pages/KnowledgeBasePage'
import { SettingsPage } from './pages/SettingsPage'
import { useNodePositionsStore } from './store/nodePositionsStore'

const queryClient = new QueryClient()

// Prune old pinned positions on app startup (keep positions from last 30 days)
const thirtyDaysMs = 30 * 24 * 60 * 60 * 1000
useNodePositionsStore.getState().pruneOldPositions(thirtyDaysMs)

const rootRoute = createRootRoute({
  component: () => (
    <QueryClientProvider client={queryClient}>
      <AppShell>
        <Outlet />
      </AppShell>
    </QueryClientProvider>
  ),
})

const storyboardRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: StoryboardPage,
})

const workbenchRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/workbench',
  component: WorkbenchPage,
})

const compareRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/compare',
  component: CompareCoverPage,
})

const ontologyRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/ontology',
  component: OntologyPage,
})

const kbRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/kb',
  component: KnowledgeBasePage,
})

const settingsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/settings',
  component: SettingsPage,
})

const routeTree = rootRoute.addChildren([
  storyboardRoute,
  workbenchRoute,
  compareRoute,
  ontologyRoute,
  kbRoute,
  settingsRoute,
])

const router = createRouter({ routeTree })

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>,
)
