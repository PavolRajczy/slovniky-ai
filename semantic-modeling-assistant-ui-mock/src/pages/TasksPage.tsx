import { Link, getRouteApi, useNavigate } from '@tanstack/react-router'
import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  WorkflowContextCapsule,
  WorkflowStepper,
  resolveWorkflowContext,
} from '@/components/workflow'
import { ApiError } from '@/api/client'
import { getProject } from '@/api/projects'
import { listIterations } from '@/api/iterations'
import { listTaskPatterns } from '@/api/patterns'
import {
  createTask,
  deleteTask,
  listTasks,
  planTasks,
  prepareIteration,
  updateTask,
} from '@/api/tasks'
import type {
  DesignIterationModel,
  DesignTaskModel,
  DesignTaskStatus,
} from '@/api/types'

const tasksRouteApi = getRouteApi('/tasks')

const COLUMNS: Array<{ id: DesignTaskStatus; label: string; description: string }> = [
  { id: 'planned', label: 'Planned', description: 'Tasks queued before iteration is prepared.' },
  {
    id: 'generating',
    label: 'Generating / ready',
    description: 'AI is generating operations, or operations are prepared and waiting for review.',
  },
  {
    id: 'completed',
    label: 'Completed',
    description: 'Tasks whose iteration was applied on the operations page.',
  },
]

const columnStyles: Record<DesignTaskStatus, string> = {
  planned: 'bg-slate-50 text-slate-700',
  generating: 'bg-amber-50 text-amber-800',
  completed: 'bg-emerald-50 text-emerald-800',
}

type TaskFormState = {
  name: string
  specification: string
  patternId: string
}

const INITIAL_TASK_FORM: TaskFormState = { name: '', specification: '', patternId: '' }

