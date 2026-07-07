import { Link, getRouteApi } from '@tanstack/react-router'
import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { WorkflowStepper, resolveWorkflowContext } from '@/components/workflow'
import { ApiError } from '@/api/client'
import { getProject } from '@/api/projects'
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

  const [putUrl, setPutUrl] = useState('')
  const [putUrlTouched, setPutUrlTouched] = useState(false)
  const [exportError, setExportError] = useState<string | null>(null)

  useEffect(() => {
    if (!projectId || putUrlTouched) {
      return
    }
    try {
      const stored = window.localStorage.getItem(putUrlStorageKey(projectId))
      if (stored && stored.length > 0) {
        setPutUrl(stored)
      }
    } catch {
      // localStorage may be unavailable; safe to ignore.
    }
  }, [projectId, putUrlTouched])

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

  const counts = useMemo(() => {
    const o = ontologyQuery.data
    return {
      classes: o?.classes.length ?? 0,
      attributes: o?.attributes.length ?? 0,
      relationships: o?.relationships.length ?? 0,
    }
  }, [ontologyQuery.data])

  const recap = {
    approved: search.approved ?? 0,
    pending: search.pending ?? 0,
    rejected: search.rejected ?? 0,
    regenerated: search.regenerated ?? 0,
    guidanceUpdated: search.guidanceUpdated ?? false,
    taskId: search.taskId,
  }

  const exportSearch = {
    domainId: linkContext.domainId,
    iterationId: linkContext.iterationId,
    taskId: linkContext.taskId,
    approved: recap.approved,
    pending: recap.pending,
    rejected: recap.rejected,
    regenerated: recap.regenerated,
    guidanceUpdated: recap.guidanceUpdated,
  }

  const operationsSearch = {
    projectId,
    domainId: linkContext.domainId,
    iterationId: linkContext.iterationId,
    taskId: linkContext.taskId,
  }

  const iterationsSearch = {
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
        <WorkflowStepper activeStep="export" linkContext={linkContext} />
        <div className="rounded-2xl border border-amber-200 bg-amber-50 p-6 text-sm text-amber-900">
          No project selected. Pick or create a project on the{' '}
          <Link to="/project" search={{ projectId: undefined }} className="font-medium underline">
            project setup
          </Link>{' '}
          page first.
        </div>
      </div>
    )
  }

  const exportSucceeded = exportMutation.isSuccess
  const exportPending = exportMutation.isPending

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <WorkflowStepper activeStep="export" exportSearch={exportSearch} linkContext={linkContext} />

      <section
        className={`rounded-2xl border p-6 shadow-sm ${
          exportSucceeded
            ? 'border-emerald-200 bg-emerald-50/70'
            : 'border-slate-200 bg-white'
        }`}
      >
        <h2
          className={`text-2xl font-semibold tracking-tight ${
            exportSucceeded ? 'text-emerald-900' : 'text-slate-900'
          }`}
        >
          {exportSucceeded ? 'Export completed' : 'Approved changes applied - ready to export'}
        </h2>
        <p className={`mt-2 text-sm ${exportSucceeded ? 'text-emerald-900/90' : 'text-slate-600'}`}>
          {exportSucceeded
            ? 'The designed ontology was pushed to Dataspecer.'
            : 'Approved changes are now part of the designed ontology. Push it back to Dataspecer to update the public specification.'}
        </p>

        <form className="mt-4 space-y-3" onSubmit={handleSubmit}>
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
              Same URL convention as the import step (GET fetches, PUT replaces). The last value is
              remembered per project on this device.
            </p>
          </div>

          {exportError ? (
            <p className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-900">
              {exportError}
            </p>
          ) : null}
          {exportSucceeded ? (
            <p className="rounded-lg border border-emerald-200 bg-white px-3 py-2 text-sm text-emerald-900">
              Last export succeeded. You can re-run it any time after the next iteration.
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
            <Link
              to="/operations"
              search={operationsSearch}
              className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Back to review changes
            </Link>
          </div>
        </form>
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Ontology snapshot</h3>
        {projectQuery.isLoading || ontologyQuery.isLoading ? (
          <p className="mt-2 text-sm text-slate-600">Loading ontology…</p>
        ) : projectQuery.isError ? (
          <p className="mt-2 text-sm text-rose-700">
            Failed to load project: {(projectQuery.error as Error).message}
          </p>
        ) : ontologyQuery.isError ? (
          <p className="mt-2 text-sm text-rose-700">
            Failed to load ontology: {(ontologyQuery.error as Error).message}
          </p>
        ) : (
          <>
            <p className="mt-2 text-sm text-slate-600">Live counts read from the backend store.</p>
            <ul className="mt-4 space-y-2 text-sm text-slate-800">
              <li className="flex justify-between gap-4 border-b border-slate-100 pb-2">
                <span className="text-slate-600">Project</span>
                <span className="max-w-[55%] text-right font-semibold text-slate-900">
                  {projectQuery.data?.name ?? '—'}
                </span>
              </li>
              <li className="flex justify-between gap-4 border-b border-slate-100 pb-2">
                <span className="text-slate-600">Ontology IRI</span>
                <span className="max-w-[60%] truncate text-right font-mono text-xs text-slate-700">
                  {ontologyUri}
                </span>
              </li>
              <li className="flex justify-between gap-4 border-b border-slate-100 pb-2">
                <span className="text-slate-600">Classes</span>
                <span className="font-semibold tabular-nums">{counts.classes}</span>
              </li>
              <li className="flex justify-between gap-4 border-b border-slate-100 pb-2">
                <span className="text-slate-600">Attributes</span>
                <span className="font-semibold tabular-nums">{counts.attributes}</span>
              </li>
              <li className="flex justify-between gap-4 pt-1">
                <span className="text-slate-600">Relationships</span>
                <span className="font-semibold tabular-nums">{counts.relationships}</span>
              </li>
            </ul>
          </>
        )}
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Session recap</h3>
        <p className="mt-2 text-sm text-slate-600">
          Snapshot of the review state passed from review changes via URL search params.
        </p>
        <ul className="mt-4 space-y-2 text-sm text-slate-800">
          {recap.taskId ? (
            <li className="flex justify-between gap-4 border-b border-slate-100 pb-2">
              <span className="text-slate-600">Task</span>
              <span className="max-w-[60%] truncate text-right font-mono text-xs text-slate-700">
                {recap.taskId}
              </span>
            </li>
          ) : null}
          <li className="flex justify-between gap-4 border-b border-slate-100 pb-2">
            <span className="text-slate-600">Changes approved</span>
            <span className="font-semibold tabular-nums">{recap.approved}</span>
          </li>
          <li className="flex justify-between gap-4 border-b border-slate-100 pb-2">
            <span className="text-slate-600">Still pending review</span>
            <span className="font-semibold tabular-nums">{recap.pending}</span>
          </li>
          <li className="flex justify-between gap-4 border-b border-slate-100 pb-2">
            <span className="text-slate-600">Rejected</span>
            <span className="font-semibold tabular-nums">{recap.rejected}</span>
          </li>
          <li className="flex justify-between gap-4 pt-1">
            <span className="text-slate-600">Guidance updated this session</span>
            <span className="font-semibold">{recap.guidanceUpdated ? 'Yes' : 'No'}</span>
          </li>
        </ul>
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Next steps</h3>
        <div className="mt-4 flex flex-wrap gap-2">
          <Link
            to="/iterations"
            search={iterationsSearch}
            className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
          >
            Start next iteration
          </Link>
          <Link
            to="/guidance"
            search={{ projectId }}
            className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Open guidance
          </Link>
          <Link
            to="/operations"
            search={operationsSearch}
            className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Back to review changes
          </Link>
        </div>
      </section>
    </div>
  )
}
