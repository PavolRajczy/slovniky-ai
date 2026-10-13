import { Link, getRouteApi } from '@tanstack/react-router'
import { useEffect, useMemo, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { getProject, openProjectFromDataspecer } from '@/api/projects'
import { ApiError } from '@/api/client'
import { useCurrentProject } from '@/hooks/useCurrentProject'
import { KnowledgeBaseSection } from '@/components/KnowledgeBaseSection'

const projectRouteApi = getRouteApi('/project')

export function ProjectSetupPage() {
  const { projectId, setProjectId } = useCurrentProject()
  const { packageIri } = projectRouteApi.useSearch()
  const queryClient = useQueryClient()
  const [dataspecerError, setDataspecerError] = useState<string | null>(null)
  const [openingDataspecer, setOpeningDataspecer] = useState(false)

  useEffect(() => {
    if (!packageIri) {
      return
    }
    let cancelled = false
    setDataspecerError(null)
    setOpeningDataspecer(true)
    openProjectFromDataspecer(packageIri)
      .then(async (project) => {
        if (cancelled) {
          return
        }
        await queryClient.invalidateQueries({ queryKey: ['projects'] })
        setProjectId(project.id)
      })
      .catch((error: unknown) => {
        if (cancelled) {
          return
        }
        if (error instanceof ApiError) {
          setDataspecerError(error.message)
        } else if (error instanceof Error) {
          setDataspecerError(error.message)
        } else {
          setDataspecerError('Could not open the Dataspecer vocabulary.')
        }
      })
      .finally(() => {
        if (!cancelled) {
          setOpeningDataspecer(false)
        }
      })
    return () => {
      cancelled = true
    }
  }, [packageIri, queryClient, setProjectId])

  const currentProjectQuery = useQuery({
    queryKey: ['project', projectId],
    queryFn: ({ signal }) => getProject(projectId!, signal),
    enabled: Boolean(projectId),
  })

  const ontologySummary = useMemo(() => {
    const project = currentProjectQuery.data
    if (!project) {
      return null
    }
    const areas = project.domain_areas.length
    const iterations =
      project.planned_iterations.length +
      project.finished_iterations.length +
      (project.current_iteration ? 1 : 0)
    return { areas, iterations }
  }, [currentProjectQuery.data])

  return (
    <div className="mx-auto max-w-4xl space-y-8">
      <div>
        <h2 className="text-2xl font-semibold tracking-tight text-slate-900">Project &amp; knowledge base</h2>
        <p className="mt-1 text-sm text-slate-600">
          Attach the legal and expert documents that will fuel the assistant.
        </p>
        {openingDataspecer ? (
          <p className="mt-3 text-sm text-slate-600">Opening the Dataspecer vocabulary…</p>
        ) : null}
        {dataspecerError ? (
          <p className="mt-3 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-900">
            {dataspecerError}
          </p>
        ) : null}
      </div>

      {projectId ? (
        <section className="rounded-2xl border border-emerald-200/80 bg-emerald-50/40 p-6 shadow-sm">
          <h3 className="text-sm font-semibold uppercase tracking-wide text-emerald-800">
            Active project
          </h3>
          {currentProjectQuery.isLoading ? (
            <p className="mt-3 text-sm text-emerald-900/80">Loading project…</p>
          ) : currentProjectQuery.isError ? (
            <p className="mt-3 text-sm text-rose-900">
              Could not load the active project. It may have been deleted.
            </p>
          ) : currentProjectQuery.data ? (
            <div className="mt-3 grid gap-4 md:grid-cols-2">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wide text-emerald-900/80">
                  Name
                </label>
                <div className="mt-1 rounded-lg border border-emerald-200 bg-white px-3 py-2 text-sm font-medium text-slate-900">
                  {currentProjectQuery.data.name}
                </div>
              </div>
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wide text-emerald-900/80">
                  Ontology URI
                </label>
                <div className="mt-1 rounded-lg border border-emerald-200 bg-white px-3 py-2 font-mono text-xs text-slate-900">
                  {currentProjectQuery.data.ontology_uri}
                </div>
              </div>
              <div className="md:col-span-2 grid grid-cols-3 gap-3 text-sm">
                <div className="rounded-lg border border-emerald-200 bg-white px-3 py-2">
                  <div className="text-[10px] font-semibold uppercase tracking-wide text-emerald-900/70">
                    Domain areas
                  </div>
                  <div className="mt-0.5 text-xl font-semibold text-slate-900">
                    {ontologySummary?.areas ?? 0}
                  </div>
                </div>
                <div className="rounded-lg border border-emerald-200 bg-white px-3 py-2">
                  <div className="text-[10px] font-semibold uppercase tracking-wide text-emerald-900/70">
                    Iterations
                  </div>
                  <div className="mt-0.5 text-xl font-semibold text-slate-900">
                    {ontologySummary?.iterations ?? 0}
                  </div>
                </div>
                <div className="rounded-lg border border-emerald-200 bg-white px-3 py-2">
                  <div className="text-[10px] font-semibold uppercase tracking-wide text-emerald-900/70">
                    Knowledge docs
                  </div>
                  <div className="mt-0.5 text-xl font-semibold text-slate-900">
                    {currentProjectQuery.data.legal_knowledge_document_ids.length +
                      currentProjectQuery.data.expert_knowledge_document_ids.length}
                  </div>
                </div>
              </div>
            </div>
          ) : null}
        </section>
      ) : null}

      {projectId ? (
        <KnowledgeBaseSection projectId={projectId} />
      ) : (
        <section className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm">
          <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
            Knowledge base
          </h3>
          <p className="mt-2 text-sm text-slate-600">
            Choose a project in the header to manage its legal and expert documents.
          </p>
        </section>
      )}

      <div className="flex justify-end">
        <Link
          to="/domain-areas"
          search={{ projectId, packageIri: undefined }}
          className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
        >
          Continue to domain map
        </Link>
      </div>
    </div>
  )
}
