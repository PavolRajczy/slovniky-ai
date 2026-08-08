import { Link } from '@tanstack/react-router'
import { mockDomainAreas, mockIterations, mockTasks, mockWorkflowContext } from '@/data/mockContent'
import type { WorkflowLinkContext } from '@/components/workflow/WorkflowSearchContext'

type WorkflowContextCapsuleProps = {
  linkContext: WorkflowLinkContext
  /** Override goal line; defaults to mock workflow goal. */
  goal?: string
}

export function WorkflowContextCapsule({ linkContext, goal = mockWorkflowContext.goal }: WorkflowContextCapsuleProps) {
  const domain = mockDomainAreas.find((d) => d.id === linkContext.domainId)
  const iteration = mockIterations.find((i) => i.id === linkContext.iterationId)
  const task = mockTasks.find((t) => t.id === linkContext.taskId)

  return (
    <section className="sticky top-0 z-10 rounded-xl border border-slate-200/90 bg-linear-to-r from-slate-50 to-white px-4 py-3 shadow-sm backdrop-blur-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0 flex-1 space-y-1">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Current context</p>
          <p className="text-sm font-semibold text-slate-900">{domain?.label ?? 'Unknown domain'}</p>
          <p className="text-xs text-slate-600">
            <span className="font-medium text-slate-700">Iteration:</span> {iteration?.title ?? 'Not set'}
            <span className="mx-2 text-slate-300">·</span>
            <span className="font-mono text-[11px] text-slate-500">{linkContext.iterationId}</span>
          </p>
          <p className="text-xs text-slate-600">
            <span className="font-medium text-slate-700">Work item:</span> {task?.title ?? linkContext.taskId}
            <span className="mx-2 text-slate-300">·</span>
            <span className="font-mono text-[11px] text-slate-500">{linkContext.taskId}</span>
          </p>
          <p className="text-xs leading-snug text-slate-600">
            <span className="font-medium text-slate-700">Goal:</span> {goal}
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <Link
            to="/domain-areas"
            search={{ projectId: linkContext.projectId }}
            className="rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
          >
            Domain map
          </Link>
          <Link
            to="/iterations"
            search={{ projectId: linkContext.projectId, domainId: linkContext.domainId }}
            className="rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
          >
            Iterations
          </Link>
          <Link
            to="/tasks"
            search={{
              projectId: linkContext.projectId,
              domainId: linkContext.domainId,
              iterationId: linkContext.iterationId,
              taskId: linkContext.taskId,
            }}
            className="rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
          >
            Prepare changes
          </Link>
        </div>
      </div>
    </section>
  )
}
