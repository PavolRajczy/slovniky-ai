import { Link, getRouteApi, useNavigate } from '@tanstack/react-router'
import { useEffect, useMemo, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  WorkflowContextCapsule,
  resolveWorkflowContext,
} from '@/components/workflow'
import { ApiError } from '@/api/client'
import { PageBackLink } from '@/components/PageBackLink'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { getProject } from '@/api/projects'
import { saveOfnSaveFeedback } from '@/utils/ofnSaveFeedback'
import {
  applyIteration,
  buildDiffSummary,
  deleteIterationOperation,
  getIterationOperations,
} from '@/api/operations'
import { getProjectOntology } from '@/api/ontology'
import { listTaskPatterns } from '@/api/patterns'
import { listTasks, prepareIteration } from '@/api/tasks'
import { addProjectGuidance } from '@/api/guidance'
import type { OntologyOperationModel } from '@/api/types'
import {
  buildOperationFieldChanges,
  type OperationFieldChange,
} from '@/utils/operationUpdateDiff'
import {
  clearReviewDraft,
  loadReviewDraft,
  saveReviewDraft,
} from '@/utils/reviewDraftStorage'
import { saveAppliedReviewSummary } from '@/utils/appliedReviewStorage'

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
type SummaryFilter = ReviewState | 'all'

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

  const tasksQuery = useQuery({
    queryKey: ['iteration-tasks', projectId, iterationId],
    queryFn: ({ signal }) => listTasks(projectId!, iterationId!, signal),
    enabled: Boolean(projectId) && Boolean(iterationId) && Boolean(taskId),
  })

  const patternsQuery = useQuery({
    queryKey: ['project-patterns', projectId],
    queryFn: ({ signal }) => listTaskPatterns(projectId!, signal),
    enabled: Boolean(projectId) && Boolean(taskId),
  })

  const ontologyQuery = useQuery({
    queryKey: ['project-ontology', projectId],
    queryFn: ({ signal }) => getProjectOntology(projectId!, signal),
    enabled: Boolean(projectId),
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

  const activeTask = useMemo(() => {
    if (!taskId || !tasksQuery.data) return null
    const tasks = [
      ...tasksQuery.data.planned_tasks,
      ...(tasksQuery.data.current_task ? [tasksQuery.data.current_task] : []),
      ...tasksQuery.data.finished_tasks,
    ]
    return tasks.find((task) => task.id === taskId) ?? null
  }, [taskId, tasksQuery.data])

  const activeTaskPattern = useMemo(() => {
    if (!activeTask) return null
    return patternsQuery.data?.patterns.find((pattern) => pattern.id === activeTask.followed_pattern_id) ?? null
  }, [activeTask, patternsQuery.data])

  const [reviewById, setReviewById] = useState<Record<string, ReviewState>>({})
  const [rejectionReasonById, setRejectionReasonById] = useState<Record<string, string>>({})
  const [rejectModalOpId, setRejectModalOpId] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const [savedGuidanceIds, setSavedGuidanceIds] = useState<Record<string, string>>({})
  const [saveRejectReasonAsGuidance, setSaveRejectReasonAsGuidance] = useState(false)
  const [finalizeConfirmOpen, setFinalizeConfirmOpen] = useState(false)
  const [summaryFilter, setSummaryFilter] = useState<SummaryFilter>('all')
  const [draftReady, setDraftReady] = useState(false)
  const hydratedDraftKeyRef = useRef<string | null>(null)

  const operationIds = useMemo(() => new Set(operations.map((op) => op.id)), [operations])
  const draftScopeKey =
    isScopedReview && projectId && iterationId && taskId
      ? `${projectId}:${iterationId}:${taskId}`
      : null

  useEffect(() => {
    setSaveRejectReasonAsGuidance(false)
  }, [rejectModalOpId])

  useEffect(() => {
    setSummaryFilter('all')
  }, [draftScopeKey])

  useEffect(() => {
    if (!draftScopeKey) {
      hydratedDraftKeyRef.current = null
      setDraftReady(false)
      return
    }
    if (hydratedDraftKeyRef.current !== draftScopeKey) {
      hydratedDraftKeyRef.current = null
      setDraftReady(false)
    }
  }, [draftScopeKey])

  useEffect(() => {
    if (!draftScopeKey || !projectId || !iterationId || !taskId) return
    if (operationsQuery.isLoading) return
    if (hydratedDraftKeyRef.current === draftScopeKey) return

    const draft = loadReviewDraft(projectId, iterationId, taskId, operationIds)
    if (draft) {
      setReviewById(draft.reviewById)
      setRejectionReasonById(draft.rejectionReasonById)
      setSavedGuidanceIds(draft.savedGuidanceIds)
    } else {
      setReviewById({})
      setRejectionReasonById({})
      setSavedGuidanceIds({})
    }

    hydratedDraftKeyRef.current = draftScopeKey
    setDraftReady(true)
  }, [
    draftScopeKey,
    projectId,
    iterationId,
    taskId,
    operationIds,
    operationsQuery.isLoading,
  ])

  useEffect(() => {
    if (!draftReady || !draftScopeKey || !projectId || !iterationId || !taskId) return

    saveReviewDraft(
      projectId,
      iterationId,
      taskId,
      { reviewById, rejectionReasonById, savedGuidanceIds },
      operationIds,
    )
  }, [
    draftReady,
    draftScopeKey,
    projectId,
    iterationId,
    taskId,
    reviewById,
    rejectionReasonById,
    savedGuidanceIds,
    operationIds,
  ])

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
  const filteredOperations = useMemo(() => {
    if (summaryFilter === 'all') return operations
    return operations.filter((op) => reviewOf(op.id) === summaryFilter)
  }, [operations, reviewById, summaryFilter]) // eslint-disable-line react-hooks/exhaustive-deps
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
      setFinalizeConfirmOpen(false)
      if (data.ofn_saved && projectId && data.ofn_path && data.ofn_absolute_path) {
        saveOfnSaveFeedback({
          projectId,
          path: data.ofn_path,
          absolutePath: data.ofn_absolute_path,
          pojmyCount: data.ofn_pojmy_count ?? 0,
          overwroteExisting: Boolean(data.ofn_overwrote_existing),
          savedAt: new Date().toISOString(),
        })
      }
      if (isScopedReview && projectId && iterationId && taskId) {
        const rejected = operations
          .filter((op) => (reviewById[op.id] ?? 'pending') === 'rejected')
          .map((op) => ({
            ...op,
            rejectionReason: rejectionReasonById[op.id]?.trim() || undefined,
          }))
        saveAppliedReviewSummary(projectId, iterationId, {
          taskId,
          taskName: activeTask?.name ?? 'Work item',
          finalizedAt: new Date().toISOString(),
          kept: approvedOperations,
          rejected,
        })
        clearReviewDraft(projectId, iterationId, taskId)
        hydratedDraftKeyRef.current = null
        setDraftReady(false)
      }
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
        <div className="rounded-2xl border border-amber-200 bg-amber-50 p-6 text-sm text-amber-900">
          No direction selected. Prepare a direction on the{' '}
          <Link to="/tasks" search={{ projectId, domainId, iterationId, taskId }} className="font-medium underline">
            prepare changes page
          </Link>{' '}
          first.
        </div>
      </div>
    )
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

  const hasOperations = operations.length > 0
  const isPrepared = operationsQuery.data?.status === 'prepared'
  const decidedCount = counts.approved + counts.rejected
  const reviewProgressPercent =
    counts.total > 0 ? Math.round((decidedCount / counts.total) * 100) : 0
  const canFinalize =
    isPrepared && approvedOperations.length > 0 && counts.pending === 0

  const handleRegenerateChange = async (operationId: string) => {
    const reason = rejectionReasonById[operationId]?.trim()
    const ok = window.confirm(
      reason
        ? 'Regenerate this rejected change? The assistant will try again using your rejection reason.'
        : 'Regenerate this rejected change? The assistant will try again using your project guidance.',
    )
    if (!ok) return
    setActionError(null)
    try {
      if (reason && !savedGuidanceIds[operationId]) {
        await saveGuidanceMutation.mutateAsync({ operationId, reason })
      }
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

  const applyButtonLabel = isScopedReview
    ? applyMutation.isPending
      ? 'Finalizing…'
      : `Finalize ${approvedOperations.length} kept change${approvedOperations.length === 1 ? '' : 's'}`
    : applyMutation.isPending
      ? 'Applying…'
      : `Apply ${approvedOperations.length} kept change${approvedOperations.length === 1 ? '' : 's'}`

  const applyButtonTitle = !isPrepared
    ? 'Direction is not ready for review yet.'
    : approvedOperations.length === 0
      ? 'Keep at least one change first.'
      : isScopedReview && counts.pending > 0
        ? `Decide ${counts.pending} pending change${counts.pending === 1 ? '' : 's'} first.`
        : isScopedReview
          ? 'Finalize the kept changes for this work item.'
          : 'Apply the kept changes to the ontology.'

  const handleApplyClick = () => {
    if (isScopedReview) {
      if (!canFinalize) return
      setFinalizeConfirmOpen(true)
      return
    }
    applyMutation.mutate()
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <PageBackLink to="/tasks" search={tasksSearch} label="prepare changes" />
      <WorkflowContextCapsule linkContext={linkContext} />

      {isScopedReview ? (
        <section className="rounded-xl border border-emerald-200 bg-emerald-50/80 px-4 py-4 text-sm text-emerald-950">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="min-w-0 flex-1">
              <p className="text-xs font-semibold uppercase tracking-wide text-emerald-800">
                Work item under review
              </p>
              <h3 className="mt-1 text-lg font-semibold text-slate-950">
                {activeTask?.name ?? 'Selected work item'}
              </h3>
              <p className="mt-2 text-xs font-medium text-emerald-900/90">
                Modeling pattern:{' '}
                {activeTaskPattern?.name ?? activeTask?.followed_pattern_id ?? '—'}
                {activeTaskPattern?.category ? ` (${activeTaskPattern.category})` : ''}
              </p>
              <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-700">
                {activeTask?.specification ??
                  'This work item explains what the assistant was asked to model in this review.'}
              </p>
              {!hasTraceableScope ? (
                <p className="mt-2 text-xs text-emerald-900/80">
                  Some older operations do not include work item traceability yet, so the full prepared set is
                  shown.
                </p>
              ) : null}
              <Link
                to="/operations"
                search={{ projectId, domainId, iterationId, taskId: undefined }}
                className="mt-3 inline-flex text-xs font-semibold text-emerald-800 underline"
              >
                Review all prepared changes
              </Link>
            </div>

            <div className="w-full rounded-xl border border-emerald-200 bg-white/80 p-4 sm:w-80 lg:hidden">
              <ReviewDecisionProgress
                decidedCount={decidedCount}
                totalCount={counts.total}
                pendingCount={counts.pending}
                progressPercent={reviewProgressPercent}
              />
            </div>
          </div>
        </section>
      ) : null}

      <div className="flex flex-wrap items-center gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm shadow-sm">
        <span className="font-medium text-slate-700">Summary:</span>
        <SummaryFilterChip
          label={`Kept ${counts.approved}`}
          active={summaryFilter === 'approved'}
          onClick={() => setSummaryFilter(summaryFilter === 'approved' ? 'all' : 'approved')}
          className="bg-emerald-50 text-emerald-900 hover:bg-emerald-100"
          activeClassName="ring-2 ring-emerald-400 ring-offset-1"
        />
        <SummaryFilterChip
          label={`Pending ${counts.pending}`}
          active={summaryFilter === 'pending'}
          onClick={() => setSummaryFilter(summaryFilter === 'pending' ? 'all' : 'pending')}
          className="bg-slate-100 text-slate-700 hover:bg-slate-200"
          activeClassName="ring-2 ring-slate-400 ring-offset-1"
        />
        <SummaryFilterChip
          label={`Rejected ${counts.rejected}`}
          active={summaryFilter === 'rejected'}
          onClick={() => setSummaryFilter(summaryFilter === 'rejected' ? 'all' : 'rejected')}
          className="bg-rose-50 text-rose-900 hover:bg-rose-100"
          activeClassName="ring-2 ring-rose-400 ring-offset-1"
        />
        <SummaryFilterChip
          label={`Total ${counts.total}`}
          active={summaryFilter === 'all'}
          onClick={() => setSummaryFilter('all')}
          className="bg-slate-100 text-slate-700 hover:bg-slate-200"
          activeClassName="ring-2 ring-slate-400 ring-offset-1"
        />
        {operationsQuery.isFetching ? <span className="text-xs text-slate-500">refreshing…</span> : null}
      </div>

      {!isScopedReview ? (
        <p className="rounded-lg border border-amber-200 bg-amber-50/80 px-3 py-2 text-xs text-amber-900">
          This is the full prepared set. For less context at once, go back to prepare changes and review one
          work item at a time. Apply sends only kept changes to the backend.
        </p>
      ) : (
        <p className="rounded-lg border border-amber-200 bg-amber-50/80 px-3 py-2 text-xs text-amber-900">
          Decide each change once. Finalize writes kept changes to the backend and you will not be able
          to change them here again; rejected changes stay out of the ontology.
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
                ? 'The AI proposed these ontology changes for the selected work item. Keep what should be applied, reject anything wrong, then finalize the kept set.'
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
                If the direction is not ready for review yet, prepare it from{' '}
                <Link to="/tasks" search={tasksSearch} className="font-medium underline">
                  the prepare changes page
                </Link>
                .
              </p>
            </div>
          ) : !hasOperations ? (
            <div className="rounded-xl border border-dashed border-amber-300 bg-amber-50/70 px-4 py-6 text-sm text-amber-950">
              <p className="font-medium">No proposed changes for this direction.</p>
              <p className="mt-1 text-amber-900/90">
                Prepare or re-prepare the selected direction from the prepare changes page so the assistant can propose
                changes.
              </p>
            </div>
          ) : filteredOperations.length === 0 ? (
            <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50 px-4 py-6 text-sm text-slate-600">
              <p className="font-medium text-slate-800">
                No {summaryFilter === 'approved' ? 'kept' : summaryFilter === 'rejected' ? 'rejected' : 'pending'}{' '}
                changes in this view.
              </p>
              <button
                type="button"
                onClick={() => setSummaryFilter('all')}
                className="mt-2 text-xs font-semibold text-emerald-700 hover:underline"
              >
                Show all {counts.total} changes
              </button>
            </div>
          ) : (
            <ul className="space-y-2">
              {filteredOperations.map((op) => {
                const state = reviewOf(op.id)
                const refs = op.specification_references ?? op.references ?? []
                const rejectionReason = rejectionReasonById[op.id]?.trim()
                const updateChanges = buildOperationFieldChanges(ontologyQuery.data, op)
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
                        {state === 'rejected' && rejectionReason ? (
                          <p className="mt-2 rounded-lg border border-rose-200 bg-rose-50 px-2 py-1.5 text-[11px] leading-5 text-rose-900">
                            <span className="font-medium">Rejection reason:</span> {rejectionReason}
                          </p>
                        ) : null}
                        <OperationUpdateDiff
                          operation={op}
                          changes={updateChanges}
                          isLoading={ontologyQuery.isLoading}
                        />
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
                        {state === 'pending' ? (
                          <>
                            <button
                              type="button"
                              className="rounded border border-emerald-200 bg-emerald-50 px-2 py-1 text-[11px] font-medium text-emerald-800 hover:bg-emerald-100"
                              onClick={() => setReview(op.id, 'approved')}
                            >
                              Keep this change
                            </button>
                            <button
                              type="button"
                              className="rounded border border-rose-200 bg-rose-50 px-2 py-1 text-[11px] font-medium text-rose-700 hover:bg-rose-100"
                              onClick={() => setRejectModalOpId(op.id)}
                            >
                              Reject this change
                            </button>
                          </>
                        ) : (
                          <>
                            <button
                              type="button"
                              className="rounded border border-slate-200 bg-white px-2 py-1 text-[11px] font-medium text-slate-700 hover:bg-slate-50"
                              onClick={() => setReview(op.id, 'pending')}
                            >
                              Cancel decision
                            </button>
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
                          </>
                        )}
                      </div>
                    </div>
                  </li>
                )
              })}
            </ul>
          )}

        </div>

        <aside className="w-full shrink-0 space-y-4 lg:sticky lg:top-6 lg:w-96 lg:max-h-[calc(100vh-1.5rem)] lg:overflow-y-auto">
          {isScopedReview ? (
            <div className="hidden rounded-2xl border border-slate-200 bg-white p-4 shadow-sm lg:block">
              <ReviewDecisionProgress
                decidedCount={decidedCount}
                totalCount={counts.total}
                pendingCount={counts.pending}
                progressPercent={reviewProgressPercent}
              />
            </div>
          ) : null}
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
            {isScopedReview && counts.pending > 0 ? (
              <p className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900">
                Decide {counts.pending} pending change{counts.pending === 1 ? '' : 's'} before finalizing.
              </p>
            ) : null}
            <button
              type="button"
              disabled={
                applyMutation.isPending ||
                (isScopedReview ? !canFinalize : !isPrepared || approvedOperations.length === 0)
              }
              onClick={handleApplyClick}
              className="rounded-lg bg-emerald-600 py-2.5 text-center text-sm font-semibold text-white shadow-sm disabled:opacity-60"
              title={applyButtonTitle}
            >
              {applyButtonLabel}
            </button>
          </div>
        </aside>
      </div>

      {finalizeConfirmOpen && isScopedReview ? (
        <ConfirmDialog
          tone="primary"
          title={`Finalize ${approvedOperations.length} kept change${approvedOperations.length === 1 ? '' : 's'}?`}
          description="Kept changes are written into the project ontology and the project OFN file is regenerated (overwrites data/projects/{id}/ofn.json if it already exists). Pending changes are not applied."
          confirmLabel="Finalize & save OFN"
          isConfirmPending={applyMutation.isPending}
          onConfirm={() => applyMutation.mutate()}
          onCancel={() => setFinalizeConfirmOpen(false)}
        />
      ) : null}

      {rejectModalOp ? (
        <RejectModal
          operation={rejectModalOp}
          rejectionReason={rejectionReasonById[rejectModalOp.id] ?? ''}
          onReasonChange={(value) =>
            setRejectionReasonById((prev) => ({ ...prev, [rejectModalOp.id]: value }))
          }
          saveAsGuidance={saveRejectReasonAsGuidance}
          onSaveAsGuidanceChange={setSaveRejectReasonAsGuidance}
          guidanceAlreadySaved={Boolean(savedGuidanceIds[rejectModalOp.id])}
          isConfirmPending={saveGuidanceMutation.isPending}
          onConfirmReject={async () => {
            const reason = rejectionReasonById[rejectModalOp.id]?.trim()
            try {
              if (
                saveRejectReasonAsGuidance &&
                reason &&
                !savedGuidanceIds[rejectModalOp.id]
              ) {
                await saveGuidanceMutation.mutateAsync({ operationId: rejectModalOp.id, reason })
              }
              setReview(rejectModalOp.id, 'rejected')
              setRejectModalOpId(null)
            } catch {
              // saveGuidanceMutation.onError surfaces the message.
            }
          }}
          onCancel={() => setRejectModalOpId(null)}
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
  saveAsGuidance: boolean
  onSaveAsGuidanceChange: (value: boolean) => void
  guidanceAlreadySaved: boolean
  isConfirmPending: boolean
  onConfirmReject: () => void | Promise<void>
  onCancel: () => void
}

function RejectModal({
  operation,
  rejectionReason,
  onReasonChange,
  saveAsGuidance,
  onSaveAsGuidanceChange,
  guidanceAlreadySaved,
  isConfirmPending,
  onConfirmReject,
  onCancel,
}: RejectModalProps) {
  const hasReason = rejectionReason.trim().length > 0

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
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-rose-700">Reject change</p>
          <p className="mt-2 text-sm font-medium text-slate-900">{operation.label ?? operation.uri}</p>
          <p className="mt-0.5 break-all font-mono text-[11px] text-slate-500">{operation.uri}</p>
          {operation.definition ? (
            <p className="mt-2 text-xs text-slate-700">{operation.definition}</p>
          ) : operation.description ? (
            <p className="mt-2 text-xs text-slate-700">{operation.description}</p>
          ) : null}
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
          <label className="mt-3 flex items-start gap-2">
            <input
              type="checkbox"
              checked={saveAsGuidance || guidanceAlreadySaved}
              disabled={!hasReason || guidanceAlreadySaved || isConfirmPending}
              onChange={(event) => onSaveAsGuidanceChange(event.target.checked)}
              className="mt-0.5 rounded border-rose-300 text-rose-700 focus:ring-rose-500"
            />
            <span className="text-[11px] leading-5 text-slate-700">
              Save reason as project guidance for future work
              {guidanceAlreadySaved ? (
                <span className="mt-0.5 block text-slate-500">Already saved to guidance.</span>
              ) : null}
            </span>
          </label>
          <p className="mt-2 text-[11px] leading-5 text-slate-600">
            This reason will be used as extra context when you regenerate this change.
          </p>
          <p className="mt-2 text-[11px] leading-5 text-rose-900/80">
            Rejected changes stay visible in the list but are excluded when you apply kept changes. Use
            Regenerate if you want the assistant to try again.
          </p>
        </div>

        <div className="mt-5 flex flex-wrap justify-end gap-2 border-t border-slate-100 pt-4">
          <button
            type="button"
            className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            onClick={onCancel}
            disabled={isConfirmPending}
          >
            Cancel
          </button>
          <button
            type="button"
            className="rounded-lg bg-rose-700 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-rose-800 disabled:opacity-60"
            onClick={() => void onConfirmReject()}
            disabled={isConfirmPending}
          >
            {isConfirmPending ? 'Saving…' : 'Mark rejected'}
          </button>
        </div>
      </div>
    </div>
  )
}

function ReviewDecisionProgress({
  decidedCount,
  totalCount,
  pendingCount,
  progressPercent,
}: {
  decidedCount: number
  totalCount: number
  pendingCount: number
  progressPercent: number
}) {
  return (
    <div>
      <div className="flex items-center justify-between gap-3 text-xs font-semibold uppercase tracking-wide text-emerald-800">
        <span>Review progress</span>
        <span>{progressPercent}%</span>
      </div>
      <div className="mt-3 h-2 overflow-hidden rounded-full bg-emerald-100">
        <div className="h-full rounded-full bg-emerald-600" style={{ width: `${progressPercent}%` }} />
      </div>
      <p className="mt-2 text-xs leading-5 text-slate-700">
        {decidedCount} of {totalCount} decided
        {pendingCount > 0 ? (
          <>
            {' '}
            · {pendingCount} still pending
          </>
        ) : (
          <> · ready to finalize</>
        )}
      </p>
    </div>
  )
}

type OperationUpdateDiffProps = {
  operation: OntologyOperationModel
  changes: OperationFieldChange[]
  isLoading: boolean
}

function OperationUpdateDiff({ operation, changes, isLoading }: OperationUpdateDiffProps) {
  if (operation.operation_type !== 'update') return null

  if (isLoading) {
    return <p className="mt-2 text-[11px] text-slate-500">Loading current ontology values…</p>
  }

  if (changes.length === 0) {
    return (
      <p className="mt-2 text-[11px] text-slate-500">
        No field differences detected against the current ontology.
      </p>
    )
  }

  return (
    <div className="mt-3 rounded-lg border border-amber-200 bg-amber-50/70 p-2.5">
      <p className="text-[11px] font-semibold uppercase tracking-wide text-amber-900">What changes</p>
      <ul className="mt-2 space-y-2">
        {changes.map((change) => (
          <li key={`${operation.id}-${change.field}`} className="text-[11px] leading-5 text-slate-700">
            <span className="font-medium text-slate-900">{change.field}</span>
            <div className="mt-0.5 rounded border border-rose-200/80 bg-white px-2 py-1 text-rose-900 line-through decoration-rose-400/80">
              {change.before}
            </div>
            <div className="mt-1 rounded border border-emerald-200/80 bg-white px-2 py-1 text-emerald-900">
              {change.after}
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}

type SummaryFilterChipProps = {
  label: string
  active: boolean
  onClick: () => void
  className: string
  activeClassName: string
}

function SummaryFilterChip({
  label,
  active,
  onClick,
  className,
  activeClassName,
}: SummaryFilterChipProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={`rounded-full px-2.5 py-0.5 text-xs font-semibold transition ${className} ${
        active ? activeClassName : ''
      }`}
    >
      {label}
    </button>
  )
}

function toErrorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message
  if (error instanceof Error) return error.message
  return 'Request failed.'
}
