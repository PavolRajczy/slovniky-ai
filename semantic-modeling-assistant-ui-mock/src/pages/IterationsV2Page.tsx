import { Link, getRouteApi } from '@tanstack/react-router'
import { useMemo, useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  WorkflowStepper,
  resolveWorkflowContext,
} from '@/components/workflow'
import { ActivitySummary } from '@/components/ActivitySummary'
import { ApiError } from '@/api/client'
import { listDomainAreas } from '@/api/domainAreas'
import {
  createIteration,
  listIterations,
  suggestIterations,
} from '@/api/iterations'
import type {
  DesignIterationModel,
  KnowledgeDomainAreaModel,
} from '@/api/types'

const iterationsV2RouteApi = getRouteApi('/iterations-v2')

type SuggestFormState = {
  goal: string
  classUris: string
  count: number
}

type ManualFormState = {
  name: string
  specification: string
  focusedAreaId: string
}

const INITIAL_MANUAL: ManualFormState = { name: '', specification: '', focusedAreaId: '' }

export function IterationsV2Page() {
  const { projectId, domainId } = iterationsV2RouteApi.useSearch()
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

  const [suggestForm, setSuggestForm] = useState<SuggestFormState>({
    goal: '',
    classUris: '',
    count: 3,
  })
  const [suggestError, setSuggestError] = useState<string | null>(null)
  const [manualForm, setManualForm] = useState<ManualFormState>(INITIAL_MANUAL)
  const [manualError, setManualError] = useState<string | null>(null)

  const currentDomain = useMemo(
    () => (domainId ? areas.find((area) => area.id === domainId) : undefined) ?? areas[0],
    [areas, domainId],
  )
  const effectiveAreaId = currentDomain?.id ?? ''
  const effectiveManualAreaId = manualForm.focusedAreaId || domainId || areas[0]?.id || ''

  const planned = iterationsQuery.data?.planned_iterations ?? []
  const ready = iterationsQuery.data?.current_iteration ? [iterationsQuery.data.current_iteration] : []
  const completed = iterationsQuery.data?.finished_iterations ?? []
  const domainProgress = estimateDomainProgress({
    plannedCount: planned.length,
    readyCount: ready.length,
    completedCount: completed.length,
  })

  const invalidate = async () => {
    if (!projectId) return
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ['project-iterations', projectId] }),
      queryClient.invalidateQueries({ queryKey: ['project', projectId] }),
      queryClient.invalidateQueries({ queryKey: ['project-activity', projectId] }),
    ])
  }

  const suggestMutation = useMutation({
    mutationFn: () =>
      suggestIterations(projectId!, {
        focused_area_id: effectiveAreaId,
        count: suggestForm.count,
        user_instruction: composeDirectionInstruction(suggestForm) || null,
      }),
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

  const handleSuggest = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!effectiveAreaId) {
      setSuggestError('Pick a domain area first.')
      return
    }
    if (suggestForm.count < 1 || suggestForm.count > 10) {
      setSuggestError('Number of suggestions must be between 1 and 10.')
      return
    }
    suggestMutation.mutate()
  }

  const handleCreate = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const focusedAreaId = manualForm.focusedAreaId || effectiveManualAreaId
    if (!manualForm.name.trim() || !manualForm.specification.trim()) {
      setManualError('Name and description are required.')
      return
    }
    if (!focusedAreaId) {
      setManualError('Pick a domain area for this direction.')
      return
    }
    createMutation.mutate({ ...manualForm, focusedAreaId })
  }

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

  return (
    <div className="mx-auto max-w-6xl space-y-8">
      <WorkflowStepper activeStep="iterations" linkContext={linkContext} />
      <ActivitySummary projectId={projectId} />
      <DomainFeedbackPanel
        domain={currentDomain}
        progress={domainProgress}
        projectId={projectId}
      />

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_22rem]">
        <section className="rounded-2xl border border-emerald-200 bg-linear-to-br from-emerald-50 to-white p-6 shadow-sm">
          <p className="text-xs font-semibold uppercase tracking-wide text-emerald-800">
            Iterations v2 concept
          </p>
          <h2 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">
            What should we explore next?
          </h2>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-700">
            This page treats iterations as direction suggestions, not as a fixed plan. Ask the assistant for
            the next promising work in a domain, review the proposed changes, and return here whenever the
            ontology still needs another pass.
          </p>
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-5 text-sm shadow-sm">
          <h3 className="font-semibold text-slate-900">How this flow should feel</h3>
          <ol className="mt-3 space-y-3 text-slate-600">
            <li>
              <span className="font-medium text-slate-900">1. Choose a direction.</span> Say what part of the
              domain deserves attention now.
            </li>
            <li>
              <span className="font-medium text-slate-900">2. Work through it.</span> Turn one suggestion into
              tasks and review the resulting changes.
            </li>
            <li>
              <span className="font-medium text-slate-900">3. Come back for more.</span> If review reveals more
              work, ask for another set of directions.
            </li>
          </ol>
        </section>
      </div>

      <section className="rounded-2xl border border-slate-200/80 bg-white shadow-sm">
        <form onSubmit={handleSuggest} className="p-5 sm:p-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
                Ask for next directions
              </h3>
              <p className="mt-1 text-sm text-slate-600">
                Keep this simple: describe what you want to improve or understand in the current domain.
              </p>
            </div>
            {iterationsQuery.isFetching ? (
              <span className="text-xs text-slate-500">refreshing...</span>
            ) : null}
          </div>

          <div className="mt-5 grid gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-700" htmlFor="v2-goal">
                What should the assistant focus on?
              </label>
              <textarea
                id="v2-goal"
                rows={3}
                value={suggestForm.goal}
                onChange={(event) => setSuggestForm((state) => ({ ...state, goal: event.target.value }))}
                placeholder="For example: check whether important concepts are missing, or suggest what should be modeled after the last review."
                className="mt-1 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
              />
            </div>
          </div>

          <details className="mt-5 rounded-xl border border-slate-200 bg-slate-50/70">
            <summary className="flex cursor-pointer list-none items-center justify-between gap-3 px-4 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500 [&::-webkit-details-marker]:hidden">
              Advanced suggestion settings
              <span className="normal-case tracking-normal text-slate-400">optional</span>
            </summary>
            <div className="border-t border-slate-200 px-4 pb-4 pt-3">
              <p className="text-xs text-slate-600">
                Use this only when you already know how many suggestions you want or which ontology classes
                should constrain the next direction.
              </p>
              <div className="mt-3 grid gap-4 md:grid-cols-[12rem_1fr]">
                <div>
                  <label className="block text-xs font-medium text-slate-700" htmlFor="v2-count">
                    Number of suggestions
                  </label>
                  <input
                    id="v2-count"
                    type="number"
                    min={1}
                    max={10}
                    value={suggestForm.count}
                    onChange={(event) =>
                      setSuggestForm((state) => ({ ...state, count: Number(event.target.value) || 1 }))
                    }
                    className="mt-1 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-700" htmlFor="v2-class-uris">
                    Limit to class URIs
                  </label>
                  <textarea
                    id="v2-class-uris"
                    rows={3}
                    value={suggestForm.classUris}
                    onChange={(event) =>
                      setSuggestForm((state) => ({ ...state, classUris: event.target.value }))
                    }
                    placeholder={'https://example.org/ontology#Vehicle\nhttps://example.org/ontology#Registration'}
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

          <div className="mt-5 flex flex-wrap items-center gap-3">
            <button
              type="submit"
              disabled={suggestMutation.isPending || areas.length === 0}
              className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-60"
            >
              {suggestMutation.isPending ? 'Thinking...' : 'Suggest next directions'}
            </button>
            {suggestMutation.isSuccess && suggestMutation.data ? (
              <span className="text-xs text-emerald-700">
                Added {suggestMutation.data.length} direction
                {suggestMutation.data.length === 1 ? '' : 's'}. You can ask again after review.
              </span>
            ) : null}
          </div>
        </form>
      </section>

      <section className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_22rem]">
        <DirectionColumn
          title="Possible next directions"
          description="Suggestions waiting for you to choose one and turn it into tasks."
          items={planned}
          areas={areas}
          projectId={projectId}
          emptyMessage="No directions yet. Ask the assistant above for the next useful work in this domain."
        />

        <div className="space-y-4">
          <DirectionColumn
            title="Being worked on"
            description="The current direction already has tasks or prepared changes."
            items={ready}
            areas={areas}
            projectId={projectId}
            emptyMessage="Nothing is being worked on right now."
            compact
          />
          <DirectionColumn
            title="Already reviewed"
            description="Finished directions can reveal what to ask for next."
            items={completed}
            areas={areas}
            projectId={projectId}
            emptyMessage="No reviewed directions yet."
            compact
          />
        </div>
      </section>

      <section className="rounded-2xl border border-dashed border-slate-300 bg-white p-5 shadow-sm">
        <details className="group [&_summary::-webkit-details-marker]:hidden">
          <summary className="flex cursor-pointer list-none items-center justify-between gap-3">
            <div>
              <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
                Advanced: create a direction manually
              </h3>
              <p className="mt-1 text-xs text-slate-600">
                Use this when you already know the exact next direction and do not need AI suggestions.
              </p>
            </div>
            <span className="text-slate-400 transition-transform duration-200 group-open:rotate-180" aria-hidden>
              v
            </span>
          </summary>
          <form onSubmit={handleCreate} className="mt-4 border-t border-slate-100 pt-4">
            <div className="grid gap-3 md:grid-cols-2">
              <input
                value={manualForm.name}
                onChange={(event) => setManualForm((state) => ({ ...state, name: event.target.value }))}
                placeholder="Direction name"
                className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
              />
              <select
                value={manualForm.focusedAreaId || effectiveManualAreaId}
                onChange={(event) =>
                  setManualForm((state) => ({ ...state, focusedAreaId: event.target.value }))
                }
                className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
              >
                <option value="">Pick a domain area</option>
                {areas.map((area) => (
                  <option key={area.id} value={area.id}>
                    {area.label}
                  </option>
                ))}
              </select>
              <textarea
                value={manualForm.specification}
                onChange={(event) =>
                  setManualForm((state) => ({ ...state, specification: event.target.value }))
                }
                rows={2}
                placeholder="Describe why this direction is useful and what should be explored."
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
                {createMutation.isPending ? 'Saving...' : 'Save manual direction'}
              </button>
            </div>
          </form>
        </details>
      </section>
    </div>
  )
}

