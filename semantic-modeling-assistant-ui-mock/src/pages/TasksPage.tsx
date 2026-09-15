import { Link, getRouteApi, useNavigate } from '@tanstack/react-router'
import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ApiError } from '@/api/client'
import { PageBackLink } from '@/components/PageBackLink'
import { actionButton, CardActions } from '@/components/ActionButtons'
import { AppliedReviewSummaryModal, buildModalReviewGroups } from '@/components/AppliedReviewSummaryModal'
import { ConfirmDialog } from '@/components/ConfirmDialog'
import { getProject } from '@/api/projects'
import { listIterations } from '@/api/iterations'
import { listTaskPatterns } from '@/api/patterns'
import {
  createTask,
  deleteTask,
  listTasks,
  planTasks,
  prepareIteration,
  prepareTask,
  updateTask,
} from '@/api/tasks'
import type {
  DesignIterationModel,
  DesignIterationStatus,
  DesignTaskModel,
  DesignTaskStatus,
} from '@/api/types'
import {
  listAppliedReviewSummaries,
  mergeAppliedReviewSummaries,
} from '@/utils/appliedReviewStorage'
import {
  clearOfnSaveFeedback,
  readOfnSaveFeedback,
  type OfnSaveFeedback,
} from '@/utils/ofnSaveFeedback'

const tasksRouteApi = getRouteApi('/tasks')

const COLUMNS: Array<{ id: DesignTaskStatus; label: string; description: string }> = [
  { id: 'planned', label: 'To prepare', description: 'Work items waiting before changes are prepared.' },
  {
    id: 'generating',
    label: 'Ready to review',
    description: 'AI is generating changes, or changes are prepared and waiting for review.',
  },
  {
    id: 'completed',
    label: 'Applied',
    description: 'Work items whose approved changes were applied.',
  },
]

const columnStyles: Record<DesignTaskStatus, string> = {
  planned: 'bg-slate-50 text-slate-700',
  generating: 'bg-amber-50 text-amber-800',
  completed: 'bg-emerald-50 text-emerald-800',
}

const iterationStatusLabels: Record<DesignIterationStatus, string> = {
  suggested: 'Suggested',
  planned: 'Planned',
  prepared: 'Ready to review',
  completed: 'Applied',
}

type TaskFormState = {
  name: string
  specification: string
  patternId: string
}

const INITIAL_TASK_FORM: TaskFormState = { name: '', specification: '', patternId: '' }

