import { Link } from '@tanstack/react-router'
import { getRouteApi } from '@tanstack/react-router'
import {
  NextActionBanner,
  WorkflowContextCapsule,
  WorkflowStepper,
  resolveWorkflowContext,
} from '@/components/workflow'
import {
  mockActivityHistory,
  mockDomainAreas,
  mockIterations,
  mockTasks,
  mockSubareaClassUris,
  mockWorkflowContext,
} from '@/data/mockContent'

const statusStyles = {
  done: 'bg-emerald-50 text-emerald-800',
  prepared: 'bg-amber-50 text-amber-900',
  planned: 'bg-slate-100 text-slate-700',
}

const iterationsRouteApi = getRouteApi('/iterations')

export function IterationsPage() {
  const { projectId, domainId } = iterationsRouteApi.useSearch()
  const linkContext = resolveWorkflowContext({ projectId, domainId })
  const selectedDomain = domainId ? mockDomainAreas.find((area) => area.id === domainId) : undefined
  const filteredIterations = selectedDomain
    ? mockIterations.filter((iteration) => iteration.domainId === selectedDomain.id)
    : mockIterations
  const filteredHistory = selectedDomain
    ? mockActivityHistory.filter((entry) => entry.domainId === selectedDomain.id)
    : mockActivityHistory
  const tasksByIteration = new Map(
    mockIterations.map((iteration) => [
      iteration.id,
      mockTasks.filter((task) => task.iterationId === iteration.id),
    ]),
  )

  return (
    <div className="mx-auto max-w-5xl space-y-8">
      <WorkflowStepper activeStep="iterations" linkContext={linkContext} />
      <WorkflowContextCapsule linkContext={linkContext} />
      <NextActionBanner variant="iterations" />

      <div>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="text-2xl font-semibold tracking-tight text-slate-900">Iterations</h2>
            <p className="mt-1 text-sm text-slate-600">
              Suggest modeling iterations for an area, optionally scoped by subarea and a free-text goal, then prepare:
              the task planner fills the iteration with tasks and keeps the work organized per domain context.
            </p>
          </div>
          <button
            type="button"
            className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
          >
            Create iteration
          </button>
        </div>
      </div>

      <section className="rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Domain summary</h3>
        {selectedDomain ? (
          <div className="mt-2">
            <p className="text-sm font-semibold text-slate-900">{selectedDomain.label}</p>
            <p className="mt-1 text-sm text-slate-600">{selectedDomain.description}</p>
          </div>
        ) : domainId ? (
          <p className="mt-2 text-sm text-amber-700">
            No domain selected for <span className="font-mono">{domainId}</span>. Showing all iterations.
          </p>
        ) : (
          <p className="mt-2 text-sm text-slate-600">No domain selected. Showing all iterations.</p>
        )}
      </section>

      <section className="rounded-2xl border border-slate-200/80 bg-white shadow-sm">
        <details className="group [&_summary::-webkit-details-marker]:hidden">
          <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-5 py-4 text-left sm:px-6">
            <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Assistant scope</h3>
            <span
              className="shrink-0 text-slate-400 transition-transform duration-200 group-open:rotate-180"
              aria-hidden
            >
              ▼
            </span>
          </summary>
          <div className="border-t border-slate-100 px-5 pb-6 pt-2 sm:px-6">
            <div className="grid gap-4 lg:grid-cols-2">
              <div>
                <label className="block text-sm font-medium text-slate-700" htmlFor="goal">
                  Goal (optional)
                </label>
                <textarea
                  id="goal"
                  readOnly
                  rows={3}
                  className="mt-1 w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-800"
                  defaultValue="Add missing attributes for Section 12 classes in the selected subarea."
                />
              </div>
              <div>
                <span className="block text-sm font-medium text-slate-700">Subarea (class URIs)</span>
                <ul className="mt-2 space-y-2 rounded-lg border border-slate-200 bg-slate-50 p-3 font-mono text-xs text-slate-700">
                  {mockSubareaClassUris.map((u) => (
                    <li key={u} className="break-all">
                      {u}
                    </li>
                  ))}
                </ul>
                <button
                  type="button"
                  className="mt-2 text-sm font-medium text-emerald-700 hover:text-emerald-800"
                >
                  Pick from ontology viewer…
                </button>
              </div>
            </div>
            
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <button
                type="button"
                className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
              >
                Generate iteration from scope
              </button>
            </div>
          </div>
        </details>
      </section>

      <section className="rounded-2xl border border-slate-200/80 bg-white shadow-sm">
        <details className="group [&_summary::-webkit-details-marker]:hidden">
          <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-5 py-4 text-left sm:px-6">
            <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Create custom iteration</h3>
            <span
              className="shrink-0 text-slate-400 transition-transform duration-200 group-open:rotate-180"
              aria-hidden
            >
              ▼
            </span>
          </summary>
          <div className="border-t border-slate-100 px-5 pb-6 pt-2 sm:px-6">
            <div className="grid gap-3 md:grid-cols-2">
              <input
                readOnly
                value="User-defined custom iteration"
                className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-800"
              />
              <input
                readOnly
                value={selectedDomain?.label ?? 'General domain context'}
                className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-800"
              />
              <textarea
                readOnly
                rows={2}
                className="md:col-span-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-800"
                defaultValue="Define specific modeling goal, scope limits, and expected ontology outputs."
              />
            </div>
            <div className="mt-3">
              <button
                type="button"
                className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-emerald-700"
              >
                Save custom iteration
              </button>
            </div>
          </div>
        </details>
      </section>

      <div className="grid gap-4 md:grid-cols-3">
        {filteredIterations.map((it) => (
          (() => {
            const tasks = tasksByIteration.get(it.id) ?? []
            const defaultTaskIdForIteration = tasks[0]?.id ?? mockWorkflowContext.taskId
            const totalTasks = tasks.length
            const doneTasks = tasks.filter((task) => task.status === 'done').length
            const startedTasks = tasks.filter((task) => task.status !== 'todo').length
            const completionRatio = totalTasks > 0 ? doneTasks / totalTasks : 0
            const effectiveStatus = totalTasks > 0 && doneTasks === totalTasks ? 'done' : it.status

            return (
              <article
                key={it.id}
                className="flex h-full flex-col rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm"
              >
                <div className="flex items-start justify-between gap-2">
                  <h3 className="font-semibold text-slate-900">{it.title}</h3>
                  <span
                    className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium capitalize ${statusStyles[effectiveStatus]}`}
                  >
                    {effectiveStatus}
                  </span>
                </div>
                <p className="mt-2 text-xs text-slate-500">{it.domainArea}</p>

                <div className="mt-auto pt-4 space-y-3">
                  {totalTasks === 0 ? (
                    <div className="rounded-lg border border-dashed border-amber-300 bg-amber-50/70 px-3 py-2 text-xs text-amber-900">
                      No tasks planned yet
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-xs text-slate-600">
                        <span>Task progress</span>
                        <span className="font-semibold text-slate-800">
                          {doneTasks}/{totalTasks} completed
                        </span>
                      </div>
                      <div className="h-2 rounded-full bg-slate-100">
                        <div
                          className="h-2 rounded-full bg-emerald-600 transition-all"
                          style={{ width: `${Math.round(completionRatio * 100)}%` }}
                        />
                      </div>
                    </div>
                  )}

                  <div className="flex gap-2">
                    <Link
                      to="/tasks"
                      search={{
                        projectId,
                        domainId: it.domainId,
                        iterationId: it.id,
                        taskId: defaultTaskIdForIteration,
                      }}
                      className="rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-800"
                    >
                      Open tasks
                    </Link>
                    {startedTasks === 0 ? (
                      <button
                        type="button"
                        className="rounded-md border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
                      >
                        Edit
                      </button>
                    ) : null}
                  </div>
                </div>
              </article>
            )
          })()
        ))}
      </div>

      <section className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Recent activity (mock)</h3>
        <ul className="mt-3 space-y-2">
          {filteredHistory.map((entry) => (
            <li key={entry.id} className="rounded-lg border border-slate-100 bg-slate-50 px-3 py-2">
              <div className="flex items-center justify-between gap-3">
                <span className="text-sm font-medium text-slate-900">{entry.action}</span>
                <span className="text-xs text-slate-500">{entry.at}</span>
              </div>
              <p className="mt-1 text-sm text-slate-600">{entry.detail}</p>
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}