type DirectionColumnProps = {
  title: string
  description: string
  items: DesignIterationModel[]
  areas: KnowledgeDomainAreaModel[]
  projectId: string
  emptyMessage: string
  compact?: boolean
}

type DomainProgressEstimate = {
  percent: number
  confidence: string
  rationale: string
}

type DomainFeedbackPanelProps = {
  domain: KnowledgeDomainAreaModel | undefined
  progress: DomainProgressEstimate
  projectId: string
}

function DomainFeedbackPanel({ domain, progress, projectId }: DomainFeedbackPanelProps) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Current domain</p>
          <h2 className="mt-1 text-xl font-semibold tracking-tight text-slate-950">
            {domain?.label ?? 'No domain selected'}
          </h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
            {domain?.description ??
              'Open a domain area first so the assistant can suggest where to continue.'}
          </p>
          {domain && domain.key_concepts.length > 0 ? (
            <div className="mt-3 flex flex-wrap gap-1">
              {domain.key_concepts.map((concept) => (
                <span
                  key={concept}
                  className="rounded-md bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700"
                >
                  {concept}
                </span>
              ))}
            </div>
          ) : null}
        </div>

        <div className="w-full rounded-xl border border-emerald-200 bg-emerald-50/70 p-4 sm:w-80">
          <div className="flex items-center justify-between gap-3">
            <p className="text-xs font-semibold uppercase tracking-wide text-emerald-800">
              AI progress estimate
            </p>
            <span className="rounded-full bg-white px-2 py-0.5 text-xs font-semibold text-emerald-900">
              {progress.percent}%
            </span>
          </div>
          <div className="mt-3 h-2 overflow-hidden rounded-full bg-white">
            <div
              className="h-full rounded-full bg-emerald-600"
              style={{ width: `${progress.percent}%` }}
            />
          </div>
          <p className="mt-2 text-xs leading-5 text-emerald-950">{progress.rationale}</p>
          <p className="mt-1 text-[11px] text-emerald-900/80">
            Confidence: {progress.confidence}. This is feedback for choosing the next direction, not a final
            completion score.
          </p>
        </div>
      </div>

      <div className="mt-4 flex justify-end">
        <Link
          to="/domain-areas"
          search={{ projectId }}
          className="text-xs font-medium text-emerald-700 hover:underline"
        >
          Choose a different domain
        </Link>
      </div>
    </section>
  )
}

