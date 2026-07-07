import { Link, getRouteApi, useNavigate } from '@tanstack/react-router'
import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  WorkflowContextCapsule,
  WorkflowStepper,
  resolveWorkflowContext,
} from '@/components/workflow'
import { ApiError } from '@/api/client'
import { getProject } from '@/api/projects'
import {
  applyIteration,
  buildDiffSummary,
  deleteIterationOperation,
  getIterationOperations,
} from '@/api/operations'
import { prepareIteration } from '@/api/tasks'
import { addProjectGuidance } from '@/api/guidance'
import type { OntologyOperationModel } from '@/api/types'

const operationsRouteApi = getRouteApi('/operations')

const targetStyles: Record<OntologyOperationModel['target_type'], string> = {
  class: 'bg-sky-100 text-sky-800',
  attribute: 'bg-violet-100 text-violet-800',
  relationship: 'bg-emerald-100 text-emerald-800',
}

const operationStyles: Record<OntologyOperationModel['operation_type'], string> = {
  create: 'bg-emerald-50 text-emerald-800',
  update: 'bg-amber-50 text-amber-800',
  delete: 'bg-rose-50 text-rose-800',
}

const operationLabels: Record<OntologyOperationModel['operation_type'], string> = {
  create: 'Create',
  update: 'Update',
  delete: 'Delete',
}

const targetLabels: Record<OntologyOperationModel['target_type'], string> = {
  class: 'Class',
  attribute: 'Attribute',
  relationship: 'Relationship',
}

type ReviewState = 'pending' | 'approved' | 'rejected'

