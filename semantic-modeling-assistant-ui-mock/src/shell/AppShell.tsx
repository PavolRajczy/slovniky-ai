import { Link, Outlet, useRouterState } from '@tanstack/react-router'
import { useMemo } from 'react'
import { BackendStatusPill } from '@/components/BackendStatusPill'
import { CurrentProjectProvider, useCurrentProjectContext } from '@/shell/CurrentProjectProvider'

const navItems = [
  { to: '/project', label: 'Project & KB' },
  { to: '/domain-areas', label: 'Domain areas' },
  { to: '/iterations', label: 'Iterations' },
  { to: '/tasks', label: 'Tasks' },
  { to: '/operations', label: 'Operations review' },
  { to: '/guidance', label: 'Guidance' },
] as const

function ProjectSwitcher() {
  const { projectId, projects, setProjectId, isLoading } = useCurrentProjectContext()

  const projectsSorted = useMemo(() => {
    if (!projects) {
      return []
    }
    return [...projects].sort((a, b) => a.name.localeCompare(b.name))
  }, [projects])

  if (isLoading && !projects) {
    return (
      <span className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-500 shadow-sm">
        Loading projects…
      </span>
    )
  }

  if (!projects || projects.length === 0) {
    return (
      <Link
        to="/project"
        search={{ projectId: undefined }}
        className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 shadow-sm hover:bg-slate-50"
      >
        Import a vocabulary…
      </Link>
    )
  }

  return (
    <select
      id="project-select"
      className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 shadow-sm"
      value={projectId ?? ''}
      onChange={(event) => {
        const next = event.target.value
        setProjectId(next === '' ? undefined : next)
      }}
    >
      <option value="">— pick a project —</option>
      {projectsSorted.map((entry) => (
        <option key={entry.id} value={entry.id}>
          {entry.name}
        </option>
      ))}
    </select>
  )
}

function HeaderProjectSummary() {
  const { project, projectId, isLoading } = useCurrentProjectContext()

  if (!projectId) {
    return (
      <>
        <h1 className="truncate text-sm font-medium text-slate-500">Current project</h1>
        <div className="flex items-center gap-2">
          <span className="truncate font-semibold text-slate-900">No project selected</span>
          <span className="shrink-0 rounded-full bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-900">
            pick or import
          </span>
        </div>
      </>
    )
  }

  if (isLoading || !project) {
    return (
      <>
        <h1 className="truncate text-sm font-medium text-slate-500">Current project</h1>
        <span className="truncate font-semibold text-slate-900">Loading…</span>
      </>
    )
  }

  return (
    <>
      <h1 className="truncate text-sm font-medium text-slate-500">Current project</h1>
      <div className="flex items-center gap-2">
        <span className="truncate font-semibold text-slate-900">{project.name}</span>
        <span
          className="shrink-0 truncate rounded-full bg-slate-100 px-2 py-0.5 font-mono text-[11px] text-slate-600"
          title={project.ontology_uri}
        >
          {project.ontology_uri}
        </span>
      </div>
    </>
  )
}

function Sidebar() {
  const pathname = useRouterState({ select: (s) => s.location.pathname })
  const { projectId } = useCurrentProjectContext()
  const search = { projectId }

  return (
    <aside className="flex w-64 shrink-0 flex-col bg-[var(--color-app-sidebar)] text-slate-100">
      <div className="border-b border-white/10 px-4 py-5">
        <div className="text-xs font-medium uppercase tracking-wider text-emerald-300/90">
          Ontology assistant
        </div>
        <div className="mt-1 text-lg font-semibold leading-tight">Design workspace</div>
        <p className="mt-2 text-xs leading-snug text-slate-400">
          React + FastAPI workflow for the Dataspecer-bound vocabulary assistant.
        </p>
      </div>
      <nav className="flex flex-1 flex-col gap-0.5 overflow-y-auto p-3">
        {navItems.map((item) => {
          const active = pathname === item.to
          return (
            <Link
              key={item.to}
              to={item.to}
              search={search}
              className={
                active
                  ? 'rounded-lg bg-white/10 px-3 py-2 text-sm font-medium text-white'
                  : 'rounded-lg px-3 py-2 text-sm text-slate-300 transition hover:bg-white/5 hover:text-white'
              }
            >
              {item.label}
            </Link>
          )
        })}
      </nav>
      <div className="border-t border-white/10 p-3 text-[11px] text-slate-500">
        React · Vite · TanStack Router · Tailwind
      </div>
    </aside>
  )
}

function ShellChrome() {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between gap-4 border-b border-slate-200/80 bg-[var(--color-app-surface)] px-6 py-3 shadow-sm">
          <div className="min-w-0">
            <HeaderProjectSummary />
          </div>
          <div className="flex items-center gap-3">
            <BackendStatusPill />
            <label className="sr-only" htmlFor="project-select">
              Project
            </label>
            <ProjectSwitcher />
            <Link
              to="/project"
              search={{ projectId: undefined }}
              className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 shadow-sm hover:bg-slate-50"
            >
              Import another…
            </Link>
          </div>
        </header>
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export function AppShell() {
  return (
    <CurrentProjectProvider>
      <ShellChrome />
    </CurrentProjectProvider>
  )
}
