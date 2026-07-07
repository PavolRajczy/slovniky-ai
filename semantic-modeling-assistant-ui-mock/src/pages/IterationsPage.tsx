import { Link, getRouteApi } from '@tanstack/react-router'
import { useMemo, useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  WorkflowContextCapsule,
  WorkflowStepper,
  resolveWorkflowContext,
} from '@/components/workflow'
import { ApiError } from '@/api/client'
import { listDomainAreas } from '@/api/domainAreas'
import {
  createIteration,
  deleteIteration,
  listIterations,
  suggestIterations,
  updateIteration,
} from '@/api/iterations'
import type {
  DesignIterationModel,
  DesignIterationStatus,
  KnowledgeDomainAreaModel,
} from '@/api/types'

const iterationsRouteApi = getRouteApi('/iterations')

const statusStyles: Record<DesignIterationStatus, string> = {
  suggested: 'bg-slate-100 text-slate-700',
  planned: 'bg-sky-50 text-sky-800',
  prepared: 'bg-amber-50 text-amber-900',
  completed: 'bg-emerald-50 text-emerald-800',
}

const statusLabels: Record<DesignIterationStatus, string> = {
  suggested: 'Suggested',
  planned: 'Planned',
  prepared: 'Ready for tasks',
  completed: 'Completed',
}

type SuggestFormState = {
  focusedAreaId: string
  goal: string
  subareaUris: string
  count: number
}

type ManualFormState = {
  name: string
  specification: string
  focusedAreaId: string
}

const INITIAL_MANUAL: ManualFormState = { name: '', specification: '', focusedAreaId: '' }

