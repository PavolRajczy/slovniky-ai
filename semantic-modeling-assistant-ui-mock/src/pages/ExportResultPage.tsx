import { Link, getRouteApi } from '@tanstack/react-router'
import { useEffect, useMemo, useRef, useState, type FormEvent } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { resolveWorkflowContext } from '@/components/workflow'
import { PageBackLink } from '@/components/PageBackLink'
import { ActivitySummary } from '@/components/ActivitySummary'
import {
  OfnConceptStats,
  OfnExportPanel,
  countOfnConcepts,
  type OfnConceptCounts,
} from '@/components/OfnExportPanel'
import { ApiError } from '@/api/client'
import { getDataspecerExportUrl, getProject, getProjectOfn } from '@/api/projects'
import { listIterations } from '@/api/iterations'
import { exportOntologyToDataspecer, getOntology } from '@/api/ontologies'

const exportRouteApi = getRouteApi('/export-result')

const putUrlStorageKey = (projectId: string) => `dataspecer-put-url:${projectId}`

export function ExportResultPage() {
  const search = exportRouteApi.useSearch()
  const linkContext = resolveWorkflowContext({
    projectId: search.projectId,
    domainId: search.domainId,
    iterationId: search.iterationId,
    taskId: search.taskId,
  })
  const projectId = search.projectId
  const iterationId = search.iterationId

  const projectQuery = useQuery({
    queryKey: ['project', projectId],
    queryFn: ({ signal }) => getProject(projectId!, signal),
    enabled: Boolean(projectId),
  })

  const ontologyUri = projectQuery.data?.ontology_uri

  const ontologyQuery = useQuery({
    queryKey: ['ontology', ontologyUri],
    queryFn: ({ signal }) => getOntology(ontologyUri!, signal),
    enabled: Boolean(ontologyUri),
  })

  const ofnQuery = useQuery({
    queryKey: ['project-ofn', projectId],
    queryFn: ({ signal }) => getProjectOfn(projectId!, signal),
    enabled: Boolean(projectId),
    retry: false,
  })

  const iterationsQuery = useQuery({
    queryKey: ['project-iterations', projectId, 'all'],
    queryFn: ({ signal }) => listIterations(projectId!, {}, signal),
    enabled: Boolean(projectId),
  })

  const finishedIteration = useMemo(
    () => iterationsQuery.data?.finished_iterations.find((it) => it.id === iterationId),
    [iterationsQuery.data, iterationId],
  )

  const [putUrl, setPutUrl] = useState('')
  const [putUrlTouched, setPutUrlTouched] = useState(false)
  const [exportError, setExportError] = useState<string | null>(null)
  const [linkedExportUrl, setLinkedExportUrl] = useState<string | null>(null)
  const [dataspecerOpen, setDataspecerOpen] = useState(false)
  const autoExportStarted = useRef(false)

  const linkedToDataspecer = Boolean(projectQuery.data?.dataspecer_package_iri)

  useEffect(() => {
    if (!projectId || putUrlTouched) {
      return
    }
    try {
      const stored = window.localStorage.getItem(putUrlStorageKey(projectId))
      if (stored && stored.length > 0) {
        setPutUrl(stored)
        return
      }
    } catch {
      // localStorage may be unavailable; safe to ignore.
    }
    if (!linkedToDataspecer) {
      return
    }
    let cancelled = false
    getDataspecerExportUrl(projectId)
      .then((result) => {
        if (cancelled) {
          return
        }
        setLinkedExportUrl(result.put_url)
        setPutUrl(result.put_url)
      })
      .catch((error: unknown) => {
        if (cancelled) {
          return
        }
        if (error instanceof ApiError) setExportError(error.message)
        else if (error instanceof Error) setExportError(error.message)
        else setExportError('Could not resolve the local Dataspecer export URL.')
      })
    return () => {
      cancelled = true
    }
  }, [projectId, putUrlTouched, linkedToDataspecer])

  const exportMutation = useMutation({
    mutationFn: () =>
      exportOntologyToDataspecer({
        ontology_uri: ontologyUri!,
        put_url: putUrl.trim(),
      }),
    onSuccess: () => {
      setExportError(null)
      if (projectId) {
        try {
          window.localStorage.setItem(putUrlStorageKey(projectId), putUrl.trim())
        } catch {
          // localStorage may be unavailable; the export still succeeded.
        }
      }
    },
    onError: (error: unknown) => {
      if (error instanceof ApiError) setExportError(error.message)
      else if (error instanceof Error) setExportError(error.message)
      else setExportError('Export failed.')
    },
  })

  useEffect(() => {
    if (!linkedExportUrl || !ontologyUri || putUrl !== linkedExportUrl || autoExportStarted.current) {
      return
    }
    autoExportStarted.current = true
    exportMutation.mutate()
  }, [linkedExportUrl, ontologyUri, putUrl, exportMutation])

  const conceptCounts = useMemo<OfnConceptCounts>(() => {
    if (ofnQuery.data) {
      return countOfnConcepts(ofnQuery.data.pojmy ?? [])
    }
    const o = ontologyQuery.data
    const classes = o?.classes.length ?? 0
    const relations = o?.relationships.length ?? 0
    const properties = o?.attributes.length ?? 0
    return { total: classes + relations + properties, classes, relations, properties }
  }, [ofnQuery.data, ontologyQuery.data])

  const directionsSearch = {
    projectId,
    domainId: linkContext.domainId,
  }

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!ontologyUri) {
      setExportError('Project ontology not loaded yet.')
      return
    }
    if (!putUrl.trim()) {
      setExportError('Provide a Dataspecer export URL.')
      return
    }
    exportMutation.mutate()
  }

  if (!projectId) {
    return (
      <div className="mx-auto max-w-3xl space-y-4">
        <div className="rounded-2xl border border-amber-200 bg-amber-50 p-6 text-sm text-amber-900">
          No project selected. Pick or create a project on the{' '}
          <Link to="/project" search={{ projectId: undefined, packageIri: undefined }} className="font-medium underline">
            project setup
          </Link>{' '}
          page first.
        </div>
      </div>
    )
  }

  const exportSucceeded = exportMutation.isSuccess
  const exportPending = exportMutation.isPending
  const dataspecerStatus = exportPending
    ? 'Exporting to Dataspecer…'
    : exportSucceeded
      ? 'Exported to Dataspecer.'
      : exportError
        ? 'Dataspecer export failed.'
        : 'Not exported to Dataspecer yet.'

  return (
    <div className="mx-auto max-w-5xl space-y-6">
      <PageBackLink to="/iterations-v2" search={directionsSearch} label="directions" />

      <section className="rounded-2xl border border-emerald-200 bg-emerald-50/70 p-6 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-wide text-emerald-800">
          {finishedIteration ? 'Direction completed' : 'Project result'}
        </p>
        <h2 className="mt-1 text-2xl font-semibold tracking-tight text-emerald-950">
          {finishedIteration?.name ?? projectQuery.data?.name ?? 'Designed ontology'}
        </h2>
        {finishedIteration ? (
          <p className="mt-1 text-sm text-emerald-900/90">
            {finishedIteration.finished_tasks_count} work item
            {finishedIteration.finished_tasks_count === 1 ? '' : 's'} applied to the ontology.
          </p>
        ) : null}
        {ontologyUri ? (
          <p className="mt-1 truncate font-mono text-[11px] text-emerald-900/70" title={ontologyUri}>
            {ontologyUri}
          </p>
        ) : null}

        <div className="mt-4">
          {ofnQuery.isLoading || ontologyQuery.isLoading ? (
            <p className="text-sm text-slate-600">Loading ontology…</p>
          ) : (
            <OfnConceptStats counts={conceptCounts} />
          )}
        </div>

        <div className="mt-4">
          <ActivitySummary projectId={projectId} iterationId={iterationId} />
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          <Link
            to="/iterations-v2"
            search={directionsSearch}
            className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
          >
            Back to directions
          </Link>
          <Link
            to="/guidance"
            search={{ projectId }}
            className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Open guidance
          </Link>
        </div>
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Dataspecer export</p>
            <p
              className={`mt-1 text-sm ${
                exportError && !exportPending
                  ? 'text-rose-700'
                  : exportSucceeded
                    ? 'text-emerald-800'
                    : 'text-slate-600'
              }`}
            >
              {dataspecerStatus}
            </p>
          </div>
          <button
            type="button"
            onClick={() => setDataspecerOpen((open) => !open)}
            className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            {dataspecerOpen ? 'Hide' : 'Show export'}
          </button>
        </div>

        {dataspecerOpen ? (
          <form className="mt-4 space-y-3" onSubmit={handleSubmit}>
            <p className="text-sm text-slate-600">
              Approved changes are part of the designed ontology. Finalize already regenerates project OFN;
              Dataspecer export is optional.
            </p>
            <div>
              <label className="block text-xs font-medium uppercase tracking-wide text-slate-600">
                Dataspecer export URL
              </label>
              <input
                type="url"
                value={putUrl}
                onChange={(event) => {
                  setPutUrl(event.target.value)
                  setPutUrlTouched(true)
                }}
                placeholder="https://tool.dataspecer.com/api/simplified-semantic-model?iri=..."
                className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 font-mono text-xs text-slate-800 shadow-sm focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/30"
                disabled={exportPending}
              />
              <p className="mt-1 text-[11px] text-slate-500">
                {linkedToDataspecer
                  ? 'Filled from the linked local Dataspecer vocabulary. Export runs on its own when this page opens.'
                  : 'Same URL convention as the import step (GET fetches, PUT replaces). The last value is remembered per project on this device.'}
              </p>
            </div>

            {exportError ? (
              <p className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-900">
                {exportError}
              </p>
            ) : null}

            <div className="flex flex-wrap gap-2">
              <button
                type="submit"
                disabled={exportPending || !ontologyUri || putUrl.trim().length === 0}
                className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-emerald-700 disabled:opacity-60"
              >
                {exportPending
                  ? 'Exporting…'
                  : exportSucceeded
                    ? 'Re-export to Dataspecer'
                    : 'Export to Dataspecer'}
              </button>
            </div>
          </form>
        ) : null}
      </section>

      <OfnExportPanel
        projectId={projectId}
        projectName={projectQuery.data?.name}
        showStats={false}
        defaultExpanded={false}
      />
    </div>
  )
}