function DirectionColumn({
  title,
  description,
  items,
  areas,
  projectId,
  emptyMessage,
  compact = false,
}: DirectionColumnProps) {
  return (
    <section className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm">
      <div>
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">{title}</h3>
        <p className="mt-1 text-xs text-slate-600">{description}</p>
      </div>

      {items.length === 0 ? (
        <p className="mt-4 rounded-xl border border-dashed border-slate-200 bg-slate-50 px-4 py-5 text-center text-sm text-slate-500">
          {emptyMessage}
        </p>
      ) : (
        <div className={compact ? 'mt-4 space-y-3' : 'mt-4 grid gap-4 md:grid-cols-2'}>
          {items.map((item) => {
            const area = areas.find((candidate) => candidate.id === item.focused_area_id)
            return (
              <article
                key={item.id}
                className="flex h-full flex-col rounded-xl border border-slate-200 bg-slate-50/50 p-4"
              >
                <p className="text-sm font-semibold text-slate-900">{item.name}</p>
                <p className="mt-1 text-xs text-slate-500">{area?.label ?? item.focused_area_id}</p>
                <p className="mt-3 text-sm text-slate-700 line-clamp-4">{item.specification}</p>
                <div className="mt-auto pt-4">
                  <Link
                    to="/tasks"
                    search={{
                      projectId,
                      domainId: item.focused_area_id,
                      iterationId: item.id,
                      taskId: undefined,
                    }}
                    className="inline-flex rounded-md bg-slate-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-slate-800"
                  >
                    Explore this direction
                  </Link>
                </div>
              </article>
            )
          })}
        </div>
      )}
    </section>
  )
}

