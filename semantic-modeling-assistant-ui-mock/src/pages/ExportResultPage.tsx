import { Link, getRouteApi } from '@tanstack/react-router'
import { WorkflowStepper, resolveWorkflowContext } from '@/components/workflow'
import { mockExportRecapDefaults, mockTasks, mockWorkflowContext } from '@/data/mockContent'

const exportRouteApi = getRouteApi('/export-result')

export function ExportResultPage() {
  const search = exportRouteApi.useSearch()
  const linkContext = resolveWorkflowContext({
    projectId: search.projectId,
    taskId: search.taskId,
  })

  const recap = {
    approved: search.approved ?? mockExportRecapDefaults.approved,
    pending: search.pending ?? mockExportRecapDefaults.pending,
    rejected: search.rejected ?? mockExportRecapDefaults.rejected,
    regenerated: search.regenerated ?? mockExportRecapDefaults.regenerated,
    guidanceUpdated: search.guidanceUpdated ?? mockExportRecapDefaults.guidanceUpdated,
    taskId: search.taskId ?? mockWorkflowContext.taskId,
  }

  const taskTitle = mockTasks.find((t) => t.id === recap.taskId)?.title ?? recap.taskId

  const exportSearch = {
    projectId: linkContext.projectId,
    approved: recap.approved,
    pending: recap.pending,
    rejected: recap.rejected,
    regenerated: recap.regenerated,
    guidanceUpdated: recap.guidanceUpdated,
    taskId: recap.taskId,
  }

  const operationsSearch = {
    projectId: linkContext.projectId,
    domainId: mockWorkflowContext.domainId,
    iterationId: mockWorkflowContext.iterationId,
    taskId: recap.taskId,
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <WorkflowStepper activeStep="export" exportSearch={exportSearch} linkContext={linkContext} />

      <section className="rounded-2xl border border-emerald-200 bg-emerald-50/70 p-6 shadow-sm">
        <h2 className="text-2xl font-semibold tracking-tight text-emerald-900">Export completed</h2>
        <p className="mt-2 text-sm text-emerald-900/90">
          Approved operations were applied and exported to Dataspecer automatically.
        </p>
        <div className="mt-4 rounded-lg border border-emerald-200 bg-white p-3 text-sm text-slate-700">
          <p>
            <span className="font-semibold text-slate-900">Target:</span>{' '}
            https://dataspecer.com/specifications/demo-zakon-v1
          </p>
          <p className="mt-2">
            <span className="font-semibold text-slate-900">Export time:</span> Today 15:06
          </p>
          <p className="mt-2">
            <span className="font-semibold text-slate-900">Status:</span> OK (mock)
          </p>
        </div>
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Session recap</h3>
        <p className="mt-2 text-sm text-slate-600">
          Snapshot of the review state passed from operations review (URL search params + defaults).
        </p>
        <ul className="mt-4 space-y-2 text-sm text-slate-800">
          <li className="flex justify-between gap-4 border-b border-slate-100 pb-2">
            <span className="text-slate-600">Task</span>
            <span className="max-w-[55%] text-right font-semibold text-slate-900">{taskTitle}</span>
          </li>
          <li className="flex justify-between gap-4 border-b border-slate-100 pb-2">
            <span className="text-slate-600">Operations approved</span>
            <span className="font-semibold tabular-nums">{recap.approved}</span>
          </li>
          <li className="flex justify-between gap-4 border-b border-slate-100 pb-2">
            <span className="text-slate-600">Still pending review</span>
            <span className="font-semibold tabular-nums">{recap.pending}</span>
          </li>
          <li className="flex justify-between gap-4 border-b border-slate-100 pb-2">
            <span className="text-slate-600">Rejected</span>
            <span className="font-semibold tabular-nums">{recap.rejected}</span>
          </li>
          <li className="flex justify-between gap-4 border-b border-slate-100 pb-2">
            <span className="text-slate-600">Regenerations run</span>
            <span className="font-semibold tabular-nums">{recap.regenerated}</span>
          </li>
          <li className="flex justify-between gap-4 pt-1">
            <span className="text-slate-600">Guidance updated this session</span>
            <span className="font-semibold">{recap.guidanceUpdated ? 'Yes' : 'No'}</span>
          </li>
        </ul>
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Next steps</h3>
        <div className="mt-4 flex flex-wrap gap-2">
          <Link
            to="/operations"
            search={operationsSearch}
            className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
          >
            Back to operations review
          </Link>
          <Link
            to="/iterations"
            search={{ projectId: linkContext.projectId, domainId: mockWorkflowContext.domainId }}
            className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Start next iteration
          </Link>
          <Link
            to="/guidance"
            search={{ projectId: linkContext.projectId }}
            className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Open guidance
          </Link>
        </div>
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">If export fails</h3>
        <p className="mt-2 text-sm text-slate-600">
          Retry export or return to operations review and adjust selected changes.
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          <button
            type="button"
            className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
          >
            Retry export
          </button>
          <Link
            to="/operations"
            search={operationsSearch}
            className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Back to operations review
          </Link>
        </div>
      </section>
    </div>
  )
}
