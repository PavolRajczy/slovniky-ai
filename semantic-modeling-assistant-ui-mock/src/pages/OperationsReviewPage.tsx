import { Link } from '@tanstack/react-router'
import { getRouteApi } from '@tanstack/react-router'
import { useEffect, useMemo, useState } from 'react'
import {
  NextActionBanner,
  WorkflowContextCapsule,
  WorkflowStepper,
  resolveWorkflowContext,
} from '@/components/workflow'
import {
  getOperationsForTask,
  getPreviewDiffForTask,
  mockOperationProposalSwap,
  mockTasks,
  type MockOperation,
} from '@/data/mockContent'

type ReviewState = 'pending' | 'approved' | 'rejected'

const operationsRouteApi = getRouteApi('/operations')

function buildInitialReview(ops: MockOperation[]): Record<string, ReviewState> {
  const initial: Record<string, ReviewState> = {}
  for (const op of ops) {
    initial[op.id] = op.approved ? 'approved' : 'pending'
  }
  return initial
}

function mockNowStamp(): string {
  const d = new Date()
  return `Today ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')} (mock)`
}

export function OperationsReviewPage() {
  const search = operationsRouteApi.useSearch()
  const linkContext = resolveWorkflowContext(search)
  const taskId = linkContext.taskId

  const operationsForTask = useMemo(() => getOperationsForTask(taskId), [taskId])
  const taskMeta = mockTasks.find((t) => t.id === taskId)
  const previewDiff = useMemo(() => getPreviewDiffForTask(taskId), [taskId])

  const [reviewById, setReviewById] = useState<Record<string, ReviewState>>(() =>
    buildInitialReview(operationsForTask),
  )
  const [regeneratedNoticeId, setRegeneratedNoticeId] = useState<string | null>(null)
  const [rejectionReasonById, setRejectionReasonById] = useState<Record<string, string>>({})
  const [regenCountById, setRegenCountById] = useState<Record<string, number>>({})
  const [lastRegenAtById, setLastRegenAtById] = useState<Record<string, string>>({})
  const [regeneratedProposalById, setRegeneratedProposalById] = useState<Record<string, boolean>>({})
  const [guidanceUpdatedSession, setGuidanceUpdatedSession] = useState(false)
  const [rejectModalOpId, setRejectModalOpId] = useState<string | null>(null)

  useEffect(() => {
    const ops = getOperationsForTask(taskId)
    setReviewById(buildInitialReview(ops))
    setRegeneratedNoticeId(null)
    setRejectionReasonById({})
    setRegenCountById({})
    setLastRegenAtById({})
    setRegeneratedProposalById({})
    setRejectModalOpId(null)
  }, [taskId])

  useEffect(() => {
    if (!rejectModalOpId) {
      return
    }
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setRejectModalOpId(null)
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [rejectModalOpId])

  const setState = (id: string, next: ReviewState) => {
    setReviewById((prev) => ({ ...prev, [id]: next }))
    setRegeneratedNoticeId((cur) => (cur === id ? null : cur))
  }

  const handleRegenerate = (id: string) => {
    setReviewById((prev) => ({ ...prev, [id]: 'pending' }))
    setRegeneratedNoticeId(id)
    setRegenCountById((prev) => ({ ...prev, [id]: (prev[id] ?? 0) + 1 }))
    setLastRegenAtById((prev) => ({ ...prev, [id]: mockNowStamp() }))
    setRegeneratedProposalById((prev) => ({ ...prev, [id]: true }))
  }

  const anyRejected = Object.values(reviewById).some((s) => s === 'rejected')

  const counts = useMemo(() => {
    let approved = 0
    let pending = 0
    let rejected = 0
    for (const op of operationsForTask) {
      const s = reviewById[op.id] ?? 'pending'
      if (s === 'approved') {
        approved++
      } else if (s === 'rejected') {
        rejected++
      } else {
        pending++
      }
    }
    const regenerated = Object.values(regenCountById).reduce((a, b) => a + b, 0)
    return { approved, pending, rejected, regenerated }
  }, [reviewById, regenCountById, operationsForTask])

  const exportSearch = {
    approved: counts.approved,
    pending: counts.pending,
    rejected: counts.rejected,
    regenerated: counts.regenerated,
    guidanceUpdated: guidanceUpdatedSession,
    taskId,
  }

  const displaySummary = (opId: string, fallback: string) => {
    const swap = mockOperationProposalSwap[opId]
    if (swap && regeneratedProposalById[opId]) {
      return swap.nextLabel
    }
    return fallback
  }

  const proposalBadge = (opId: string) => {
    const swap = mockOperationProposalSwap[opId]
    if (!swap || !regeneratedProposalById[opId]) {
      return null
    }
    return (
      <span className="rounded bg-violet-100 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-violet-800">
        New proposal
      </span>
    )
  }

  const tasksSearch = {
    domainId: linkContext.domainId,
    iterationId: linkContext.iterationId,
    taskId: linkContext.taskId,
  }

  const rejectModalOp = rejectModalOpId
    ? operationsForTask.find((o) => o.id === rejectModalOpId)
    : undefined

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <WorkflowStepper activeStep="operations" exportSearch={exportSearch} linkContext={linkContext} />
      <WorkflowContextCapsule linkContext={linkContext} />
      <NextActionBanner variant="operations" operationsHasRejected={anyRejected} />

      <div className="flex flex-wrap gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm shadow-sm">
        <span className="font-medium text-slate-700">Summary (this task):</span>
        <span className="rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-900">
          Approved {counts.approved}
        </span>
        <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-slate-700">
          Pending {counts.pending}
        </span>
        <span className="rounded-full bg-rose-50 px-2.5 py-0.5 text-xs font-semibold text-rose-900">
          Rejected {counts.rejected}
        </span>
        <span className="rounded-full bg-violet-50 px-2.5 py-0.5 text-xs font-semibold text-violet-900">
          Regenerations {counts.regenerated}
        </span>
      </div>

      <div className="flex flex-col gap-6 lg:flex-row lg:items-start">
        <div className="min-w-0 flex-1 space-y-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Scoped to one task</p>
            <h2 className="text-2xl font-semibold tracking-tight text-slate-900">Operations review</h2>
            <p className="mt-1 text-sm text-slate-600">
              Ontology operations proposed for{' '}
              <span className="font-medium text-slate-900">{taskMeta?.title ?? taskId}</span>
              <span className="font-mono text-slate-500"> ({taskId})</span>. Each task has its own operation list and
              review state.
            </p>
            <p className="mt-2 text-sm text-slate-600">
              Review generated ontology operations and approve final changes before export to Dataspecer.
            </p>
          </div>

          {anyRejected && (
            <p className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-600">
              Rejected operations can be regenerated in place. Optionally update{' '}
              <a
                href="/guidance"
                target="_blank"
                rel="noreferrer"
                className="font-medium text-violet-700 underline-offset-2 hover:underline"
              >
                project guidance
              </a>{' '}
              first if the model should follow new rules.
            </p>
          )}

          {operationsForTask.length === 0 ? (
            <div className="rounded-xl border border-dashed border-amber-300 bg-amber-50/70 px-4 py-6 text-sm text-amber-950">
              <p className="font-medium">No operations for this task yet.</p>
              <p className="mt-1 text-amber-900/90">
                Run the task first so the assistant can propose ontology operations (mock empty state).
              </p>
              <Link
                to="/tasks"
                search={tasksSearch}
                className="mt-3 inline-flex rounded-lg bg-slate-900 px-3 py-2 text-xs font-medium text-white hover:bg-slate-800"
              >
                Back to tasks
              </Link>
            </div>
          ) : (
            <ul className="space-y-2">
              {operationsForTask.map((op) => {
                const state = reviewById[op.id] ?? 'pending'
                const swap = mockOperationProposalSwap[op.id]

                return (
                  <li
                    key={op.id}
                    className={`overflow-hidden rounded-xl border bg-white shadow-sm ${
                      state === 'rejected' ? 'border-rose-300 ring-1 ring-rose-200/80' : 'border-slate-200'
                    }`}
                  >
                    <div className="flex items-start gap-3 p-4">
                      <input
                        type="checkbox"
                        className="mt-1 h-4 w-4 rounded border-slate-300"
                        checked={state === 'approved'}
                        readOnly
                        aria-label={`Operation ${op.id} approved`}
                      />
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="font-mono text-xs text-slate-400">{op.id}</span>
                          <span className="rounded bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600">
                            {op.kind}
                          </span>
                          {proposalBadge(op.id)}
                          {state === 'rejected' && (
                            <span className="rounded bg-rose-100 px-2 py-0.5 text-xs font-medium text-rose-800">
                              Rejected
                            </span>
                          )}
                        </div>
                        <p className="mt-1 text-sm font-medium text-slate-900">{displaySummary(op.id, op.summary)}</p>
                        {swap && regeneratedProposalById[op.id] && (
                          <p className="mt-1 text-xs text-slate-500 line-through">{swap.previousLabel}</p>
                        )}
                      </div>
                      <div className="flex shrink-0 flex-col gap-1">
                        <button
                          type="button"
                          className="text-xs font-medium text-emerald-700 hover:underline"
                          onClick={() => setState(op.id, 'approved')}
                        >
                          Approve
                        </button>
                        <button
                          type="button"
                          className="text-xs font-medium text-rose-700 hover:underline"
                          onClick={() => setRejectModalOpId(op.id)}
                        >
                          Reject
                        </button>
                        {state === 'rejected' ? (
                          <button
                            type="button"
                            className="text-xs font-medium text-slate-600 hover:underline"
                            onClick={() => setRejectModalOpId(op.id)}
                          >
                            Rejection details
                          </button>
                        ) : null}
                      </div>
                    </div>

                    {regeneratedNoticeId === op.id && state === 'pending' && (
                      <div className="border-t border-emerald-200/80 bg-emerald-50/80 px-4 py-2 text-xs text-emerald-900">
                        New proposal queued for this operation (mock).
                      </div>
                    )}
                  </li>
                )
              })}
            </ul>
          )}
        </div>

        <aside className="w-full shrink-0 space-y-4 lg:w-96">
          <div className="rounded-xl border border-slate-200 bg-slate-50/80 p-3 text-xs text-slate-700">
            <label className="flex cursor-pointer items-center gap-2">
              <input
                type="checkbox"
                className="rounded border-slate-300"
                checked={guidanceUpdatedSession}
                onChange={(e) => setGuidanceUpdatedSession(e.target.checked)}
              />
              <span>
                Guidance updated this session <span className="text-slate-500">(mock toggle for export recap)</span>
              </span>
            </label>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <h3 className="text-sm font-semibold text-slate-900">Operation preview</h3>
            <p className="mt-1 text-xs text-slate-500">Projection for this task if selected operations are applied.</p>
            <div className="mt-4 space-y-4 text-sm">
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wide text-emerald-700">Classes +</h4>
                <ul className="mt-1 space-y-1 font-mono text-xs text-slate-700">
                  {previewDiff.classesAdded.length === 0 ? (
                    <li className="text-slate-400">—</li>
                  ) : (
                    previewDiff.classesAdded.map((c) => <li key={c}>+ {c}</li>)
                  )}
                </ul>
              </div>
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wide text-emerald-700">Attributes +</h4>
                <ul className="mt-1 space-y-1 font-mono text-xs text-slate-700">
                  {previewDiff.attributesAdded.length === 0 ? (
                    <li className="text-slate-400">—</li>
                  ) : (
                    previewDiff.attributesAdded.map((a) => <li key={a}>+ {a}</li>)
                  )}
                </ul>
              </div>
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wide text-emerald-700">Relationships +</h4>
                <ul className="mt-1 space-y-1 font-mono text-xs text-slate-700">
                  {previewDiff.relationshipsAdded.length === 0 ? (
                    <li className="text-slate-400">—</li>
                  ) : (
                    previewDiff.relationshipsAdded.map((r) => <li key={r}>+ {r}</li>)
                  )}
                </ul>
              </div>
            </div>
          </div>

          <div className="flex flex-col gap-2">
            <Link
              to="/export-result"
              search={exportSearch}
              className="rounded-lg bg-emerald-600 py-2.5 text-center text-sm font-semibold text-white shadow-sm"
            >
              Apply selected and continue
            </Link>
            <Link to="/tasks" search={tasksSearch} className="rounded-lg border border-slate-200 py-2.5 text-center text-sm font-medium">
              Back to tasks
            </Link>
          </div>
        </aside>
      </div>

      {rejectModalOp ? (
        <div className="fixed inset-0 z-50 flex items-end justify-center sm:items-center" role="dialog" aria-modal="true">
          <button
            type="button"
            className="absolute inset-0 bg-slate-900/40"
            aria-label="Close rejection dialog"
            onClick={() => setRejectModalOpId(null)}
          />
          <div className="relative z-10 m-4 w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-5 shadow-xl">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-rose-700">Reject operation</p>
                <p className="mt-1 font-mono text-xs text-slate-400">{rejectModalOp.id}</p>
                <p className="mt-2 text-sm font-medium text-slate-900">
                  {displaySummary(rejectModalOp.id, rejectModalOp.summary)}
                </p>
              </div>
              <button
                type="button"
                className="rounded-lg px-2 py-1 text-xs font-medium text-slate-500 hover:bg-slate-100"
                onClick={() => setRejectModalOpId(null)}
              >
                Close
              </button>
            </div>

            <div className="mt-4 border-t border-rose-200/80 pt-4">
              <p className="text-xs font-medium text-rose-950">Decision log</p>
              <label className="mt-2 block text-[11px] font-medium uppercase tracking-wide text-rose-900/80">
                Rejection reason
              </label>
              <textarea
                value={rejectionReasonById[rejectModalOp.id] ?? ''}
                onChange={(e) =>
                  setRejectionReasonById((prev) => ({ ...prev, [rejectModalOp.id]: e.target.value }))
                }
                rows={3}
                placeholder='e.g. "Class name should be singular according to methodology."'
                className="mt-1 w-full rounded-lg border border-rose-200 bg-white px-2 py-1.5 text-xs text-slate-800 placeholder:text-slate-400"
              />
              <div className="mt-2 flex flex-wrap gap-3 text-[11px] text-rose-900/90">
                <span>
                  <span className="font-semibold">Regenerations:</span> {regenCountById[rejectModalOp.id] ?? 0}
                </span>
                {lastRegenAtById[rejectModalOp.id] ? (
                  <span>
                    <span className="font-semibold">Last regenerated:</span> {lastRegenAtById[rejectModalOp.id]}
                  </span>
                ) : (
                  <span className="text-rose-800/80">Not regenerated yet</span>
                )}
              </div>
              <p className="mt-2 text-xs text-rose-900/85">
                Save persistent corrections via guidance if this should apply beyond this step (opens in a new tab).
              </p>
              <div className="mt-3 flex flex-wrap gap-2">
                <button
                  type="button"
                  className="rounded-lg bg-violet-700 px-3 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-violet-800"
                  onClick={() => {
                    handleRegenerate(rejectModalOp.id)
                    setRejectModalOpId(null)
                  }}
                >
                  Regenerate this operation
                </button>
                <a
                  href="/guidance"
                  target="_blank"
                  rel="noreferrer"
                  className="rounded-lg border border-rose-200 bg-white px-3 py-1.5 text-xs font-medium text-rose-900 hover:bg-rose-50/80"
                >
                  Save as correction guidance
                </a>
              </div>
            </div>

            <div className="mt-5 flex flex-wrap justify-end gap-2 border-t border-slate-100 pt-4">
              <button
                type="button"
                className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
                onClick={() => setRejectModalOpId(null)}
              >
                Cancel
              </button>
              <button
                type="button"
                className="rounded-lg bg-rose-700 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-rose-800"
                onClick={() => {
                  setState(rejectModalOp.id, 'rejected')
                  setRejectModalOpId(null)
                }}
              >
                {(reviewById[rejectModalOp.id] ?? 'pending') === 'rejected' ? 'Save & close' : 'Confirm rejection'}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  )
}