export function IterationsPage() {
  const { projectId, domainId } = iterationsRouteApi.useSearch()
  const linkContext = resolveWorkflowContext({ projectId, domainId })
  const queryClient = useQueryClient()

  const areasQuery = useQuery({
    queryKey: ['project-domain-areas', projectId],
    queryFn: ({ signal }) => listDomainAreas(projectId!, signal),
    enabled: Boolean(projectId),
  })

  const iterationsQuery = useQuery({
    queryKey: ['project-iterations', projectId, domainId ?? 'all'],
    queryFn: ({ signal }) =>
      listIterations(projectId!, { areaId: domainId }, signal),
    enabled: Boolean(projectId),
  })

  const areas = useMemo<KnowledgeDomainAreaModel[]>(() => areasQuery.data ?? [], [areasQuery.data])
  const selectedDomain = useMemo(
    () => (domainId ? areas.find((a) => a.id === domainId) : undefined),
    [areas, domainId],
  )

  const [suggestForm, setSuggestForm] = useState<SuggestFormState>({
    focusedAreaId: '',
    goal: '',
    subareaUris: '',
    count: 3,
  })
  const [suggestError, setSuggestError] = useState<string | null>(null)
  const [manualForm, setManualForm] = useState<ManualFormState>(INITIAL_MANUAL)
  const [manualError, setManualError] = useState<string | null>(null)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editForm, setEditForm] = useState<ManualFormState>(INITIAL_MANUAL)
  const [editError, setEditError] = useState<string | null>(null)

  // Seed focused area from URL when areas load
  const effectiveSuggestAreaId = suggestForm.focusedAreaId || domainId || areas[0]?.id || ''
  const effectiveManualAreaId = manualForm.focusedAreaId || domainId || areas[0]?.id || ''

  const invalidate = async () => {
    if (!projectId) return
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ['project-iterations', projectId] }),
      queryClient.invalidateQueries({ queryKey: ['project', projectId] }),
    ])
  }

  const suggestMutation = useMutation({
    mutationFn: () => {
      const userInstruction = composeSuggestionInstruction(suggestForm)
      return suggestIterations(projectId!, {
        focused_area_id: effectiveSuggestAreaId,
        count: suggestForm.count,
        user_instruction: userInstruction || null,
      })
    },
    onSuccess: async () => {
      setSuggestError(null)
      await invalidate()
    },
    onError: (error: unknown) => setSuggestError(toErrorMessage(error)),
  })

  const createMutation = useMutation({
    mutationFn: (form: ManualFormState) =>
      createIteration(projectId!, {
        name: form.name.trim(),
        specification: form.specification.trim(),
        focused_area_id: form.focusedAreaId,
      }),
    onSuccess: async () => {
      setManualError(null)
      setManualForm(INITIAL_MANUAL)
      await invalidate()
    },
    onError: (error: unknown) => setManualError(toErrorMessage(error)),
  })

  const updateMutation = useMutation({
    mutationFn: ({ iterationId, form }: { iterationId: string; form: ManualFormState }) =>
      updateIteration(projectId!, iterationId, {
        name: form.name.trim(),
        specification: form.specification.trim(),
        focused_area_id: form.focusedAreaId,
      }),
    onSuccess: async () => {
      setEditError(null)
      setEditingId(null)
      await invalidate()
    },
    onError: (error: unknown) => setEditError(toErrorMessage(error)),
  })

  const deleteMutation = useMutation({
    mutationFn: (iterationId: string) => deleteIteration(projectId!, iterationId),
    onSuccess: invalidate,
  })

  if (!projectId) {
    return (
      <div className="mx-auto max-w-3xl space-y-4">
        <WorkflowStepper activeStep="iterations" linkContext={linkContext} />
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

  const planned = iterationsQuery.data?.planned_iterations ?? []
  const current = iterationsQuery.data?.current_iteration ?? null
  const finished = iterationsQuery.data?.finished_iterations ?? []

  const handleSuggest = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!effectiveSuggestAreaId) {
      setSuggestError('Pick a domain area to focus the suggestion on.')
      return
    }
    if (suggestForm.count < 1 || suggestForm.count > 10) {
      setSuggestError('Count must be between 1 and 10.')
      return
    }
    setSuggestForm((s) => ({ ...s, focusedAreaId: effectiveSuggestAreaId }))
    suggestMutation.mutate()
  }

  const handleCreate = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const focusedAreaId = manualForm.focusedAreaId || effectiveManualAreaId
    if (!manualForm.name.trim() || !manualForm.specification.trim()) {
      setManualError('Name and specification are required.')
      return
    }
    if (!focusedAreaId) {
      setManualError('Pick a domain area for the iteration.')
      return
    }
    createMutation.mutate({ ...manualForm, focusedAreaId })
  }

  const startEdit = (iteration: DesignIterationModel) => {
    setEditingId(iteration.id)
    setEditForm({
      name: iteration.name,
      specification: iteration.specification,
      focusedAreaId: iteration.focused_area_id,
    })
    setEditError(null)
  }

  const handleSaveEdit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!editingId) return
    if (!editForm.name.trim() || !editForm.specification.trim() || !editForm.focusedAreaId) {
      setEditError('All fields are required.')
      return
    }
    updateMutation.mutate({ iterationId: editingId, form: editForm })
  }

  const handleDelete = (iteration: DesignIterationModel) => {
    const ok = window.confirm(`Delete iteration "${iteration.name}"? This cannot be undone.`)
    if (!ok) return
    deleteMutation.mutate(iteration.id)
  }

  return (
    <div className="mx-auto max-w-5xl space-y-8">
      <WorkflowStepper activeStep="iterations" linkContext={linkContext} />
      <WorkflowContextCapsule linkContext={linkContext} />

      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-slate-900">Modeling iterations</h2>
          <p className="mt-1 text-sm text-slate-600">
            Suggest the next useful pieces of work for a domain area. You do not need to know the whole
            plan upfront - after reviewing changes, you can come back and ask for more iterations.
          </p>
        </div>
        <div className="text-right text-xs text-slate-500">
          {iterationsQuery.isFetching ? 'refreshing…' : null}
        </div>
      </div>

      <section className="grid gap-3 rounded-2xl border border-emerald-200/80 bg-emerald-50/60 p-4 shadow-sm md:grid-cols-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-emerald-800">1. Suggest next work</p>
          <p className="mt-1 text-sm text-emerald-950">
            Pick a domain area and describe what you want to improve next.
          </p>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-emerald-800">2. Review the result</p>
          <p className="mt-1 text-sm text-emerald-950">
            Plan tasks, prepare changes, then approve or reject what the AI proposes.
          </p>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-emerald-800">3. Continue if needed</p>
          <p className="mt-1 text-sm text-emerald-950">
            If the model still needs work, return here and suggest another set of iterations.
          </p>
        </div>
      </section>

      <section className="rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Domain summary</h3>
        {selectedDomain ? (
          <div className="mt-2">
            <p className="text-sm font-semibold text-slate-900">{selectedDomain.label}</p>
            <p className="mt-1 text-sm text-slate-600">{selectedDomain.description}</p>
            {selectedDomain.key_concepts.length > 0 ? (
              <div className="mt-2 flex flex-wrap gap-1">
                {selectedDomain.key_concepts.map((c) => (
                  <span
                    key={c}
                    className="rounded-md bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700"
                  >
                    {c}
                  </span>
                ))}
              </div>
            ) : null}
          </div>
        ) : domainId ? (
          <p className="mt-2 text-sm text-amber-700">
            No domain selected for <span className="font-mono">{domainId}</span>. Showing all iterations.
          </p>
        ) : (
          <p className="mt-2 text-sm text-slate-600">No domain filter. Showing iterations across all areas.</p>
        )}
      </section>

      <section className="rounded-2xl border border-slate-200/80 bg-white shadow-sm">
        <details className="group [&_summary::-webkit-details-marker]:hidden" open>
          <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-5 py-4 text-left sm:px-6">
            <div>
              <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Suggest next iterations</h3>
              <p className="mt-1 text-xs normal-case tracking-normal text-slate-600">
                Ask for the next few useful iterations now. You can repeat this later after the current work is reviewed.
              </p>
            </div>
            <span
              className="shrink-0 text-slate-400 transition-transform duration-200 group-open:rotate-180"
              aria-hidden
            >
              ▼
            </span>
          </summary>
          <form onSubmit={handleSuggest} className="border-t border-slate-100 px-5 pb-6 pt-2 sm:px-6">
            <div className="grid gap-4">
              <div>
                <label className="block text-xs font-medium text-slate-700" htmlFor="suggest-area">
                  Selected domain area
                </label>
                <select
                  id="suggest-area"
                  value={effectiveSuggestAreaId}
                  onChange={(event) =>
                    setSuggestForm((s) => ({ ...s, focusedAreaId: event.target.value }))
                  }
                  className="mt-1 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                >
                  <option value="">— pick area —</option>
                  {areas.map((area) => (
                    <option key={area.id} value={area.id}>
                      {area.label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-700" htmlFor="suggest-goal">
                  Goal (optional)
                </label>
                <textarea
                  id="suggest-goal"
                  rows={2}
                  value={suggestForm.goal}
                  onChange={(event) => setSuggestForm((s) => ({ ...s, goal: event.target.value }))}
                  placeholder="Add missing attributes for Section 12 classes."
                  className="mt-1 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                />
              </div>
            </div>

            <details className="mt-5 rounded-xl border border-slate-200 bg-slate-50/70">
              <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-4 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500 [&::-webkit-details-marker]:hidden">
                Suggest iteration configuration
                <span className="text-slate-400" aria-hidden>
                  optional
                </span>
              </summary>
              <div className="border-t border-slate-200 px-4 pb-4 pt-3">
                <p className="text-xs text-slate-600">
                  Most users can leave this closed. Open it only when you want to control the number of
                  suggestions or restrict the AI to specific ontology classes.
                </p>
                <div className="mt-3 grid gap-4 md:grid-cols-[12rem_1fr]">
                  <div>
                    <label className="block text-xs font-medium text-slate-700" htmlFor="suggest-count">
                      Number of suggestions
                    </label>
                    <input
                      id="suggest-count"
                      type="number"
                      min={1}
                      max={10}
                      value={suggestForm.count}
                      onChange={(event) =>
                        setSuggestForm((s) => ({ ...s, count: Number(event.target.value) || 1 }))
                      }
                      className="mt-1 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-slate-700" htmlFor="suggest-subarea">
                      Limit to class URIs (optional, one per line)
                    </label>
                    <textarea
                      id="suggest-subarea"
                      rows={3}
                      value={suggestForm.subareaUris}
                      onChange={(event) =>
                        setSuggestForm((s) => ({ ...s, subareaUris: event.target.value }))
                      }
                      placeholder={'https://example.org/ontology#RoadSign\nhttps://example.org/ontology#Crossroad'}
                      className="mt-1 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 font-mono text-xs text-slate-800 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                    />
                  </div>
                </div>
              </div>
            </details>
            {suggestError ? (
              <p className="mt-3 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-900">
                {suggestError}
              </p>
            ) : null}
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <button
                type="submit"
                disabled={suggestMutation.isPending || areas.length === 0}
                className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
              >
                {suggestMutation.isPending ? 'Suggesting…' : 'Suggest next iterations'}
              </button>
              {suggestMutation.isSuccess && suggestMutation.data ? (
                <span className="text-xs text-emerald-700">
                  Added {suggestMutation.data.length} suggestion
                  {suggestMutation.data.length === 1 ? '' : 's'} to the planned list. You can ask for more later.
                </span>
              ) : null}
            </div>
          </form>
        </details>
      </section>

      <section className="rounded-2xl border border-slate-200/80 bg-white shadow-sm">
        <details className="group [&_summary::-webkit-details-marker]:hidden">
          <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-5 py-4 text-left sm:px-6">
            <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Create iteration manually</h3>
            <span
              className="shrink-0 text-slate-400 transition-transform duration-200 group-open:rotate-180"
              aria-hidden
            >
              ▼
            </span>
          </summary>
          <form onSubmit={handleCreate} className="border-t border-slate-100 px-5 pb-6 pt-2 sm:px-6">
            <div className="grid gap-3 md:grid-cols-2">
              <input
                value={manualForm.name}
                onChange={(event) => setManualForm((s) => ({ ...s, name: event.target.value }))}
                placeholder="Iteration name"
                className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
              />
              <select
                value={manualForm.focusedAreaId || effectiveManualAreaId}
                onChange={(event) =>
                  setManualForm((s) => ({ ...s, focusedAreaId: event.target.value }))
                }
                className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
              >
                <option value="">— pick area —</option>
                {areas.map((area) => (
                  <option key={area.id} value={area.id}>
                    {area.label}
                  </option>
                ))}
              </select>
              <textarea
                value={manualForm.specification}
                onChange={(event) =>
                  setManualForm((s) => ({ ...s, specification: event.target.value }))
                }
                rows={2}
                placeholder="What this iteration should achieve — scope, goals, expected ontology outputs."
                className="md:col-span-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
              />
              {manualError ? (
                <p className="md:col-span-2 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-900">
                  {manualError}
                </p>
              ) : null}
            </div>
            <div className="mt-3 flex justify-end">
              <button
                type="submit"
                disabled={createMutation.isPending}
                className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white shadow-sm disabled:opacity-60"
              >
                {createMutation.isPending ? 'Saving…' : 'Save manual iteration'}
              </button>
            </div>
          </form>
        </details>
      </section>

      {iterationsQuery.isError ? (
        <p className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-900">
          {(iterationsQuery.error as Error).message}
        </p>
      ) : null}

      <IterationGroup
        title="Planned"
        items={planned}
        areas={areas}
        editingId={editingId}
        editForm={editForm}
        editError={editError}
        editPending={updateMutation.isPending}
        deletePending={deleteMutation.isPending ? deleteMutation.variables ?? null : null}
        projectId={projectId}
        onSetEditForm={setEditForm}
        onStartEdit={startEdit}
        onCancelEdit={() => {
          setEditingId(null)
          setEditError(null)
        }}
        onSaveEdit={handleSaveEdit}
        onDelete={handleDelete}
        emptyMessage="No planned iterations yet - suggest the next set above. After reviewing changes, you can come back and suggest more."
        editable
        deletable
      />

      {current ? (
        <IterationGroup
          title="Ready for tasks"
          items={[current]}
          areas={areas}
          editingId={null}
          editForm={editForm}
          editError={null}
          editPending={false}
          deletePending={deleteMutation.isPending ? deleteMutation.variables ?? null : null}
          projectId={projectId}
          onSetEditForm={() => undefined}
          onStartEdit={() => undefined}
          onCancelEdit={() => undefined}
          onSaveEdit={() => undefined}
          onDelete={handleDelete}
          emptyMessage=""
          editable={false}
          deletable
        />
      ) : null}

      {finished.length > 0 ? (
        <IterationGroup
          title="Completed"
          items={finished}
          areas={areas}
          editingId={null}
          editForm={editForm}
          editError={null}
          editPending={false}
          deletePending={null}
          projectId={projectId}
          onSetEditForm={() => undefined}
          onStartEdit={() => undefined}
          onCancelEdit={() => undefined}
          onSaveEdit={() => undefined}
          onDelete={() => undefined}
          emptyMessage=""
          editable={false}
          deletable={false}
        />
      ) : null}
    </div>
  )
}

type IterationGroupProps = {
  title: string
  items: DesignIterationModel[]
  areas: KnowledgeDomainAreaModel[]
  editingId: string | null
  editForm: ManualFormState
  editError: string | null
  editPending: boolean
  deletePending: string | null
  projectId: string
  onSetEditForm: (form: ManualFormState | ((prev: ManualFormState) => ManualFormState)) => void
  onStartEdit: (iteration: DesignIterationModel) => void
  onCancelEdit: () => void
  onSaveEdit: (event: FormEvent<HTMLFormElement>) => void
  onDelete: (iteration: DesignIterationModel) => void
  emptyMessage: string
  editable: boolean
  deletable: boolean
}

function IterationGroup(props: IterationGroupProps) {
  const {
    title,
    items,
    areas,
    editingId,
    editForm,
    editError,
    editPending,
    deletePending,
    projectId,
    onSetEditForm,
    onStartEdit,
    onCancelEdit,
    onSaveEdit,
    onDelete,
    emptyMessage,
    editable,
    deletable,
  } = props
  return (
    <section>
      <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">{title}</h3>
      {items.length === 0 ? (
        emptyMessage ? (
          <p className="rounded-2xl border border-dashed border-slate-200 bg-white px-4 py-6 text-center text-sm text-slate-500">
            {emptyMessage}
          </p>
        ) : null
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {items.map((iteration) => {
            const area = areas.find((a) => a.id === iteration.focused_area_id)
            const isEditing = editable && editingId === iteration.id
            if (isEditing) {
              return (
                <article
                  key={iteration.id}
                  className="rounded-2xl border border-emerald-300 bg-white p-5 shadow-sm"
                >
                  <form onSubmit={onSaveEdit} className="space-y-2">
                    <input
                      value={editForm.name}
                      onChange={(event) => onSetEditForm((s) => ({ ...s, name: event.target.value }))}
                      className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                    />
                    <select
                      value={editForm.focusedAreaId}
                      onChange={(event) =>
                        onSetEditForm((s) => ({ ...s, focusedAreaId: event.target.value }))
                      }
                      className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                    >
                      {areas.map((a) => (
                        <option key={a.id} value={a.id}>
                          {a.label}
                        </option>
                      ))}
                    </select>
                    <textarea
                      value={editForm.specification}
                      onChange={(event) =>
                        onSetEditForm((s) => ({ ...s, specification: event.target.value }))
                      }
                      rows={3}
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
                        onClick={onCancelEdit}
                        className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700"
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        disabled={editPending}
                        className="rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white shadow-sm disabled:opacity-60"
                      >
                        {editPending ? 'Saving…' : 'Save changes'}
                      </button>
                    </div>
                  </form>
                </article>
              )
            }
            return (
              <article
                key={iteration.id}
                className="flex h-full flex-col rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm"
              >
                <div className="flex items-start justify-between gap-2">
                  <h4 className="font-semibold text-slate-900">{iteration.name}</h4>
                  <span
                    className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${statusStyles[iteration.status]}`}
                  >
                    {statusLabels[iteration.status]}
                  </span>
                </div>
                {area ? (
                  <p className="mt-1 text-xs text-slate-500">{area.label}</p>
                ) : (
                  <p className="mt-1 font-mono text-[11px] text-slate-400">{iteration.focused_area_id}</p>
                )}
                <p className="mt-3 text-sm text-slate-700 line-clamp-4">{iteration.specification}</p>

                <div className="mt-auto pt-4 space-y-3">
                  <div className="flex items-center justify-between text-xs text-slate-600">
                    <span>Tasks</span>
                    <span className="font-semibold text-slate-800">
                      {iteration.finished_tasks_count}/{iteration.total_tasks} done
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Link
                      to="/tasks"
                      search={{
                        projectId,
                        domainId: iteration.focused_area_id,
                        iterationId: iteration.id,
                        taskId: undefined,
                      }}
                      className="rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-800"
                    >
                      Plan tasks
                    </Link>
                    {editable ? (
                      <button
                        type="button"
                        onClick={() => onStartEdit(iteration)}
                        className="rounded-md border border-slate-200 bg-white px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
                      >
                        Edit
                      </button>
                    ) : null}
                    {deletable ? (
                      <button
                        type="button"
                        onClick={() => onDelete(iteration)}
                        disabled={deletePending === iteration.id}
                        className="rounded-md border border-rose-200 bg-white px-3 py-1.5 text-sm font-medium text-rose-700 hover:bg-rose-50 disabled:opacity-60"
                      >
                        Delete
                      </button>
                    ) : null}
                  </div>
                </div>
              </article>
            )
          })}
        </div>
      )}
    </section>
  )
}

function composeSuggestionInstruction(form: SuggestFormState): string {
  const lines: string[] = []
  const goal = form.goal.trim()
  const subarea = form.subareaUris
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
  if (goal) {
    lines.push(`Goal: ${goal}`)
  }
  if (subarea.length > 0) {
    lines.push('Subarea — restrict focus to these classes:')
    for (const uri of subarea) {
      lines.push(`- ${uri}`)
    }
  }
  return lines.join('\n')
}

function toErrorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message
  if (error instanceof Error) return error.message
  return 'Request failed.'
}