function estimateDomainProgress(input: {
  plannedCount: number
  readyCount: number
  completedCount: number
}): DomainProgressEstimate {
  const totalKnownDirections = input.plannedCount + input.readyCount + input.completedCount
  const percent = Math.min(
    92,
    25 + input.completedCount * 18 + input.readyCount * 12 + input.plannedCount * 5,
  )

  if (totalKnownDirections === 0) {
    return {
      percent: 25,
      confidence: 'low',
      rationale: 'The assistant has not proposed directions for this domain yet.',
    }
  }

  if (input.completedCount === 0) {
    return {
      percent,
      confidence: 'medium',
      rationale: 'There are directions to explore, but none have been reviewed end-to-end yet.',
    }
  }

  return {
    percent,
    confidence: input.readyCount > 0 || input.plannedCount > 0 ? 'medium' : 'high',
    rationale: 'Reviewed work gives the assistant a better sense of what remains in this domain.',
  }
}

function composeDirectionInstruction(form: SuggestFormState): string {
  const lines: string[] = []
  const goal = form.goal.trim()
  const classUris = form.classUris
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)

  if (goal) {
    lines.push(`Goal: ${goal}`)
  }
  if (classUris.length > 0) {
    lines.push('Restrict next direction suggestions to these classes:')
    for (const uri of classUris) {
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
