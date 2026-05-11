import { Link } from '@tanstack/react-router'
import type { WorkflowStepId } from '@/components/workflow/workflowTypes'
import { getWorkflowStepIndex } from '@/components/workflow/workflowTypes'
import type { WorkflowLinkContext } from '@/components/workflow/WorkflowSearchContext'

const STEP_META: { id: WorkflowStepId; label: string }[] = [
  { id: 'domain-areas', label: 'Domain areas' },
  { id: 'iterations', label: 'Iterations' },
  { id: 'tasks', label: 'Tasks' },
  { id: 'operations', label: 'Operations' },
  { id: 'export', label: 'Export' },
]

type ExportRecapSearch = {
  approved?: number
  pending?: number
  rejected?: number
  regenerated?: number
  guidanceUpdated?: boolean
}

type WorkflowStepperProps = {
  activeStep: WorkflowStepId
  linkContext: WorkflowLinkContext
  exportSearch?: ExportRecapSearch
}

export function WorkflowStepper({ activeStep, linkContext, exportSearch }: WorkflowStepperProps) {
  const activeIndex = getWorkflowStepIndex(activeStep)

  return (
    <nav aria-label="Workflow progress" className="overflow-x-auto rounded-xl border border-slate-200 bg-white px-3 py-3 shadow-sm">
      <ol className="flex min-w-max items-center gap-1 sm:gap-2">
        {STEP_META.map((step, index) => {
          const isCurrent = index === activeIndex
          const isCompleted = index < activeIndex

          const domainSearch = { domainId: linkContext.domainId }
          const tasksOpsSearch = {
            domainId: linkContext.domainId,
            iterationId: linkContext.iterationId,
            taskId: linkContext.taskId,
          }

          let href: string | undefined
          let search: Record<string, unknown> | undefined

          if (isCompleted || isCurrent) {
            switch (step.id) {
              case 'domain-areas':
                href = '/domain-areas'
                break
              case 'iterations':
                href = '/iterations'
                search = domainSearch
                break
              case 'tasks':
                href = '/tasks'
                search = tasksOpsSearch
                break
              case 'operations':
                href = '/operations'
                search = tasksOpsSearch
                break
              case 'export':
                href = '/export-result'
                search = exportSearch !== undefined ? { ...exportSearch } : undefined
                break
              default:
                break
            }
          }

          const content = (
            <span
              className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium sm:text-sm ${
                isCurrent
                  ? 'bg-emerald-600 text-white ring-2 ring-emerald-600/30'
                  : isCompleted
                    ? 'bg-emerald-50 text-emerald-900'
                    : 'bg-slate-100 text-slate-500'
              }`}
            >
              <span className="tabular-nums opacity-80">{index + 1}</span>
              <span className="whitespace-nowrap">{step.label}</span>
            </span>
          )

          return (
            <li key={step.id} className="flex items-center">
              {index > 0 ? (
                <span className="mx-1 text-slate-300 sm:mx-2" aria-hidden>
                  →
                </span>
              ) : null}
              {isCompleted && href ? (
                <Link to={href} search={search as never} className="rounded-full outline-none ring-emerald-600/40 focus-visible:ring-2">
                  {content}
                </Link>
              ) : isCurrent ? (
                <span className="rounded-full">{content}</span>
              ) : (
                <span className="rounded-full opacity-90" aria-current={false}>
                  {content}
                </span>
              )}
            </li>
          )
        })}
      </ol>
    </nav>
  )
}
