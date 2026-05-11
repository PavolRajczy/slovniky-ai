import { Link } from '@tanstack/react-router'
import { getRouteApi } from '@tanstack/react-router'
import { useMemo } from 'react'
import {
  NextActionBanner,
  WorkflowContextCapsule,
  WorkflowStepper,
  resolveWorkflowContext,
} from '@/components/workflow'
import { mockDomainAreas, mockIterations, mockTasks } from '@/data/mockContent'

const columns = [
  { id: 'todo', label: 'To do' },
  { id: 'in_progress', label: 'In progress' },
  { id: 'done', label: 'Done' },
] as const

const tasksRouteApi = getRouteApi('/tasks')

export function TasksPage() {
  const search = tasksRouteApi.useSearch()
  const linkContext = resolveWorkflowContext(search)

  const defaultTaskForOperations = useMemo(() => {
    const scoped = mockTasks.filter(
      (t) => t.domainId === linkContext.domainId && t.iterationId === linkContext.iterationId,
    )
    const running = scoped.find((t) => t.status === 'in_progress')
    const done = scoped.find((t) => t.status === 'done')
    return running?.id ?? done?.id ?? scoped[0]?.id ?? linkContext.taskId
  }, [linkContext.domainId, linkContext.iterationId, linkContext.taskId])

  const opsSearchBase = {
    domainId: linkContext.domainId,
    iterationId: linkContext.iterationId,
  }

  return (
    <div className="mx-auto max-w-6xl space-y-8">
      <WorkflowStepper activeStep="tasks" linkContext={linkContext} />
      <WorkflowContextCapsule linkContext={linkContext} />
      <NextActionBanner variant="tasks" />

      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-slate-900">Tasks</h2>
          <p className="mt-1 text-sm text-slate-600">
            Each task has its own generated operations — use <span className="font-medium">Review operations</span> on
            a card to open that task&apos;s operation list.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
          >
            Create task
          </button>
          <Link
            to="/iterations"
            search={{ domainId: linkContext.domainId }}
            className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Back to iterations
          </Link>
        </div>
      </div>

      <div className="flex justify-end">
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Run all tasks
          </button>
          <Link
            to="/operations"
            search={{ ...opsSearchBase, taskId: defaultTaskForOperations }}
            className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-emerald-700"
          >
            Continue to operations review
          </Link>
        </div>
      </div>

      <section className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Create custom task</h3>
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          <input
            readOnly
            value="User-defined custom task"
            className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-800"
          />
          <input
            readOnly
            value="In progress"
            className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-800"
          />
          <textarea
            readOnly
            rows={2}
            className="md:col-span-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-800"
            defaultValue="Task detail: what should be modeled, validated, or refined in this iteration."
          />
        </div>
        <div className="mt-3">
          <button
            type="button"
            className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-emerald-700"
          >
            Save custom task
          </button>
        </div>
      </section>

      <div className="grid gap-4 lg:grid-cols-3">
        {columns.map((column) => (
          <section key={column.id} className="rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm">
            <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">{column.label}</h3>
            <div className="mt-4 space-y-3">
              {mockTasks
                .filter((task) => task.status === column.id)
                .map((task) => {
                  const domain = mockDomainAreas.find((item) => item.id === task.domainId)
                  const iteration = mockIterations.find((item) => item.id === task.iterationId)
                  const opsSearch = {
                    domainId: task.domainId ?? linkContext.domainId,
                    iterationId: task.iterationId ?? linkContext.iterationId,
                    taskId: task.id,
                  }
                  return (
                    <article key={task.id} className="rounded-xl border border-slate-200 bg-slate-50/60 p-3">
                      <p className="text-sm font-semibold text-slate-900">{task.title}</p>
                      <p className="mt-1 text-xs text-slate-500">{task.id}</p>
                      <div className="mt-3 space-y-1 text-xs text-slate-600">
                        <p>
                          <span className="font-medium text-slate-700">Domain:</span> {domain?.label ?? 'Unknown'}
                        </p>
                        <p>
                          <span className="font-medium text-slate-700">Iteration:</span>{' '}
                          {iteration?.title ?? 'Not assigned'}
                        </p>
                      </div>
                      <div className="mt-3 flex flex-wrap gap-2">
                        {task.status === 'todo' ? (
                          <>
                            <button
                              type="button"
                              className="rounded-md bg-slate-900 px-2.5 py-1.5 text-xs font-semibold text-white hover:bg-slate-800"
                            >
                              Run
                            </button>
                            <button
                              type="button"
                              className="rounded-md border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
                            >
                              Edit task
                            </button>
                          </>
                        ) : (
                          <Link
                            to="/operations"
                            search={opsSearch}
                            className="rounded-md bg-emerald-600 px-2.5 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-emerald-700"
                          >
                            Review operations
                          </Link>
                        )}
                      </div>
                    </article>
                  )
                })}
            </div>
          </section>
        ))}
      </div>
    </div>
  )
}