export function OperationsReviewPage() {
  const search = operationsRouteApi.useSearch()
  const linkContext = resolveWorkflowContext({
    projectId: search.projectId,
    domainId: search.domainId,
    iterationId: search.iterationId,
    taskId: search.taskId,
  })
  const { projectId, iterationId, domainId, taskId } = search
  const queryClient = useQueryClient()
  const navigate = useNavigate()

  const projectQuery = useQuery({
    queryKey: ['project', projectId],
    queryFn: ({ signal }) => getProject(projectId!, signal),
    enabled: Boolean(projectId),
  })

  const operationsQuery = useQuery({
    queryKey: ['iteration-operations', projectId, iterationId],
    queryFn: ({ signal }) => getIterationOperations(projectId!, iterationId!, signal),
    enabled: Boolean(projectId) && Boolean(iterationId),
    retry: false,
  })

  const allOperations = useMemo(
    () => operationsQuery.data?.operations ?? [],
    [operationsQuery.data],
  )
  const operations = useMemo(() => {
    if (!taskId) {
      return allOperations
    }
    const scoped = allOperations.filter((op) => op.created_from_task_id === taskId)
    return scoped.length > 0 ? scoped : allOperations
  }, [allOperations, taskId])
  const isScopedReview = Boolean(taskId)
  const hasTraceableScope = !taskId || operations.every((op) => op.created_from_task_id === taskId)

  const [reviewById, setReviewById] = useState<Record<string, ReviewState>>({})
  const [rejectionReasonById, setRejectionReasonById] = useState<Record<string, string>>({})
  const [rejectModalOpId, setRejectModalOpId] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const [savedGuidanceIds, setSavedGuidanceIds] = useState<Record<string, string>>({})

  const reviewOf = (id: string): ReviewState => reviewById[id] ?? 'pending'
  const setReview = (id: string, next: ReviewState) =>
    setReviewById((prev) => ({ ...prev, [id]: next }))

  const counts = useMemo(() => {
    let approved = 0
    let pending = 0
    let rejected = 0
    for (const op of operations) {
      const state = reviewOf(op.id)
      if (state === 'approved') approved++
      else if (state === 'rejected') rejected++
      else pending++
    }
    return { approved, pending, rejected, total: operations.length }
  }, [operations, reviewById]) // eslint-disable-line react-hooks/exhaustive-deps

  const approvedOperations = useMemo(
    () => operations.filter((op) => reviewOf(op.id) === 'approved'),
    [operations, reviewById], // eslint-disable-line react-hooks/exhaustive-deps
  )
  const diff = useMemo(() => buildDiffSummary(approvedOperations), [approvedOperations])

  const invalidateAll = async () => {
    if (!projectId) return
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ['iteration-operations', projectId, iterationId] }),
      queryClient.invalidateQueries({ queryKey: ['iteration-tasks', projectId, iterationId] }),
      queryClient.invalidateQueries({ queryKey: ['project-iterations', projectId] }),
      queryClient.invalidateQueries({ queryKey: ['project', projectId] }),
    ])
  }

  const saveGuidanceMutation = useMutation({
    mutationFn: ({ operationId, reason }: { operationId: string; reason: string }) =>
      addProjectGuidance(projectId!, {
        content: reason,
        type: 'correction',
      }).then((item) => ({ operationId, item })),
    onSuccess: ({ operationId, item }) => {
      setSavedGuidanceIds((prev) => ({ ...prev, [operationId]: item.id }))
    },
    onError: (error: unknown) => setActionError(toErrorMessage(error)),
  })

  const regeneratePending = useMutation({
    mutationFn: () => prepareIteration(projectId!, iterationId!),
    onSuccess: invalidateAll,
    onError: (error: unknown) => setActionError(toErrorMessage(error)),
  })

  const applyMutation = useMutation({
    mutationFn: () =>
      applyIteration(projectId!, iterationId!, {
        operations: approvedOperations,
      }),
    onSuccess: async (data) => {
      setActionError(null)
      await invalidateAll()
      if (isScopedReview) {
        await navigate({
          to: '/tasks',
          search: {
            projectId,
            domainId,
            iterationId,
            taskId: undefined,
          },
        })
      } else {
        await navigate({
          to: '/export-result',
          search: {
            projectId,
            domainId,
            iterationId,
            taskId,
            approved: counts.approved,
            pending: counts.pending,
            rejected: counts.rejected,
            regenerated: undefined,
            guidanceUpdated: Object.keys(savedGuidanceIds).length > 0,
          },
        })
      }
      // Touch returned data to satisfy unused-warning lint if any.
      void data.applied_operations_count
    },
    onError: (error: unknown) => setActionError(toErrorMessage(error)),
  })

  if (!projectId || !iterationId) {
    return (
      <div className="mx-auto max-w-3xl space-y-4">
        <WorkflowStepper activeStep="operations" linkContext={linkContext} />
        <div className="rounded-2xl border border-amber-200 bg-amber-50 p-6 text-sm text-amber-900">
          No iteration selected. Prepare an iteration on the{' '}
          <Link to="/tasks" search={{ projectId, domainId, iterationId, taskId }} className="font-medium underline">
            prepare changes page
          </Link>{' '}
          first.
        </div>
      </div>
    )
  }

  const exportSearch = {
    projectId,
    approved: counts.approved,
    pending: counts.pending,
    rejected: counts.rejected,
    regenerated: undefined as number | undefined,
    guidanceUpdated: Object.keys(savedGuidanceIds).length > 0,
    taskId,
  }

  const tasksSearch = {
    projectId,
    domainId,
    iterationId,
    taskId,
  }

  const rejectModalOp = rejectModalOpId
    ? operations.find((op) => op.id === rejectModalOpId) ?? null
    : null

  const anyRejected = counts.rejected > 0
  const hasOperations = operations.length > 0
  const isPrepared = operationsQuery.data?.status === 'prepared'

  const handleRegenerateChange = async (operationId: string) => {
    const ok = window.confirm('Regenerate this rejected change? The assistant will try again using your guidance.')
    if (!ok) return
    setActionError(null)
    try {
      await deleteIterationOperation(projectId, iterationId, operationId)
      setReviewById((prev) => {
        const next = { ...prev }
        delete next[operationId]
        return next
      })
      await regeneratePending.mutateAsync()
    } catch (error) {
      setActionError(toErrorMessage(error))
    }
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <WorkflowStepper activeStep="operations" exportSearch={exportSearch} linkContext={linkContext} />
      <WorkflowContextCapsule linkContext={linkContext} />

      {isScopedReview ? (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50/80 px-4 py-3 text-sm text-emerald-950">
          <p className="font-medium">Reviewing one work item</p>
          <p className="mt-1 text-emerald-900/90">
            This view is scoped to the selected work item so you can approve changes in smaller pieces.
            {!hasTraceableScope
              ? ' Some older operations do not include work item traceability yet, so the full prepared set is shown.'
              : null}
          </p>
          <Link
            to="/operations"
            search={{ projectId, domainId, iterationId, taskId: undefined }}
            className="mt-2 inline-flex text-xs font-semibold text-emerald-800 underline"
          >
            Review all prepared changes
          </Link>
        </div>
      ) : null}

      <div className="flex flex-wrap items-center gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm shadow-sm">
        <span className="font-medium text-slate-700">Summary:</span>
        <span className="rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-900">
          Kept {counts.approved}
        </span>
        <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-slate-700">
          Pending {counts.pending}
        </span>
        <span className="rounded-full bg-rose-50 px-2.5 py-0.5 text-xs font-semibold text-rose-900">
          Rejected {counts.rejected}
        </span>
        <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-slate-700">
          Total {counts.total}
        </span>
        {operationsQuery.isFetching ? <span className="text-xs text-slate-500">refreshing…</span> : null}
      </div>

      {!isScopedReview ? (
        <p className="rounded-lg border border-amber-200 bg-amber-50/80 px-3 py-2 text-xs text-amber-900">
          This is the full prepared set. For less context at once, go back to prepare changes and review one
          work item at a time. Apply sends only kept changes to the backend.
        </p>
      ) : (
        <p className="rounded-lg border border-amber-200 bg-amber-50/80 px-3 py-2 text-xs text-amber-900">
          Decide each change once. Apply sends kept changes to the
          backend; rejected changes stay out of the ontology.
        </p>
      )}

      {actionError ? (
        <p className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-900">
          {actionError}
        </p>
      ) : null}

      <div className="flex flex-col gap-6 lg:flex-row lg:items-start">
        <div className="min-w-0 flex-1 space-y-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Proposed changes
            </p>
            <h2 className="text-2xl font-semibold tracking-tight text-slate-900">
              {isScopedReview ? 'Review this work item' : 'Review changes'}
            </h2>
            <p className="mt-1 text-sm text-slate-600">
              {isScopedReview
                ? 'The AI proposed these ontology changes for the selected work item. Keep what should be applied, or reject anything wrong.'
                : 'The AI proposed these ontology changes for the selected direction. Keep what should be applied, reject anything wrong, then apply the kept set.'}
            </p>
          </div>

          {operationsQuery.isLoading ? (
            <div className="rounded-xl border border-slate-200 bg-white px-4 py-6 text-sm text-slate-600">
              Loading prepared changes…
            </div>
          ) : operationsQuery.isError ? (
            <div className="rounded-xl border border-amber-300 bg-amber-50 px-4 py-6 text-sm text-amber-900">
              <p className="font-medium">{(operationsQuery.error as Error).message}</p>
              <p className="mt-1">
                If the iteration is not ready for review yet, prepare it from{' '}
                <Link to="/tasks" search={tasksSearch} className="font-medium underline">
                  the prepare changes page
                </Link>
                .
              </p>
            </div>
          ) : !hasOperations ? (
            <div className="rounded-xl border border-dashed border-amber-300 bg-amber-50/70 px-4 py-6 text-sm text-amber-950">
              <p className="font-medium">No proposed changes for this iteration.</p>
              <p className="mt-1 text-amber-900/90">
                Prepare or re-prepare the selected direction from the prepare changes page so the assistant can propose
                changes.
              </p>
              <Link
                to="/tasks"
                search={tasksSearch}
                className="mt-3 inline-flex rounded-lg bg-slate-900 px-3 py-2 text-xs font-medium text-white hover:bg-slate-800"
              >
                Back to prepare changes
              </Link>
            </div>
          ) : (
            <ul className="space-y-2">
              {operations.map((op) => {
                const state = reviewOf(op.id)
                const refs = op.specification_references ?? op.references ?? []
                return (
                  <li
                    key={op.id}
                    className={`overflow-hidden rounded-xl border bg-white shadow-sm ${
                      state === 'rejected'
                        ? 'border-rose-300 ring-1 ring-rose-200/80'
                        : state === 'approved'
                        ? 'border-emerald-300 ring-1 ring-emerald-200/80'
                        : 'border-slate-200'
                    }`}
                  >
                    <div className="flex items-start gap-3 p-4">
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <span
                            className={`rounded px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide ${operationStyles[op.operation_type]}`}
                          >
                            {operationLabels[op.operation_type]}
                          </span>
                          <span
                            className={`rounded px-2 py-0.5 text-[11px] font-medium ${targetStyles[op.target_type]}`}
                          >
                            {targetLabels[op.target_type]}
                          </span>
                          {state === 'rejected' && (
                            <span className="rounded bg-rose-100 px-2 py-0.5 text-xs font-medium text-rose-800">
                              Rejected
                            </span>
                          )}
                          {state === 'approved' && (
                            <span className="rounded bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-800">
                              Kept
                            </span>
                          )}
                          {savedGuidanceIds[op.id] ? (
                            <span className="rounded bg-violet-100 px-2 py-0.5 text-[11px] font-medium text-violet-800">
                              Saved to guidance
                            </span>
                          ) : null}
                        </div>
                        <p className="mt-1 text-sm font-semibold text-slate-900">
                          {op.label ?? op.uri}
                        </p>
                        <p className="mt-0.5 break-all font-mono text-[11px] text-slate-500">{op.uri}</p>
                        {op.definition ? (
                          <p className="mt-2 text-xs text-slate-700">{op.definition}</p>
                        ) : op.description ? (
                          <p className="mt-2 text-xs text-slate-700">{op.description}</p>
                        ) : null}
                        {op.target_type === 'attribute' && op.owning_class_uri ? (
                          <p className="mt-2 text-[11px] text-slate-500">
                            Owning class: <span className="font-mono">{op.owning_class_uri}</span>
                          </p>
                        ) : null}
                        {op.target_type === 'relationship' &&
                        op.source_class_uri &&
                        op.target_class_uri ? (
                          <p className="mt-2 text-[11px] text-slate-500">
                            <span className="font-mono">{op.source_class_uri}</span> →{' '}
                            <span className="font-mono">{op.target_class_uri}</span>
                          </p>
                        ) : null}
                        {refs.length > 0 ? (
                          <details className="mt-2 text-[11px] text-slate-600">
                            <summary className="cursor-pointer text-slate-500">
                              {refs.length} reference{refs.length === 1 ? '' : 's'}
                            </summary>
                            <ul className="mt-1 list-disc pl-5">
                              {refs.map((ref, i) => (
                                <li key={`${op.id}-ref-${i}`} className="wrap-break-word">
                                  {ref}
                                </li>
                              ))}
                            </ul>
                          </details>
                        ) : null}
                      </div>
                      <div className="flex shrink-0 flex-col gap-1">
                        <button
                          type="button"
                          className={`rounded border px-2 py-1 text-[11px] font-medium ${
                            state === 'approved'
                              ? 'border-emerald-600 bg-emerald-600 text-white'
                              : 'border-emerald-200 bg-emerald-50 text-emerald-800 hover:bg-emerald-100'
                          }`}
                          onClick={() => setReview(op.id, 'approved')}
                        >
                          Keep this change
                        </button>
                        <button
                          type="button"
                          className={`rounded border px-2 py-1 text-[11px] font-medium ${
                            state === 'rejected'
                              ? 'border-rose-700 bg-rose-700 text-white'
                              : 'border-rose-200 bg-rose-50 text-rose-700 hover:bg-rose-100'
                          }`}
                          onClick={() => setRejectModalOpId(op.id)}
                        >
                          Reject this change
                        </button>
                        {state !== 'pending' ? (
                          <button
                            type="button"
                            className="text-[11px] font-medium text-slate-600 hover:underline"
                            onClick={() => setReview(op.id, 'pending')}
                          >
                            Decide later
                          </button>
                        ) : null}
                        {state === 'rejected' ? (
                          <button
                            type="button"
                            className="rounded border border-violet-200 bg-violet-50 px-2 py-1 text-[11px] font-medium text-violet-800 hover:bg-violet-100 disabled:opacity-60"
                            onClick={() => handleRegenerateChange(op.id)}
                            disabled={regeneratePending.isPending}
                          >
                            {regeneratePending.isPending ? 'Regenerating…' : 'Regenerate'}
                          </button>
                        ) : null}
                      </div>
                    </div>
                  </li>
                )
              })}
            </ul>
          )}

          {anyRejected ? (
            <p className="rounded-lg border border-amber-200 bg-amber-50/80 px-3 py-2 text-xs text-amber-900">
              Rejected changes can be regenerated directly on their cards.
            </p>
          ) : null}
        </div>

        <aside className="w-full shrink-0 space-y-4 lg:w-96">
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <h3 className="text-sm font-semibold text-slate-900">Kept changes preview</h3>
            <p className="mt-1 text-xs text-slate-500">
              Projection of the {approvedOperations.length} kept change
              {approvedOperations.length === 1 ? '' : 's'}.
            </p>
            <DiffBlock title="Classes" added={diff.classesAdded} updated={diff.classesUpdated} deleted={diff.classesDeleted} />
            <DiffBlock
              title="Attributes"
              added={diff.attributesAdded}
              updated={diff.attributesUpdated}
              deleted={diff.attributesDeleted}
            />
            <DiffBlock
              title="Relationships"
              added={diff.relationshipsAdded}
              updated={diff.relationshipsUpdated}
              deleted={diff.relationshipsDeleted}
            />
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-3 text-xs text-slate-700">
            <p className="font-medium text-slate-900">Project context</p>
            <p className="mt-1 truncate" title={projectQuery.data?.name}>
              {projectQuery.data?.name ?? '—'}
            </p>
            <p className="mt-0.5 break-all font-mono text-[10px] text-slate-500">
              {projectQuery.data?.ontology_uri}
            </p>
          </div>

          <div className="flex flex-col gap-2">
            <button
              type="button"
              disabled={
                applyMutation.isPending ||
                !isPrepared ||
                approvedOperations.length === 0
              }
              onClick={() => applyMutation.mutate()}
              className="rounded-lg bg-emerald-600 py-2.5 text-center text-sm font-semibold text-white shadow-sm disabled:opacity-60"
              title={
                !isPrepared
                  ? 'Iteration is not ready for review yet.'
                  : approvedOperations.length === 0
                  ? 'Keep at least one change first.'
                  : 'Apply the kept changes to the ontology.'
              }
            >
              {applyMutation.isPending
                ? 'Applying…'
                : `Apply ${approvedOperations.length} kept change${approvedOperations.length === 1 ? '' : 's'}`}
            </button>
            <Link
              to="/tasks"
              search={tasksSearch}
              className="rounded-lg border border-slate-200 py-2.5 text-center text-sm font-medium"
            >
              Back to prepare changes
            </Link>
          </div>
        </aside>
      </div>

      {rejectModalOp ? (
        <RejectModal
          operation={rejectModalOp}
          rejectionReason={rejectionReasonById[rejectModalOp.id] ?? ''}
          onReasonChange={(value) =>
            setRejectionReasonById((prev) => ({ ...prev, [rejectModalOp.id]: value }))
          }
          alreadySavedGuidance={Boolean(savedGuidanceIds[rejectModalOp.id])}
          isSavingGuidance={
            saveGuidanceMutation.isPending && saveGuidanceMutation.variables?.operationId === rejectModalOp.id
          }
          onConfirmReject={() => {
            setReview(rejectModalOp.id, 'rejected')
            setRejectModalOpId(null)
          }}
          onCancel={() => setRejectModalOpId(null)}
          onSaveGuidance={() => {
            const reason = rejectionReasonById[rejectModalOp.id]?.trim()
            if (!reason) {
              setActionError('Provide a reason before saving guidance.')
              return
            }
            saveGuidanceMutation.mutate({ operationId: rejectModalOp.id, reason })
          }}
        />
      ) : null}
    </div>
  )
}