export function TasksPage() {
  const { projectId, domainId, iterationId } = tasksRouteApi.useSearch()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [ofnFeedback, setOfnFeedback] = useState<OfnSaveFeedback | null>(null)

  useEffect(() => {
    if (!projectId) {
      setOfnFeedback(null)
      return
    }
    setOfnFeedback(readOfnSaveFeedback(projectId))
  }, [projectId])

  const projectQuery = useQuery({
    queryKey: ['project', projectId],
    queryFn: ({ signal }) => getProject(projectId!, signal),
    enabled: Boolean(projectId),
  })

  const iterationsQuery = useQuery({
    queryKey: ['project-iterations', projectId, 'all'],
    queryFn: ({ signal }) => listIterations(projectId!, {}, signal),
    enabled: Boolean(projectId),
  })

  const patternsQuery = useQuery({
    queryKey: ['project-patterns', projectId],
    queryFn: ({ signal }) => listTaskPatterns(projectId!, signal),
    enabled: Boolean(projectId),
  })

  const allIterations = useMemo<DesignIterationModel[]>(() => {
    const it = iterationsQuery.data
    if (!it) return []
    return [...it.planned_iterations, ...(it.current_iteration ? [it.current_iteration] : []), ...it.finished_iterations]
  }, [iterationsQuery.data])

  const activeIterationId = iterationId ?? allIterations[0]?.id
  const activeIteration = useMemo(
    () => allIterations.find((it) => it.id === activeIterationId),
    [allIterations, activeIterationId],
  )

  const tasksQuery = useQuery({
    queryKey: ['iteration-tasks', projectId, activeIterationId],
    queryFn: ({ signal }) => listTasks(projectId!, activeIterationId!, signal),
    enabled: Boolean(projectId) && Boolean(activeIterationId),
  })

  const patterns = useMemo(() => patternsQuery.data?.patterns ?? [], [patternsQuery.data])

  const [taskForm, setTaskForm] = useState<TaskFormState>(INITIAL_TASK_FORM)
  const [taskFormError, setTaskFormError] = useState<string | null>(null)
  const [planInstruction, setPlanInstruction] = useState('')
  const [planError, setPlanError] = useState<string | null>(null)
  const [prepareError, setPrepareError] = useState<string | null>(null)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editForm, setEditForm] = useState<TaskFormState>(INITIAL_TASK_FORM)
  const [editError, setEditError] = useState<string | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<DesignTaskModel | null>(null)
  const [appliedSummaryOpen, setAppliedSummaryOpen] = useState(false)
  const [appliedSummaryFocusTaskId, setAppliedSummaryFocusTaskId] = useState<string | null>(null)

  // Default pattern in form once patterns load
  useEffect(() => {
    if (patterns.length > 0 && !taskForm.patternId) {
      setTaskForm((s) => ({ ...s, patternId: patterns[0].id }))
    }
  }, [patterns, taskForm.patternId])

  const invalidateTasks = async () => {
    if (!projectId || !activeIterationId) return
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ['iteration-tasks', projectId, activeIterationId] }),
      queryClient.invalidateQueries({ queryKey: ['project-iterations', projectId] }),
      queryClient.invalidateQueries({ queryKey: ['project', projectId] }),
    ])
  }

  const planMutation = useMutation({
    mutationFn: () =>
      planTasks(projectId!, activeIterationId!, {
        user_instruction: planInstruction.trim() || null,
      }),
    onSuccess: async () => {
      setPlanError(null)
      await invalidateTasks()
    },
    onError: (error: unknown) => setPlanError(toErrorMessage(error)),
  })

  const createMutation = useMutation({
    mutationFn: (form: TaskFormState) =>
      createTask(projectId!, activeIterationId!, {
        name: form.name.trim(),
        specification: form.specification.trim(),
        followed_pattern_id: form.patternId,
      }),
    onSuccess: async () => {
      setTaskFormError(null)
      setTaskForm({ name: '', specification: '', patternId: taskForm.patternId })
      await invalidateTasks()
    },
    onError: (error: unknown) => setTaskFormError(toErrorMessage(error)),
  })

  const updateMutation = useMutation({
    mutationFn: ({ taskId: id, form }: { taskId: string; form: TaskFormState }) =>
      updateTask(projectId!, activeIterationId!, id, {
        name: form.name.trim(),
        specification: form.specification.trim(),
        followed_pattern_id: form.patternId,
      }),
    onSuccess: async () => {
      setEditError(null)
      setEditingId(null)
      await invalidateTasks()
    },
    onError: (error: unknown) => setEditError(toErrorMessage(error)),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteTask(projectId!, activeIterationId!, id),
    onSuccess: async () => {
      setDeleteTarget(null)
      await invalidateTasks()
    },
  })

  const prepareMutation = useMutation({
    mutationFn: ({ targetTaskId, openReview }: { targetTaskId?: string; openReview: boolean }) =>
      (targetTaskId
        ? prepareTask(projectId!, activeIterationId!, targetTaskId)
        : prepareIteration(projectId!, activeIterationId!)
      ).then((data) => ({ data, targetTaskId, openReview })),
    onSuccess: async ({ data, targetTaskId, openReview }) => {
      setPrepareError(null)
      await invalidateTasks()
      if (openReview) {
        await navigate({
          to: '/operations',
          search: {
            projectId,
            domainId: activeIteration?.focused_area_id ?? domainId,
            iterationId: data.iteration_id,
            taskId: targetTaskId,
          },
        })
      }
    },
    onError: (error: unknown) => setPrepareError(toErrorMessage(error)),
  })

  if (!projectId) {
    return (
      <div className="mx-auto max-w-3xl space-y-4">
        <div className="rounded-2xl border border-amber-200 bg-amber-50 p-6 text-sm text-amber-900">
          No project selected. Open the{' '}
          <Link to="/project" search={{ projectId: undefined }} className="font-medium underline">
            project setup page
          </Link>{' '}
          first.
        </div>
      </div>
    )
  }

  if (!iterationsQuery.isLoading && allIterations.length === 0) {
    return (
      <div className="mx-auto max-w-3xl space-y-4">
        <div className="rounded-2xl border border-amber-200 bg-amber-50 p-6 text-sm text-amber-900">
          This project has no next directions yet. Ask for one in{' '}
          <Link to="/iterations-v2" search={{ projectId, domainId: undefined }} className="font-medium underline">
            next directions
          </Link>
          .
        </div>
      </div>
    )
  }

  const tasks = collectTasks(tasksQuery.data ?? null)
  const tasksByStatus = groupByStatus(tasks)
  const plannedTasks = tasksByStatus.get('planned') ?? []
  const appliedTasks = tasksByStatus.get('completed') ?? []
  const appliedReviewSummaries = useMemo(
    () =>
      projectId && activeIterationId
        ? listAppliedReviewSummaries(projectId, activeIterationId)
        : [],
    [projectId, activeIterationId, tasks],
  )
  const mergedAppliedReview = useMemo(
    () => mergeAppliedReviewSummaries(appliedReviewSummaries),
    [appliedReviewSummaries],
  )
  const appliedSummaryGroups = useMemo(
    () => buildModalReviewGroups(mergedAppliedReview.kept, mergedAppliedReview.rejected),
    [mergedAppliedReview],
  )
  const appliedSummaryFocusTask = appliedSummaryFocusTaskId
    ? appliedTasks.find((task) => task.id === appliedSummaryFocusTaskId) ?? null
    : null
  const isIterationPlanned = activeIteration?.status === 'planned' || activeIteration?.status === 'suggested'
  const canPlanWorkItems = isIterationPlanned
  const canMovePlannedWorkItems = activeIteration?.status !== 'completed'

  const handleCreateTask = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!taskForm.name.trim() || !taskForm.specification.trim() || !taskForm.patternId) {
      setTaskFormError('Name, description and modeling pattern are required.')
      return
    }
    createMutation.mutate(taskForm)
  }

  const startEdit = (task: DesignTaskModel) => {
    setEditingId(task.id)
    setEditForm({
      name: task.name,
      specification: task.specification,
      patternId: task.followed_pattern_id,
    })
    setEditError(null)
  }

  const handleSaveEdit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!editingId) return
    if (!editForm.name.trim() || !editForm.specification.trim() || !editForm.patternId) {
      setEditError('Name, description and modeling pattern are required.')
      return
    }
    updateMutation.mutate({ taskId: editingId, form: editForm })
  }

  const handleDelete = (task: DesignTaskModel) => {
    setDeleteTarget(task)
  }

  const openAppliedSummary = (focusTaskId: string | null) => {
    setAppliedSummaryFocusTaskId(focusTaskId)
    setAppliedSummaryOpen(true)
  }

  const closeAppliedSummary = () => {
    setAppliedSummaryOpen(false)
    setAppliedSummaryFocusTaskId(null)
  }

  const handlePrepare = (targetTaskId?: string, openReview = true) => {
    const ok = window.confirm(
      targetTaskId
        ? `Prepare changes for this work item? AI will prepare changes for the selected direction, then this item should move to Ready to review.`
        : `Prepare changes for "${activeIteration?.name ?? ''}"? AI will generate proposed ontology changes for each work item. This may take a few minutes.`,
    )
    if (!ok) return
    prepareMutation.mutate({ targetTaskId, openReview })
  }

  return (
    <div className="mx-auto max-w-6xl space-y-8">
      <PageBackLink
        to="/iterations-v2"
        search={{ projectId, domainId: activeIteration?.focused_area_id ?? domainId }}
        label="next directions"
      />

      {ofnFeedback ? (
        <section className="rounded-2xl border border-sky-200 bg-sky-50/80 p-4 text-sm text-sky-950 shadow-sm">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="min-w-0 flex-1">
              <p className="text-xs font-semibold uppercase tracking-wide text-sky-800">
                OFN saved on finalize
              </p>
              <p className="mt-1">
                {ofnFeedback.overwroteExisting
                  ? 'Existing project OFN was overwritten.'
                  : 'New project OFN file was created.'}{' '}
                Concepts: <span className="font-semibold tabular-nums">{ofnFeedback.pojmyCount}</span>
              </p>
              <p className="mt-1 break-all font-mono text-[11px] text-sky-900/80">
                {ofnFeedback.absolutePath}
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Link
                to="/export-result"
                search={{
                  projectId,
                  domainId,
                  iterationId,
                  taskId: undefined,
                  approved: undefined,
                  pending: undefined,
                  rejected: undefined,
                  regenerated: undefined,
                  guidanceUpdated: undefined,
                }}
                className="rounded-lg bg-sky-700 px-3 py-2 text-xs font-semibold text-white hover:bg-sky-800"
              >
                Open OFN export
              </Link>
              <button
                type="button"
                onClick={() => {
                  clearOfnSaveFeedback()
                  setOfnFeedback(null)
                }}
                className="rounded-lg border border-sky-200 bg-white px-3 py-2 text-xs font-medium text-sky-900 hover:bg-sky-50"
              >
                Dismiss
              </button>
            </div>
          </div>
        </section>
      ) : null}

      <DirectionWorkPanel
        activeIteration={activeIteration}
        allIterations={allIterations}
        activeIterationId={activeIterationId}
        domainId={domainId}
        projectId={projectId}
        tasks={tasks}
        tasksByStatus={tasksByStatus}
        onSelectIteration={(next) => {
          const target = allIterations.find((it) => it.id === next)
          navigate({
            to: '/tasks',
            search: {
              projectId,
              domainId: target?.focused_area_id ?? domainId,
              iterationId: next,
              taskId: undefined,
            },
          })
        }}
      />

      <div>
        <h2 className="text-2xl font-semibold tracking-tight text-slate-900">Prepare changes</h2>
        <p className="mt-1 text-sm text-slate-600">
          Break the selected direction into concrete work items, then let the assistant prepare proposed
          ontology changes for review.
        </p>
        <p className="mt-2 text-xs text-slate-500">
          For a lighter review, use the arrow on a work item card to move it into Ready to review, then
          review only that item.
        </p>
      </div>

      {prepareError ? (
        <p className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-900">
          {prepareError}
        </p>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-3">
        {COLUMNS.map((column) => (
          <section key={column.id} className="rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm">
            <div className="flex items-center justify-between gap-2">
              <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
                {column.label}
              </h3>
              <div className="flex items-center gap-2">
                {column.id === 'completed' && appliedTasks.length > 0 ? (
                  <button
                    type="button"
                    onClick={() => openAppliedSummary(null)}
                    className="rounded-md border border-slate-200 bg-white px-2 py-0.5 text-[11px] font-medium text-slate-700 hover:bg-slate-50"
                  >
                    View all applied
                  </button>
                ) : null}
                <span
                  className={`rounded-full px-2 py-0.5 text-xs font-medium capitalize ${columnStyles[column.id]}`}
                >
                  {(tasksByStatus.get(column.id) ?? []).length}
                </span>
              </div>
            </div>
            <p className="mt-1 text-[11px] text-slate-500">{column.description}</p>
            {column.id === 'planned' && activeIteration && plannedTasks.length > 0 ? (
              <button
                type="button"
                onClick={() => handlePrepare()}
                disabled={!canMovePlannedWorkItems || prepareMutation.isPending || projectQuery.isLoading}
                className="mt-3 w-full rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm font-semibold text-emerald-800 shadow-sm hover:bg-emerald-100 disabled:opacity-60"
                title={
                  !canMovePlannedWorkItems
                    ? 'This direction is already ready for review or applied.'
                    : 'Generate proposed changes and open review.'
                }
              >
                {prepareMutation.isPending ? 'Preparing…' : 'Prepare all work items'}
              </button>
            ) : null}
            <div className="mt-4 space-y-3">
              {tasksQuery.isLoading ? (
                <p className="text-xs text-slate-500">Loading work items…</p>
              ) : (tasksByStatus.get(column.id) ?? []).length === 0 ? (
                <p className="rounded-lg border border-dashed border-slate-200 bg-slate-50 px-3 py-3 text-center text-xs text-slate-500">
                  No work items.
                </p>
              ) : (
                (tasksByStatus.get(column.id) ?? []).map((task) => {
                  const isEditing = canMovePlannedWorkItems && editingId === task.id
                  const pattern = patterns.find((p) => p.id === task.followed_pattern_id)
                  if (isEditing) {
                    return (
                      <article
                        key={task.id}
                        className="rounded-xl border border-emerald-300 bg-white p-3"
                      >
                        <form onSubmit={handleSaveEdit} className="space-y-2">
                          <input
                            value={editForm.name}
                            onChange={(event) =>
                              setEditForm((s) => ({ ...s, name: event.target.value }))
                            }
                            className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                          />
                          <select
                            value={editForm.patternId}
                            onChange={(event) =>
                              setEditForm((s) => ({ ...s, patternId: event.target.value }))
                            }
                            className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                          >
                            {patterns.map((p) => (
                              <option key={p.id} value={p.id}>
                                {p.name}
                              </option>
                            ))}
                          </select>
                          <textarea
                            value={editForm.specification}
                            onChange={(event) =>
                              setEditForm((s) => ({ ...s, specification: event.target.value }))
                            }
                            rows={2}
                            className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                          />
                          {editError ? (
                            <p className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-900">
                              {editError}
                            </p>
                          ) : null}
                          <div className="flex justify-end gap-2">
                            <button
                              type="button"
                              onClick={() => {
                                setEditingId(null)
                                setEditError(null)
                              }}
                              className="rounded-md border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700"
                            >
                              Cancel
                            </button>
                            <button
                              type="submit"
                              disabled={updateMutation.isPending}
                              className="rounded-md bg-emerald-600 px-2.5 py-1.5 text-xs font-semibold text-white shadow-sm disabled:opacity-60"
                            >
                              {updateMutation.isPending ? 'Saving…' : 'Save'}
                            </button>
                          </div>
                        </form>
                      </article>
                    )
                  }
                  return (
                    <article
                      key={task.id}
                      className={`rounded-xl border bg-slate-50/60 p-3 ${
                        task.status === 'completed'
                          ? 'cursor-pointer border-emerald-200 hover:border-emerald-300 hover:bg-emerald-50/40'
                          : 'border-slate-200'
                      }`}
                      onClick={
                        task.status === 'completed'
                          ? () => openAppliedSummary(task.id)
                          : undefined
                      }
                      onKeyDown={
                        task.status === 'completed'
                          ? (event) => {
                              if (event.key === 'Enter' || event.key === ' ') {
                                event.preventDefault()
                                openAppliedSummary(task.id)
                              }
                            }
                          : undefined
                      }
                      role={task.status === 'completed' ? 'button' : undefined}
                      tabIndex={task.status === 'completed' ? 0 : undefined}
                    >
                      <p className="text-sm font-semibold text-slate-900">{task.name}</p>
                      <p className="mt-1 text-xs text-slate-600">
                        Modeling pattern: {pattern?.name ?? task.followed_pattern_id}
                      </p>
                      <p className="mt-2 text-xs text-slate-700 line-clamp-3">{task.specification}</p>
                      <CardActions className="mt-3">
                        {task.status === 'generating' ? (
                          <Link
                            to="/operations"
                            search={{
                              projectId,
                              domainId: activeIteration?.focused_area_id ?? domainId,
                              iterationId: activeIterationId,
                              taskId: task.id,
                            }}
                            className={actionButton.primarySm}
                            onClick={(event) => event.stopPropagation()}
                          >
                            Review this work item
                          </Link>
                        ) : null}
                        {task.status === 'completed' ? (
                          <button
                            type="button"
                            onClick={(event) => {
                              event.stopPropagation()
                              openAppliedSummary(task.id)
                            }}
                            className={actionButton.secondarySm}
                          >
                            View summary
                          </button>
                        ) : null}
                        {canMovePlannedWorkItems && task.status === 'planned' ? (
                          <>
                            <button
                              type="button"
                              onClick={(event) => {
                                event.stopPropagation()
                                handlePrepare(task.id, false)
                              }}
                              disabled={prepareMutation.isPending || projectQuery.isLoading}
                              className={actionButton.primarySm}
                            >
                              {prepareMutation.isPending && prepareMutation.variables?.targetTaskId === task.id
                                ? 'Preparing…'
                                : 'Prepare'}
                            </button>
                            <button
                              type="button"
                              onClick={(event) => {
                                event.stopPropagation()
                                startEdit(task)
                              }}
                              className={actionButton.secondarySm}
                            >
                              Edit
                            </button>
                            <button
                              type="button"
                              onClick={(event) => {
                                event.stopPropagation()
                                handleDelete(task)
                              }}
                              disabled={
                                deleteMutation.isPending && deleteMutation.variables === task.id
                              }
                              className={actionButton.dangerSm}
                            >
                              Delete
                            </button>
                          </>
                        ) : null}
                      </CardActions>
                    </article>
                  )
                })
              )}
            </div>
          </section>
        ))}
      </div>

      {canPlanWorkItems ? (
        <section className="rounded-2xl border border-slate-200/80 bg-white shadow-sm">
          <details className="group [&_summary::-webkit-details-marker]:hidden" open={tasks.length === 0}>
            <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-5 py-4 text-left sm:px-6">
              <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
                Break direction into work items
              </h3>
              <span
                className="shrink-0 text-slate-400 transition-transform duration-200 group-open:rotate-180"
                aria-hidden
              >
                ▼
              </span>
            </summary>
            <div className="border-t border-slate-100 px-5 pb-6 pt-2 sm:px-6">
              <p className="text-xs text-slate-600">
                The AI reads the selected direction and suggests concrete pieces of work that can become
                ontology changes.
              </p>
              <textarea
                rows={2}
                value={planInstruction}
                onChange={(event) => setPlanInstruction(event.target.value)}
                placeholder="For example: focus first on missing classes, then check attributes and relationships."
                className="mt-2 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
              />
              {planError ? (
                <p className="mt-2 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-900">
                  {planError}
                </p>
              ) : null}
              <div className="mt-2 flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => planMutation.mutate()}
                  disabled={planMutation.isPending || !activeIterationId}
                  className="rounded-lg bg-slate-900 px-3 py-2 text-xs font-medium text-white disabled:opacity-60"
                >
                  {planMutation.isPending
                    ? 'Planning…'
                    : tasks.length === 0
                    ? 'Suggest work items'
                    : 'Suggest work items again'}
                </button>
                {planMutation.isSuccess && planMutation.data ? (
                  <span className="text-xs text-emerald-700">
                    Added {planMutation.data.length} work item
                    {planMutation.data.length === 1 ? '' : 's'}.
                  </span>
                ) : null}
              </div>
            </div>
          </details>
        </section>
      ) : null}

      {canPlanWorkItems ? (
        <section className="rounded-2xl border border-slate-200/80 bg-white shadow-sm">
          <details className="group [&_summary::-webkit-details-marker]:hidden">
            <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-5 py-4 text-left sm:px-6">
              <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
                Advanced: create work item manually
              </h3>
              <span
                className="shrink-0 text-slate-400 transition-transform duration-200 group-open:rotate-180"
                aria-hidden
              >
                ▼
              </span>
            </summary>
            <form onSubmit={handleCreateTask} className="border-t border-slate-100 px-5 pb-6 pt-2 sm:px-6">
              <div className="grid gap-3 md:grid-cols-2">
                <input
                  value={taskForm.name}
                  onChange={(event) => setTaskForm((s) => ({ ...s, name: event.target.value }))}
                  placeholder="Work item name"
                  className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                />
                <select
                  value={taskForm.patternId}
                  onChange={(event) => setTaskForm((s) => ({ ...s, patternId: event.target.value }))}
                  className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                >
                  <option value="">Pick a modeling pattern</option>
                  {patterns.map((pattern) => (
                    <option key={pattern.id} value={pattern.id}>
                      {pattern.name} ({pattern.category})
                    </option>
                  ))}
                </select>
                <textarea
                  value={taskForm.specification}
                  onChange={(event) => setTaskForm((s) => ({ ...s, specification: event.target.value }))}
                  rows={2}
                  placeholder="What should be modeled, validated, or refined in this work item."
                  className="md:col-span-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                />
                {taskFormError ? (
                  <p className="md:col-span-2 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-900">
                    {taskFormError}
                  </p>
                ) : null}
              </div>
              <div className="mt-3 flex justify-end">
                <button
                  type="submit"
                  disabled={createMutation.isPending}
                  className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white shadow-sm disabled:opacity-60"
                >
                  {createMutation.isPending ? 'Saving…' : 'Save manual work item'}
                </button>
              </div>
            </form>
          </details>
        </section>
      ) : null}

      {deleteTarget ? (
        <ConfirmDialog
          title={`Delete work item "${deleteTarget.name}"?`}
          description="This cannot be undone. Any prepared changes for this work item will be removed."
          confirmLabel="Delete work item"
          isConfirmPending={deleteMutation.isPending}
          onConfirm={() => deleteMutation.mutate(deleteTarget.id)}
          onCancel={() => setDeleteTarget(null)}
        />
      ) : null}

      {appliedSummaryOpen ? (
        <AppliedReviewSummaryModal
          title="All applied work items"
          subtitle="Combined summary of kept and rejected changes across every applied work item in this direction."
          keptCount={mergedAppliedReview.kept.length}
          rejectedCount={mergedAppliedReview.rejected.length}
          summaries={appliedSummaryGroups}
          focusTaskName={appliedSummaryFocusTask?.name ?? null}
          onClose={closeAppliedSummary}
        />
      ) : null}
    </div>
  )
}

function collectTasks(data: { planned_tasks: DesignTaskModel[]; current_task: DesignTaskModel | null; finished_tasks: DesignTaskModel[] } | null): DesignTaskModel[] {
  if (!data) return []
  const out: DesignTaskModel[] = [...data.planned_tasks]
  if (data.current_task) out.push(data.current_task)
  out.push(...data.finished_tasks)
  return out
}

function groupByStatus(tasks: DesignTaskModel[]): Map<DesignTaskStatus, DesignTaskModel[]> {
  const map = new Map<DesignTaskStatus, DesignTaskModel[]>()
  for (const status of ['planned', 'generating', 'completed'] as DesignTaskStatus[]) {
    map.set(status, [])
  }
  for (const task of tasks) {
    map.get(task.status)?.push(task)
  }
  return map
}

type DirectionWorkPanelProps = {
  activeIteration: DesignIterationModel | undefined
  allIterations: DesignIterationModel[]
  activeIterationId: string | undefined
  domainId: string | undefined
  projectId: string
  tasks: DesignTaskModel[]
  tasksByStatus: Map<DesignTaskStatus, DesignTaskModel[]>
  onSelectIteration: (iterationId: string) => void
}

function DirectionWorkPanel({
  activeIteration,
  allIterations,
  activeIterationId,
  domainId,
  projectId,
  tasks,
  tasksByStatus,
  onSelectIteration,
}: DirectionWorkPanelProps) {
  const toPrepareCount = tasksByStatus.get('planned')?.length ?? 0
  const readyCount = tasksByStatus.get('generating')?.length ?? 0
  const appliedCount = tasksByStatus.get('completed')?.length ?? 0
  const totalCount = Math.max(tasks.length, 1)
  const progress = Math.round(((readyCount + appliedCount) / totalCount) * 100)

  return (
    <section className="rounded-2xl border border-emerald-200 bg-linear-to-br from-emerald-50 to-white p-5 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <p className="text-xs font-semibold uppercase tracking-wide text-emerald-800">Selected direction</p>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <select
              value={activeIterationId ?? ''}
              onChange={(event) => onSelectIteration(event.target.value)}
              className="max-w-full rounded-lg border border-emerald-200 bg-white px-3 py-2 text-sm font-semibold text-slate-900 shadow-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            >
              {allIterations.map((iteration) => (
                <option key={iteration.id} value={iteration.id}>
                  {iteration.name} - {iterationStatusLabels[iteration.status]}
                </option>
              ))}
            </select>
            <Link
              to="/iterations-v2"
              search={{ projectId, domainId }}
              className="text-xs font-medium text-emerald-800 underline"
            >
              choose another direction
            </Link>
          </div>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-700">
            {activeIteration?.specification ??
              'Choose a direction first, then break it into work items.'}
          </p>
        </div>

        <div className="w-full rounded-xl border border-emerald-200 bg-white/80 p-4 sm:w-80">
          <div className="flex items-center justify-between text-xs font-semibold uppercase tracking-wide text-emerald-800">
            <span>Work progress</span>
            <span>{progress}% ready</span>
          </div>
          <div className="mt-3 h-2 overflow-hidden rounded-full bg-emerald-100">
            <div className="h-full rounded-full bg-emerald-600" style={{ width: `${progress}%` }} />
          </div>
          <div className="mt-3 grid grid-cols-3 gap-2 text-center text-xs">
            <div className="rounded-lg bg-white px-2 py-2">
              <div className="font-semibold text-slate-900">{toPrepareCount}</div>
              <div className="text-slate-500">to prepare</div>
            </div>
            <div className="rounded-lg bg-white px-2 py-2">
              <div className="font-semibold text-slate-900">{readyCount}</div>
              <div className="text-slate-500">to review</div>
            </div>
            <div className="rounded-lg bg-white px-2 py-2">
              <div className="font-semibold text-slate-900">{appliedCount}</div>
              <div className="text-slate-500">applied</div>
            </div>
          </div>
          <p className="mt-3 text-xs leading-5 text-slate-600">
            Next step: move one work item to Ready to review with the arrow, then review just that item.
          </p>
        </div>
      </div>
    </section>
  )
}

function toErrorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message
  if (error instanceof Error) return error.message
  return 'Request failed.'
}
