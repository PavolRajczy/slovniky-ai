import { Link, getRouteApi } from '@tanstack/react-router'
import { useMemo, useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { WorkflowStepper, resolveWorkflowContext } from '@/components/workflow'
import { ApiError } from '@/api/client'
import {
  createDomainArea,
  deleteDomainArea,
  generateDomainAreas,
  listDomainAreas,
  reidentifyDomainAreas,
  updateDomainArea,
} from '@/api/domainAreas'
import { getProject } from '@/api/projects'
import type { KnowledgeDomainAreaModel } from '@/api/types'

const domainAreasRouteApi = getRouteApi('/domain-areas')

type CreateFormState = {
  label: string
  description: string
  keyConcepts: string
}

const INITIAL_CREATE: CreateFormState = {
  label: '',
  description: '',
  keyConcepts: '',
}

type EditFormState = {
  label: string
  description: string
  keyConcepts: string
}

export function DomainAreasPage() {
  const { projectId } = domainAreasRouteApi.useSearch()
  const linkContext = resolveWorkflowContext({ projectId })
  const queryClient = useQueryClient()

  const [createForm, setCreateForm] = useState<CreateFormState>(INITIAL_CREATE)
  const [createError, setCreateError] = useState<string | null>(null)
  const [generateInstruction, setGenerateInstruction] = useState('')
  const [reidentifyInstruction, setReidentifyInstruction] = useState('')
  const [analyzeError, setAnalyzeError] = useState<string | null>(null)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editForm, setEditForm] = useState<EditFormState>({ label: '', description: '', keyConcepts: '' })
  const [editError, setEditError] = useState<string | null>(null)

  const projectQuery = useQuery({
    queryKey: ['project', projectId],
    queryFn: ({ signal }) => getProject(projectId!, signal),
    enabled: Boolean(projectId),
  })

  const areasQuery = useQuery({
    queryKey: ['project-domain-areas', projectId],
    queryFn: ({ signal }) => listDomainAreas(projectId!, signal),
    enabled: Boolean(projectId),
  })

  const invalidateAreas = async () => {
    if (!projectId) return
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ['project-domain-areas', projectId] }),
      queryClient.invalidateQueries({ queryKey: ['project', projectId] }),
    ])
  }

  const generateMutation = useMutation({
    mutationFn: () =>
      generateDomainAreas(projectId!, { user_instruction: generateInstruction.trim() || null }),
    onSuccess: async () => {
      setAnalyzeError(null)
      await invalidateAreas()
    },
    onError: (error: unknown) => setAnalyzeError(toErrorMessage(error)),
  })

  const reidentifyMutation = useMutation({
    mutationFn: () =>
      reidentifyDomainAreas(projectId!, { user_instruction: reidentifyInstruction.trim() }),
    onSuccess: async () => {
      setAnalyzeError(null)
      setReidentifyInstruction('')
      await invalidateAreas()
    },
    onError: (error: unknown) => setAnalyzeError(toErrorMessage(error)),
  })

  const createMutation = useMutation({
    mutationFn: (form: CreateFormState) =>
      createDomainArea(projectId!, {
        label: form.label.trim(),
        description: form.description.trim(),
        key_concepts: splitConcepts(form.keyConcepts),
      }),
    onSuccess: async () => {
      setCreateError(null)
      setCreateForm(INITIAL_CREATE)
      await invalidateAreas()
    },
    onError: (error: unknown) => setCreateError(toErrorMessage(error)),
  })

  const updateMutation = useMutation({
    mutationFn: ({ areaId, form }: { areaId: string; form: EditFormState }) =>
      updateDomainArea(projectId!, areaId, {
        label: form.label.trim(),
        description: form.description.trim(),
        key_concepts: splitConcepts(form.keyConcepts),
      }),
    onSuccess: async () => {
      setEditError(null)
      setEditingId(null)
      await invalidateAreas()
    },
    onError: (error: unknown) => setEditError(toErrorMessage(error)),
  })

  const deleteMutation = useMutation({
    mutationFn: (areaId: string) => deleteDomainArea(projectId!, areaId),
    onSuccess: invalidateAreas,
  })

  const areas = areasQuery.data ?? []
  const hasKeyDoc = Boolean(projectQuery.data?.key_knowledge_document_id)

  const handleCreate = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!createForm.label.trim() || !createForm.description.trim()) {
      setCreateError('Label and description are required.')
      return
    }
    createMutation.mutate(createForm)
  }

  const handleStartEdit = (area: KnowledgeDomainAreaModel) => {
    setEditingId(area.id)
    setEditForm({
      label: area.label,
      description: area.description,
      keyConcepts: area.key_concepts.join(', '),
    })
    setEditError(null)
  }

  const handleSaveEdit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!editingId) return
    if (!editForm.label.trim() || !editForm.description.trim()) {
      setEditError('Label and description are required.')
      return
    }
    updateMutation.mutate({ areaId: editingId, form: editForm })
  }

  const handleDelete = (area: KnowledgeDomainAreaModel) => {
    const ok = window.confirm(`Delete section "${area.label}"? This cannot be undone.`)
    if (!ok) return
    deleteMutation.mutate(area.id)
  }

  const generatePending = generateMutation.isPending
  const reidentifyPending = reidentifyMutation.isPending
  const analyzeBusy = generatePending || reidentifyPending

  const lastMutationMessage = useMemo(() => {
    if (generateMutation.isSuccess && generateMutation.data) {
      return `Suggested ${generateMutation.data.length} section${generateMutation.data.length === 1 ? '' : 's'}.`
    }
    if (reidentifyMutation.isSuccess && reidentifyMutation.data) {
      return `Refined the map - now ${reidentifyMutation.data.length} section${reidentifyMutation.data.length === 1 ? '' : 's'}.`
    }
    return null
  }, [generateMutation.isSuccess, generateMutation.data, reidentifyMutation.isSuccess, reidentifyMutation.data])

  if (!projectId) {
    return (
      <div className="mx-auto max-w-3xl space-y-4">
        <WorkflowStepper activeStep="domain-areas" linkContext={linkContext} />
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
    <div className="mx-auto max-w-5xl space-y-8">
      <WorkflowStepper activeStep="domain-areas" linkContext={linkContext} />

      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-slate-900">Domain map</h2>
          <p className="mt-1 text-sm text-slate-600">
            A simple map of the main topics in this domain. Use it to choose where the assistant should
            explore next, without committing to a fixed modeling plan upfront.
          </p>
        </div>
        <div className="text-right text-xs text-slate-500">
          {areasQuery.isFetching ? 'refreshing…' : `${areas.length} section${areas.length === 1 ? '' : 's'}`}
        </div>
      </div>

      <section className="grid gap-3 rounded-2xl border border-emerald-200/80 bg-emerald-50/60 p-4 shadow-sm md:grid-cols-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-emerald-800">1. Map the domain</p>
          <p className="mt-1 text-sm text-emerald-950">
            Let the assistant split the legal material into understandable topic sections.
          </p>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-emerald-800">2. Choose a section</p>
          <p className="mt-1 text-sm text-emerald-950">
            Pick the part of the domain that looks most useful to work on next.
          </p>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-emerald-800">3. Ask where to go next</p>
          <p className="mt-1 text-sm text-emerald-950">
            Continue to next-direction suggestions for the selected section.
          </p>
        </div>
      </section>

      <section className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">AI suggestions</h3>
        {!hasKeyDoc ? (
          <p className="mt-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900">
            No key document is set on this project. The domain map needs a key document -
            set one on the{' '}
            <Link to="/project" search={{ projectId }} className="font-medium underline">
              project page
            </Link>
            .
          </p>
        ) : null}

        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <div className="rounded-xl border border-slate-200 bg-slate-50/80 p-4">
            <h4 className="text-sm font-semibold text-slate-900">
              {areas.length === 0 ? 'Suggest domain map' : 'Regenerate domain map'}
            </h4>
            <p className="mt-1 text-xs text-slate-600">
              AI analyzes the key document and proposes understandable topic sections. Optional steering
              instruction below.
            </p>
            <textarea
              rows={2}
              value={generateInstruction}
              onChange={(event) => setGenerateInstruction(event.target.value)}
              placeholder="Focus on road infrastructure and traffic management"
              className="mt-2 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />
            <button
              type="button"
              onClick={() => generateMutation.mutate()}
              disabled={!hasKeyDoc || analyzeBusy}
              className="mt-2 rounded-lg bg-slate-900 px-3 py-2 text-xs font-medium text-white disabled:opacity-60"
            >
              {generatePending ? 'Suggesting…' : 'Suggest domain map'}
            </button>
          </div>

          <div className="rounded-xl border border-slate-200 bg-slate-50/80 p-4">
            <h4 className="text-sm font-semibold text-slate-900">Refine the map</h4>
            <p className="mt-1 text-xs text-slate-600">
              Adjust the current sections with a focused instruction. Use this when the map feels too broad,
              too detailed, or misses an important theme.
            </p>
            <textarea
              rows={2}
              value={reidentifyInstruction}
              onChange={(event) => setReidentifyInstruction(event.target.value)}
              placeholder="Split road-safety into infrastructure and driver-behavior subareas"
              className="mt-2 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            />
            <button
              type="button"
              onClick={() => reidentifyMutation.mutate()}
              disabled={
                !hasKeyDoc || analyzeBusy || areas.length === 0 || reidentifyInstruction.trim().length === 0
              }
              className="mt-2 rounded-lg bg-emerald-600 px-3 py-2 text-xs font-medium text-white disabled:opacity-60"
            >
              {reidentifyPending ? 'Refining…' : 'Refine map'}
            </button>
          </div>
        </div>

        {analyzeError ? (
          <p className="mt-3 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-900">
            {analyzeError}
          </p>
        ) : null}
        {lastMutationMessage && !analyzeError ? (
          <p className="mt-3 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs text-emerald-900">
            {lastMutationMessage}
          </p>
        ) : null}
      </section>

      <section className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Create section manually</h3>
        <form onSubmit={handleCreate} className="mt-4 grid gap-3 md:grid-cols-2">
          <input
            value={createForm.label}
            onChange={(event) => setCreateForm((s) => ({ ...s, label: event.target.value }))}
            placeholder="Section name"
            className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
          />
          <input
            value={createForm.keyConcepts}
            onChange={(event) => setCreateForm((s) => ({ ...s, keyConcepts: event.target.value }))}
            placeholder="Key concepts (comma separated)"
            className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
          />
          <textarea
            value={createForm.description}
            onChange={(event) => setCreateForm((s) => ({ ...s, description: event.target.value }))}
            rows={2}
            placeholder="What this section is about and which legal chapters it covers."
            className="md:col-span-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
          />
          {createError ? (
            <p className="md:col-span-2 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-900">
              {createError}
            </p>
          ) : null}
          <div className="md:col-span-2 flex justify-end">
            <button
              type="submit"
              disabled={createMutation.isPending}
              className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white shadow-sm disabled:opacity-60"
            >
              {createMutation.isPending ? 'Saving…' : 'Save manual section'}
            </button>
          </div>
        </form>
      </section>

      <div className="overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-sm">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-xs font-semibold uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-4 py-3">Section</th>
              <th className="px-4 py-3">Description</th>
              <th className="px-4 py-3">Key concepts</th>
              <th className="px-4 py-3 text-right">Next step</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {areasQuery.isLoading ? (
              <tr>
                <td colSpan={4} className="px-4 py-6 text-center text-sm text-slate-500">
                  Loading domain map…
                </td>
              </tr>
            ) : areasQuery.isError ? (
              <tr>
                <td colSpan={4} className="px-4 py-6 text-center text-sm text-rose-700">
                  {(areasQuery.error as Error).message}
                </td>
              </tr>
            ) : areas.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-4 py-6 text-center text-sm text-slate-500">
                  No domain map yet. Suggest one with AI above, or create a section manually.
                </td>
              </tr>
            ) : (
              areas.map((area) =>
                editingId === area.id ? (
                  <tr key={area.id} className="bg-slate-50/60">
                    <td colSpan={4} className="px-4 py-4">
                      <form onSubmit={handleSaveEdit} className="grid gap-3 md:grid-cols-2">
                        <input
                          value={editForm.label}
                          onChange={(event) => setEditForm((s) => ({ ...s, label: event.target.value }))}
                          className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                        />
                        <input
                          value={editForm.keyConcepts}
                          onChange={(event) =>
                            setEditForm((s) => ({ ...s, keyConcepts: event.target.value }))
                          }
                          placeholder="Key concepts (comma separated)"
                          className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                        />
                        <textarea
                          value={editForm.description}
                          onChange={(event) =>
                            setEditForm((s) => ({ ...s, description: event.target.value }))
                          }
                          rows={2}
                          className="md:col-span-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                        />
                        {editError ? (
                          <p className="md:col-span-2 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-900">
                            {editError}
                          </p>
                        ) : null}
                        <div className="md:col-span-2 flex flex-wrap justify-end gap-2">
                          <button
                            type="button"
                            onClick={() => {
                              setEditingId(null)
                              setEditError(null)
                            }}
                            className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700"
                          >
                            Cancel
                          </button>
                          <button
                            type="submit"
                            disabled={updateMutation.isPending}
                            className="rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white shadow-sm disabled:opacity-60"
                          >
                            {updateMutation.isPending ? 'Saving…' : 'Save changes'}
                          </button>
                        </div>
                      </form>
                    </td>
                  </tr>
                ) : (
                  <tr key={area.id} className="hover:bg-slate-50/80 align-top">
                    <td className="px-4 py-4 font-medium text-slate-900">{area.label}</td>
                    <td className="max-w-md px-4 py-4 text-slate-600">{area.description}</td>
                    <td className="px-4 py-4">
                      <div className="flex flex-wrap gap-1">
                        {area.key_concepts.map((c) => (
                          <span
                            key={c}
                            className="rounded-md bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700"
                          >
                            {c}
                          </span>
                        ))}
                        {area.key_concepts.length === 0 ? (
                          <span className="text-xs italic text-slate-400">no concepts</span>
                        ) : null}
                      </div>
                    </td>
                    <td className="px-4 py-4 text-right">
                      <div className="inline-flex items-center gap-2">
                        <button
                          type="button"
                          onClick={() => handleStartEdit(area)}
                          className="whitespace-nowrap rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50"
                        >
                          Edit
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDelete(area)}
                          disabled={deleteMutation.isPending && deleteMutation.variables === area.id}
                          className="whitespace-nowrap rounded-lg border border-rose-200 bg-white px-3 py-2 text-xs font-medium text-rose-700 hover:bg-rose-50 disabled:opacity-60"
                        >
                          Delete
                        </button>
                        <Link
                          to="/iterations-v2"
                          search={{ projectId, domainId: area.id }}
                          className="inline-flex whitespace-nowrap rounded-lg bg-emerald-600 px-3 py-2 text-xs font-semibold text-white shadow-sm hover:bg-emerald-700"
                        >
                          Explore next directions
                        </Link>
                      </div>
                    </td>
                  </tr>
                ),
              )
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function splitConcepts(raw: string): string[] {
  return raw
    .split(',')
    .map((entry) => entry.trim())
    .filter(Boolean)
}

function toErrorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message
  if (error instanceof Error) return error.message
  return 'Request failed.'
}
