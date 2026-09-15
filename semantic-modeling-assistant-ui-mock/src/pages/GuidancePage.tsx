import { Link, getRouteApi } from '@tanstack/react-router'
import { useMemo, useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ApiError } from '@/api/client'
import {
  addProjectGuidance,
  deleteProjectGuidance,
  listProjectGuidance,
  updateProjectGuidance,
} from '@/api/guidance'
import { getProject } from '@/api/projects'
import type { DesignIterationModel, GuidanceItemSource, GuidanceItemType } from '@/api/types'
import { resolveWorkflowContext } from '@/components/workflow'
import { PageBackLink } from '@/components/PageBackLink'
import { listAppliedReviewSummariesForProject } from '@/utils/appliedReviewStorage'

const guidanceRouteApi = getRouteApi('/guidance')

const GUIDANCE_TYPES: GuidanceItemType[] = ['instruction', 'correction', 'preference', 'constraint']

const typeStyles: Record<GuidanceItemType, string> = {
  instruction: 'bg-sky-50 text-sky-900',
  correction: 'bg-rose-50 text-rose-900',
  preference: 'bg-violet-50 text-violet-900',
  constraint: 'bg-amber-50 text-amber-950',
}

const typeLabels: Record<GuidanceItemType, string> = {
  instruction: 'Instruction',
  correction: 'Correction',
  preference: 'Preference',
  constraint: 'Constraint',
}

const sourceLabels: Record<GuidanceItemSource, string> = {
  manual: 'Manual',
  correction: 'Rejection',
  saved_from_request: 'Saved from request',
}

type CreateFormState = {
  type: GuidanceItemType
  content: string
}

type EditFormState = {
  type: GuidanceItemType
  content: string
}

const INITIAL_CREATE: CreateFormState = {
  type: 'instruction',
  content: '',
}