export function TasksPage() {
  const { projectId, domainId, iterationId, taskId } = tasksRouteApi.useSearch()
  const linkContext = resolveWorkflowContext({ projectId, domainId, iterationId, taskId })
  const navigate = useNavigate()
  const queryClient = useQueryClient()

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
    onSuccess: invalidateTasks,
  })

  const prepareMutation = useMutation({
    mutationFn: () => prepareIteration(projectId!, activeIterationId!),
    onSuccess: async (data) => {
      setPrepareError(null)
      await invalidateTasks()
      await navigate({
        to: '/operations',
        search: {
          projectId,
          domainId: activeIteration?.focused_area_id ?? domainId,
          iterationId: data.iteration_id,
          taskId: undefined,
        },
      })
    },
    onError: (error: unknown) => setPrepareError(toErrorMessage(error)),
  })

  if (!projectId) {
    return (
      <div className="mx-auto max-w-3xl space-y-4">
        <WorkflowStepper activeStep="tasks" linkContext={linkContext} />
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
        <WorkflowStepper activeStep="tasks" linkContext={linkContext} />
        <div className="rounded-2xl border border-amber-200 bg-amber-50 p-6 text-sm text-amber-900">
          This project has no iterations yet. Create or suggest one in the{' '}
          <Link to="/iterations" search={{ projectId, domainId: undefined }} className="font-medium underline">
            iterations page
          </Link>
          .
        </div>
      </div>
    )
  }

  const tasks = collectTasks(tasksQuery.data ?? null)
  const tasksByStatus = groupByStatus(tasks)
  const isIterationPlanned = activeIteration?.status === 'planned' || activeIteration?.status === 'suggested'
  const canMutateTasks = isIterationPlanned

  const handleCreateTask = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!taskForm.name.trim() || !taskForm.specification.trim() || !taskForm.patternId) {
      setTaskFormError('Name, specification and pattern are required.')
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
      setEditError('Name, specification and pattern are required.')
      return
    }
    updateMutation.mutate({ taskId: editingId, form: editForm })
  }

  const handleDelete = (task: DesignTaskModel) => {
    const ok = window.confirm(`Delete task "${task.name}"?`)
    if (!ok) return
    deleteMutation.mutate(task.id)
  }

  const handlePrepare = () => {
    const ok = window.confirm(
      `Prepare iteration "${activeIteration?.name ?? ''}"? AI will generate operations for each task. This may take a few minutes.`,
    )
    if (!ok) return
    prepareMutation.mutate()
  }

  return (
    <div className="mx-auto max-w-6xl space-y-8">
      <WorkflowStepper activeStep="tasks" linkContext={linkContext} />
      <WorkflowContextCapsule linkContext={linkContext} />

      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-slate-900">Tasks</h2>
          <p className="mt-1 text-sm text-slate-600">
            Plan the iteration's tasks (or add them manually), then prepare the iteration to generate
            ontology operations.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link
            to="/iterations"
            search={{ projectId, domainId }}
            className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Back to iterations
          </Link>
        </div>
      </div>

      <section className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Iteration</h3>
            <div className="mt-1 flex flex-wrap items-center gap-2">
              <label htmlFor="iteration-picker" className="text-xs text-slate-600">
                Selected:
              </label>
              <select
                id="iteration-picker"
                value={activeIterationId ?? ''}
                onChange={(event) => {
                  const next = event.target.value
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
                className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-800 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
              >
                {allIterations.map((it) => (
                  <option key={it.id} value={it.id}>
                    {it.name} — {it.status}
                  </option>
                ))}
              </select>
            </div>
            {activeIteration ? (
              <p className="mt-2 text-sm text-slate-700">{activeIteration.specification}</p>
            ) : null}
          </div>
          {activeIteration ? (
            <button
              type="button"
              onClick={handlePrepare}
              disabled={
                !canMutateTasks ||
                tasks.length === 0 ||
                prepareMutation.isPending ||
                projectQuery.isLoading
              }
              className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white shadow-sm disabled:opacity-60"
              title={
                !canMutateTasks
                  ? 'Iteration is already prepared or finished.'
                  : tasks.length === 0
                  ? 'Add at least one task before preparing.'
                  : 'Generate operations and open operations review.'
              }
            >
              {prepareMutation.isPending ? 'Preparing…' : 'Run iteration → operations'}
            </button>
          ) : null}
        </div>
        {prepareError ? (
          <p className="mt-3 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-900">
            {prepareError}
          </p>
        ) : null}
      </section>

      {activeIteration?.status === 'prepared' ? (
        <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          <p className="font-medium">Iteration is prepared — tasks stay in "Generating / ready" until applied.</p>
          <p className="mt-1 text-amber-900/90">
            Review and apply the generated operations on the{' '}
            <Link
              to="/operations"
              search={{
                projectId,
                domainId: activeIteration.focused_area_id,
                iterationId: activeIterationId,
                taskId: undefined,
              }}
              className="font-medium underline"
            >
              operations page
            </Link>
            . After Apply, tasks move to the Completed column.
          </p>
        </div>
      ) : null}

      {canMutateTasks ? (
        <section className="rounded-2xl border border-slate-200/80 bg-white shadow-sm">
          <details className="group [&_summary::-webkit-details-marker]:hidden" open={tasks.length === 0}>
            <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-5 py-4 text-left sm:px-6">
              <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
                Plan tasks with AI
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
                The AI reviews the iteration specification and produces a task plan. Optional steering
                instruction below.
              </p>
              <textarea
                rows={2}
                value={planInstruction}
                onChange={(event) => setPlanInstruction(event.target.value)}
                placeholder="Prefer 3–5 tasks; cover classes, attributes and relationships separately."
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
                  {planMutation.isPending ? 'Planning…' : tasks.length === 0 ? 'Plan tasks' : 'Re-plan tasks'}
                </button>
                {planMutation.isSuccess && planMutation.data ? (
                  <span className="text-xs text-emerald-700">
                    Planned {planMutation.data.length} task
                    {planMutation.data.length === 1 ? '' : 's'}.
                  </span>
                ) : null}
              </div>
            </div>
          </details>
        </section>
      ) : null}

      {canMutateTasks ? (
        <section className="rounded-2xl border border-slate-200/80 bg-white shadow-sm">
          <details className="group [&_summary::-webkit-details-marker]:hidden">
            <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-5 py-4 text-left sm:px-6">
              <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
                Create custom task
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
                  placeholder="Task name"
                  className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                />
                <select
                  value={taskForm.patternId}
                  onChange={(event) => setTaskForm((s) => ({ ...s, patternId: event.target.value }))}
                  className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                >
                  <option value="">— pick task pattern —</option>
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
                  placeholder="What should be modeled, validated, or refined in this task."
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
                  {createMutation.isPending ? 'Saving…' : 'Save custom task'}
                </button>
              </div>
            </form>
          </details>
        </section>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-3">
        {COLUMNS.map((column) => (
          <section key={column.id} className="rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
                {column.label}
              </h3>
              <span
                className={`rounded-full px-2 py-0.5 text-xs font-medium capitalize ${columnStyles[column.id]}`}
              >
                {(tasksByStatus.get(column.id) ?? []).length}
              </span>
            </div>
            <p className="mt-1 text-[11px] text-slate-500">{column.description}</p>
            <div className="mt-4 space-y-3">
              {tasksQuery.isLoading ? (
                <p className="text-xs text-slate-500">Loading tasks…</p>
              ) : (tasksByStatus.get(column.id) ?? []).length === 0 ? (
                <p className="rounded-lg border border-dashed border-slate-200 bg-slate-50 px-3 py-3 text-center text-xs text-slate-500">
                  No tasks.
                </p>
              ) : (
                (tasksByStatus.get(column.id) ?? []).map((task) => {
                  const isEditing = canMutateTasks && editingId === task.id
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
                      className="rounded-xl border border-slate-200 bg-slate-50/60 p-3"
                    >
                      <p className="text-sm font-semibold text-slate-900">{task.name}</p>
                      <p className="mt-1 text-xs text-slate-600">
                        Pattern: {pattern?.name ?? task.followed_pattern_id}
                      </p>
                      <p className="mt-2 text-xs text-slate-700 line-clamp-3">{task.specification}</p>
                      <div className="mt-3 flex flex-wrap gap-2">
                        {task.status === 'completed' ? (
                          <Link
                            to="/operations"
                            search={{
                              projectId,
                              domainId: activeIteration?.focused_area_id ?? domainId,
                              iterationId: activeIterationId,
                              taskId: task.id,
                            }}
                            className="rounded-md bg-emerald-600 px-2.5 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-emerald-700"
                          >
                            Review operations
                          </Link>
                        ) : null}
                        {canMutateTasks && task.status === 'planned' ? (
                          <>
                            <button
                              type="button"
                              onClick={() => startEdit(task)}
                              className="rounded-md border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
                            >
                              Edit
                            </button>
                            <button
                              type="button"
                              onClick={() => handleDelete(task)}
                              disabled={
                                deleteMutation.isPending && deleteMutation.variables === task.id
                              }
                              className="rounded-md border border-rose-200 bg-white px-2.5 py-1.5 text-xs font-medium text-rose-700 hover:bg-rose-50 disabled:opacity-60"
                            >
                              Delete
                            </button>
                          </>
                        ) : null}
                      </div>
                    </article>
                  )
                })
              )}
            </div>
          </section>
        ))}
      </div>
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

function toErrorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message
  if (error instanceof Error) return error.message
  return 'Request failed.'
}
