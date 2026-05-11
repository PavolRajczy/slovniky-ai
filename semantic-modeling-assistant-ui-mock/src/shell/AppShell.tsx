import { Link, Outlet, useRouterState } from '@tanstack/react-router'

const navItems = [
  { to: '/project', label: 'Project & KB' },
  { to: '/domain-areas', label: 'Domain areas' },
  { to: '/iterations', label: 'Iterations' },
  { to: '/tasks', label: 'Tasks' },
  { to: '/operations', label: 'Operations review' },
  { to: '/guidance', label: 'Guidance' },
] as const

export function AppShell() {
  const pathname = useRouterState({ select: (s) => s.location.pathname })

  return (
    <div className="flex min-h-screen">
      <aside className="flex w-64 shrink-0 flex-col bg-[var(--color-app-sidebar)] text-slate-100">
        <div className="border-b border-white/10 px-4 py-5">
          <div className="text-xs font-medium uppercase tracking-wider text-emerald-300/90">
            Ontology assistant
          </div>
          <div className="mt-1 text-lg font-semibold leading-tight">Design workspace</div>
          <p className="mt-2 text-xs leading-snug text-slate-400">
            Mock UI for screenshots — no backend.
          </p>
        </div>
        <nav className="flex flex-1 flex-col gap-0.5 overflow-y-auto p-3">
          {navItems.map((item) => {
            const active = pathname === item.to
            return (
              <Link
                key={item.to}
                to={item.to}
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
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between gap-4 border-b border-slate-200/80 bg-[var(--color-app-surface)] px-6 py-3 shadow-sm">
          <div className="min-w-0">
            <h1 className="truncate text-sm font-medium text-slate-500">Current project</h1>
            <div className="flex items-center gap-2">
              <span className="truncate font-semibold text-slate-900">demo-zakon-v1</span>
              <span className="shrink-0 rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-800">
                mock
              </span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <label className="sr-only" htmlFor="project-select">
              Project
            </label>
            <select
              id="project-select"
              className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 shadow-sm"
              defaultValue="demo"
            >
              <option value="demo">demo-zakon-v1</option>
              <option value="other">imported-spec-mini</option>
            </select>
          </div>
        </header>
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