export function GuidancePage() {
  const { projectId } = guidanceRouteApi.useSearch()
  const linkContext = resolveWorkflowContext({ projectId })
  const queryClient = useQueryClient()

  const [createForm, setCreateForm] = useState<CreateFormState>(INITIAL_CREATE)
  const [createError, setCreateError] = useState<string | null>(null)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editForm, setEditForm] = useState<EditFormState>({ type: 'instruction', content: '' })
  const [itemError, setItemError] = useState<string | null>(null)

  const projectQuery = useQuery({
    queryKey: ['project', projectId],
    queryFn: ({ signal }) => getProject(projectId!, signal),
    enabled: Boolean(projectId),
  })

  const guidanceQuery = useQuery({
    queryKey: ['project-guidance', projectId],
    queryFn: ({ signal }) => listProjectGuidance(projectId!, signal),
    enabled: Boolean(projectId),
  })

  const items = useMemo(() => {
    const list = guidanceQuery.data?.items ?? []
    return [...list].sort((left, right) => compareOptionalIso(right.created_at, left.created_at))
  }, [guidanceQuery.data?.items])

  const decisions = useMemo(
    () => (projectId ? listAppliedReviewSummariesForProject(projectId) : []),
    [projectId],
  )

  const historyEntries = useMemo(
    () => buildHistoryEntries(items, projectQuery.data ?? null, decisions),
    [items, projectQuery.data, decisions],
  )

  const invalidateGuidance = async () => {
    if (!projectId) return
    await queryClient.invalidateQueries({ queryKey: ['project-guidance', projectId] })
  }

  const addMutation = useMutation({
    mutationFn: () =>
      addProjectGuidance(projectId!, {
        content: createForm.content.trim(),
        type: createForm.type,
        source: 'manual',
      }),
    onSuccess: async () => {
      setCreateError(null)
      setCreateForm(INITIAL_CREATE)
      await invalidateGuidance()
    },
    onError: (error: unknown) => setCreateError(toErrorMessage(error)),
  })

  const updateMutation = useMutation({
    mutationFn: () =>
      updateProjectGuidance(projectId!, editingId!, {
        content: editForm.content.trim(),
        type: editForm.type,
      }),
    onSuccess: async () => {
      setItemError(null)
      setEditingId(null)
      await invalidateGuidance()
    },
    onError: (error: unknown) => setItemError(toErrorMessage(error)),
  })

  const deleteMutation = useMutation({
    mutationFn: (itemId: string) => deleteProjectGuidance(projectId!, itemId),
    onSuccess: async () => {
      setItemError(null)
      setEditingId(null)
      await invalidateGuidance()
    },
    onError: (error: unknown) => setItemError(toErrorMessage(error)),
  })

  const handleCreate = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!createForm.content.trim()) {
      setCreateError('Guidance text is required.')
      return
    }
    addMutation.mutate()
  }

  const handleSaveEdit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!editForm.content.trim()) {
      setItemError('Guidance text is required.')
      return
    }
    updateMutation.mutate()
  }

  if (!projectId) {
    return (
      <div className="mx-auto max-w-3xl space-y-4">
        <div className="rounded-2xl border border-amber-200 bg-amber-50 p-6 text-sm text-amber-900">
          No project selected. Open the{' '}
          <Link to="/project" search={{ projectId: undefined }} className="font-medium underline">
            project setup page
          </Link>{' '}
          and pick or create a project first.
        </div>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-4xl space-y-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-slate-900">Project guidance</h2>
          <p className="mt-1 text-sm text-slate-600">
            Persistent instructions, corrections, preferences, and constraints merged into every
            assistant call. Remove items the assistant should stop following.
          </p>
        </div>
        <PageBackLink
          to="/operations"
          label="operations"
          search={{
            projectId,
            domainId: linkContext.domainId,
            iterationId: linkContext.iterationId,
            taskId: linkContext.taskId,
          }}
        />
      </div>

      <section className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Add guidance</h3>
        <form className="mt-4 space-y-4" onSubmit={handleCreate}>
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-slate-700" htmlFor="g-type">
                Guidance type
              </label>
              <select
                id="g-type"
                className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                value={createForm.type}
                onChange={(event) =>
                  setCreateForm((prev) => ({ ...prev, type: event.target.value as GuidanceItemType }))
                }
              >
                {GUIDANCE_TYPES.map((type) => (
                  <option key={type} value={type}>
                    {typeLabels[type]}
                  </option>
                ))}
              </select>
            </div>
            <div className="sm:col-span-2">
              <label className="block text-sm font-medium text-slate-700" htmlFor="g-text">
                Guidance text
              </label>
              <textarea
                id="g-text"
                rows={3}
                placeholder="Write guidance the assistant should follow in all future steps…"
                className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                value={createForm.content}
                onChange={(event) =>
                  setCreateForm((prev) => ({ ...prev, content: event.target.value }))
                }
              />
            </div>
          </div>
          {createError ? (
            <p className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-900">
              {createError}
            </p>
          ) : null}
          <button
            type="submit"
            disabled={addMutation.isPending}
            className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-60"
          >
            {addMutation.isPending ? 'Saving…' : 'Save guidance item'}
          </button>
        </form>
      </section>

      <section>
        <div className="flex items-baseline justify-between gap-2">
          <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Active items</h3>
          {guidanceQuery.isFetching ? (
            <span className="text-xs text-slate-500">refreshing…</span>
          ) : (
            <span className="text-xs text-slate-500">
              {items.length} item{items.length === 1 ? '' : 's'}
            </span>
          )}
        </div>
        {guidanceQuery.isError ? (
          <p className="mt-3 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-900">
            Could not load guidance: {(guidanceQuery.error as Error).message}
          </p>
        ) : null}
        {itemError ? (
          <p className="mt-3 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-900">
            {itemError}
          </p>
        ) : null}
        {guidanceQuery.isSuccess && items.length === 0 ? (
          <p className="mt-4 rounded-xl border border-dashed border-slate-200 bg-slate-50/70 p-4 text-sm text-slate-600">
            No guidance yet. Add an item here, or save a rejection reason from the operations review.
          </p>
        ) : null}
        <ul className="mt-4 space-y-3">
          {items.map((item) => {
            const isEditing = editingId === item.id
            return (
              <li key={item.id} className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                {isEditing ? (
                  <form className="space-y-3" onSubmit={handleSaveEdit}>
                    <select
                      className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                      value={editForm.type}
                      onChange={(event) =>
                        setEditForm((prev) => ({
                          ...prev,
                          type: event.target.value as GuidanceItemType,
                        }))
                      }
                    >
                      {GUIDANCE_TYPES.map((type) => (
                        <option key={type} value={type}>
                          {typeLabels[type]}
                        </option>
                      ))}
                    </select>
                    <textarea
                      rows={3}
                      className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                      value={editForm.content}
                      onChange={(event) =>
                        setEditForm((prev) => ({ ...prev, content: event.target.value }))
                      }
                    />
                    <div className="flex gap-2">
                      <button
                        type="submit"
                        disabled={updateMutation.isPending}
                        className="rounded-lg bg-slate-900 px-3 py-1.5 text-xs font-medium text-white disabled:opacity-60"
                      >
                        {updateMutation.isPending ? 'Saving…' : 'Save'}
                      </button>
                      <button
                        type="button"
                        className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-700"
                        onClick={() => setEditingId(null)}
                      >
                        Cancel
                      </button>
                    </div>
                  </form>
                ) : (
                  <>
                    <div className="flex flex-wrap items-center gap-2">
                      <span
                        className={`rounded-full px-2 py-0.5 text-xs font-semibold ${typeStyles[item.type]}`}
                      >
                        {typeLabels[item.type]}
                      </span>
                      {item.source ? (
                        <span className="rounded-md bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
                          Source: {sourceLabels[item.source]}
                        </span>
                      ) : null}
                      {item.created_at ? (
                        <span className="text-xs text-slate-400">{formatDate(item.created_at)}</span>
                      ) : null}
                    </div>
                    <p className="mt-2 text-sm leading-relaxed text-slate-800">{item.content}</p>
                    <div className="mt-3 flex gap-3 text-xs font-medium">
                      <button
                        type="button"
                        className="text-emerald-700"
                        onClick={() => {
                          setItemError(null)
                          setEditingId(item.id)
                          setEditForm({ type: item.type, content: item.content })
                        }}
                      >
                        Edit
                      </button>
                      <button
                        type="button"
                        className="text-rose-700 disabled:opacity-60"
                        disabled={deleteMutation.isPending}
                        onClick={() => {
                          if (
                            window.confirm(
                              'Remove this guidance item? The assistant will stop following it.',
                            )
                          ) {
                            deleteMutation.mutate(item.id)
                          }
                        }}
                      >
                        Delete
                      </button>
                    </div>
                  </>
                )}
              </li>
            )
          })}
        </ul>
      </section>

      <section className="rounded-xl border border-dashed border-slate-200 bg-slate-50/50 p-4 text-sm text-slate-600">
        <strong className="text-slate-800">History</strong>
        <p className="mt-1 text-xs text-slate-500">
          Guidance changes, iteration status, and keep/reject decisions from this browser.
        </p>
        {historyEntries.length === 0 ? (
          <p className="mt-2 text-sm text-slate-500">No history for this project yet.</p>
        ) : (
          <ul className="mt-2 space-y-1">
            {historyEntries.map((entry) => (
              <li key={entry.id} className="text-sm text-slate-600">
                {entry.at ? `${entry.at} — ` : ''}
                <span className="font-medium text-slate-800">{entry.action}</span>
                {': '}
                {entry.detail}
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}

type HistoryEntry = {
  id: string
  at?: string
  action: string
  detail: string
  sortKey: number
}

function buildHistoryEntries(
  items: { id: string; type: GuidanceItemType; content: string; created_at?: string | null; source?: GuidanceItemSource | null }[],
  project: {
    planned_iterations: DesignIterationModel[]
    current_iteration?: DesignIterationModel | null
    finished_iterations: DesignIterationModel[]
  } | null,
  decisions: ReturnType<typeof listAppliedReviewSummariesForProject>,
): HistoryEntry[] {
  const entries: HistoryEntry[] = items.map((item) => ({
    id: `guidance-${item.id}`,
    at: item.created_at ? formatDate(item.created_at) : undefined,
    action: `Guidance (${typeLabels[item.type]})`,
    detail: item.content,
    sortKey: parseIso(item.created_at),
  }))

  for (const decision of decisions) {
    entries.push({
      id: `decision-${decision.taskId}-${decision.finalizedAt}`,
      at: formatDate(decision.finalizedAt),
      action: 'Decision',
      detail: `${decision.taskName}: kept ${decision.kept.length}, rejected ${decision.rejected.length}`,
      sortKey: parseIso(decision.finalizedAt),
    })
  }

  if (project) {
    const iterations: Array<DesignIterationModel & { bucket: string }> = [
      ...project.finished_iterations.map((iteration) => ({ ...iteration, bucket: 'finished' })),
      ...(project.current_iteration
        ? [{ ...project.current_iteration, bucket: 'current' }]
        : []),
      ...project.planned_iterations.map((iteration) => ({ ...iteration, bucket: 'planned' })),
    ]
    for (const iteration of iterations) {
      entries.push({
        id: `iteration-${iteration.id}`,
        action: `Iteration (${iteration.bucket})`,
        detail: `${iteration.name} — ${iteration.status.replace(/_/g, ' ')}`,
        sortKey: 0,
      })
    }
  }

  return entries.sort((left, right) => right.sortKey - left.sortKey || left.action.localeCompare(right.action))
}

function compareOptionalIso(left?: string | null, right?: string | null): number {
  return parseIso(left) - parseIso(right)
}

function parseIso(value?: string | null): number {
  if (!value) return 0
  const time = new Date(value).getTime()
  return Number.isFinite(time) ? time : 0
}

function formatDate(value: string): string {
  const date = new Date(value)
  if (!Number.isFinite(date.getTime())) return value
  return date.toLocaleString()
}

function toErrorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message
  if (error instanceof Error) return error.message
  return 'Request failed.'
}