type DiffBlockProps = {
  title: string
  added: string[]
  updated: string[]
  deleted: string[]
}

function DiffBlock({ title, added, updated, deleted }: DiffBlockProps) {
  const empty = added.length === 0 && updated.length === 0 && deleted.length === 0
  return (
    <div className="mt-3 first-of-type:mt-4">
      <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-600">{title}</h4>
      {empty ? (
        <p className="mt-1 text-xs text-slate-400">—</p>
      ) : (
        <ul className="mt-1 space-y-1 font-mono text-[11px] text-slate-700">
          {added.map((label) => (
            <li key={`+${label}`} className="text-emerald-700">
              + {label}
            </li>
          ))}
          {updated.map((label) => (
            <li key={`~${label}`} className="text-amber-700">
              ~ {label}
            </li>
          ))}
          {deleted.map((label) => (
            <li key={`-${label}`} className="text-rose-700">
              − {label}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

type RejectModalProps = {
  operation: OntologyOperationModel
  rejectionReason: string
  onReasonChange: (value: string) => void
  alreadySavedGuidance: boolean
  isSavingGuidance: boolean
  onConfirmReject: () => void
  onCancel: () => void
  onSaveGuidance: () => void
}

function RejectModal({
  operation,
  rejectionReason,
  onReasonChange,
  alreadySavedGuidance,
  isSavingGuidance,
  onConfirmReject,
  onCancel,
  onSaveGuidance,
}: RejectModalProps) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center sm:items-center"
      role="dialog"
      aria-modal="true"
    >
      <button
        type="button"
        className="absolute inset-0 bg-slate-900/40"
        aria-label="Close rejection dialog"
        onClick={onCancel}
      />
      <div className="relative z-10 m-4 w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-5 shadow-xl">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-rose-700">Reject change</p>
            <p className="mt-2 text-sm font-medium text-slate-900">{operation.label ?? operation.uri}</p>
            <p className="mt-0.5 break-all font-mono text-[11px] text-slate-500">{operation.uri}</p>
          </div>
          <button
            type="button"
            className="rounded-lg px-2 py-1 text-xs font-medium text-slate-500 hover:bg-slate-100"
            onClick={onCancel}
          >
            Close
          </button>
        </div>

        <div className="mt-4 border-t border-rose-200/80 pt-4">
          <label className="block text-[11px] font-medium uppercase tracking-wide text-rose-900/80">
            Rejection reason
          </label>
          <textarea
            value={rejectionReason}
            onChange={(event) => onReasonChange(event.target.value)}
            rows={3}
            placeholder='e.g. "Class name should be singular according to methodology."'
            className="mt-1 w-full rounded-lg border border-rose-200 bg-white px-2 py-1.5 text-xs text-slate-800 placeholder:text-slate-400"
          />
          <div className="mt-3 flex flex-wrap gap-2">
            <button
              type="button"
              onClick={onSaveGuidance}
              disabled={isSavingGuidance || alreadySavedGuidance || rejectionReason.trim().length === 0}
              className="rounded-lg bg-violet-700 px-3 py-1.5 text-xs font-semibold text-white shadow-sm disabled:opacity-60 hover:bg-violet-800"
            >
              {alreadySavedGuidance
                ? 'Saved to guidance'
                : isSavingGuidance
                ? 'Saving…'
                : 'Save reason as guidance'}
            </button>
          </div>
          <p className="mt-2 text-[11px] text-rose-900/80">
            Marking a change rejected leaves it visible but excludes it from the preview and apply. After it
            is rejected, use Regenerate on the card if you want the assistant to try again.
          </p>
        </div>

        <div className="mt-5 flex flex-wrap justify-end gap-2 border-t border-slate-100 pt-4">
          <button
            type="button"
            className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            onClick={onCancel}
          >
            Cancel
          </button>
          <button
            type="button"
            className="rounded-lg bg-rose-700 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-rose-800"
            onClick={onConfirmReject}
          >
            Mark rejected
          </button>
        </div>
      </div>
    </div>
  )
}

function toErrorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message
  if (error instanceof Error) return error.message
  return 'Request failed.'
}
