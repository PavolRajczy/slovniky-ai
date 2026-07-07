import { Link } from '@tanstack/react-router'
import { useMemo, useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { createProject, getProject, listProjects } from '@/api/projects'
import { importOntologyFromDataspecer } from '@/api/ontologies'
import { ApiError } from '@/api/client'
import { useCurrentProject } from '@/hooks/useCurrentProject'
import { KnowledgeBaseSection } from '@/components/KnowledgeBaseSection'

type ImportFormState = {
  name: string
  url: string
  baseUri: string
  domainName: string
  domainDescription: string
}

const INITIAL_FORM: ImportFormState = {
  name: '',
  url: '',
  baseUri: '',
  domainName: '',
  domainDescription: '',
}

export function ProjectSetupPage() {
  const { projectId, setProjectId } = useCurrentProject()
  const queryClient = useQueryClient()
  const [importForm, setImportForm] = useState<ImportFormState>(INITIAL_FORM)
  const [importError, setImportError] = useState<string | null>(null)

  const projectsQuery = useQuery({
    queryKey: ['projects'],
    queryFn: ({ signal }) => listProjects(signal),
  })

  const currentProjectQuery = useQuery({
    queryKey: ['project', projectId],
    queryFn: ({ signal }) => getProject(projectId!, signal),
    enabled: Boolean(projectId),
  })

  const importMutation = useMutation({
    mutationFn: async (form: ImportFormState) => {
      const ontology = await importOntologyFromDataspecer({
        url: form.url.trim(),
        base_uri: form.baseUri.trim(),
      })
      const project = await createProject({
        name: form.name.trim(),
        ontology_uri: ontology.uri,
        knowledge_domain_name: form.domainName.trim() || `Domain of ${form.name.trim()}`,
        knowledge_domain_description: form.domainDescription.trim(),
      })
      return project
    },
    onSuccess: async (project) => {
      setImportError(null)
      setImportForm(INITIAL_FORM)
      await queryClient.invalidateQueries({ queryKey: ['projects'] })
      setProjectId(project.id)
    },
    onError: (error: unknown) => {
      if (error instanceof ApiError) {
        setImportError(error.message)
      } else if (error instanceof Error) {
        setImportError(error.message)
      } else {
        setImportError('Import failed.')
      }
    },
  })

  const handleImportSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!importForm.name.trim() || !importForm.url.trim() || !importForm.baseUri.trim()) {
      setImportError('Project name, Dataspecer model URL and base IRI are all required.')
      return
    }
    importMutation.mutate(importForm)
  }

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
          Start by importing a Dataspecer vocabulary (or picking an existing project), then attach the legal
          and expert documents that will fuel the assistant.
        </p>
      </div>

      {/* <section className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
            Step 1 · Pick an existing project
          </h3>
          {projectsQuery.isFetching ? (
            <span className="text-xs text-slate-500">loading…</span>
          ) : null}
        </div>
        {projectsQuery.isError ? (
          <p className="mt-3 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-900">
            Could not load projects: {(projectsQuery.error as Error).message}
          </p>
        ) : null}
        {projectsQuery.data && projectsQuery.data.length === 0 ? (
          <p className="mt-3 text-sm text-slate-500">
            No projects yet — import a Dataspecer vocabulary below to create the first one.
          </p>
        ) : null}
        {projectsQuery.data && projectsQuery.data.length > 0 ? (
          <ul className="mt-4 divide-y divide-slate-100 rounded-lg border border-slate-200">
            {projectsQuery.data.map((project) => {
              const isActive = project.id === projectId
              return (
                <li
                  key={project.id}
                  className={`flex flex-wrap items-center justify-between gap-2 px-3 py-2 text-sm ${
                    isActive ? 'bg-emerald-50/70' : 'bg-white'
                  }`}
                >
                  <div className="min-w-0">
                    <div className="font-semibold text-slate-900">{project.name}</div>
                    <div className="font-mono text-xs text-slate-500">{project.ontology_uri}</div>
                    <div className="mt-1 text-xs text-slate-500">
                      {project.domain_areas_count} domain areas · {project.iterations_count} iterations
                    </div>
                  </div>
                  <div className="flex shrink-0 items-center gap-2">
                    {isActive ? (
                      <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-semibold text-emerald-900">
                        active
                      </span>
                    ) : (
                      <button
                        type="button"
                        className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
                        onClick={() => setProjectId(project.id)}
                      >
                        Select
                      </button>
                    )}
                  </div>
                </li>
              )
            })}
          </ul>
        ) : null}
      </section>

      <section className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
          Step 2 · Import a vocabulary from Dataspecer
        </h3>
        <p className="mt-1 text-sm text-slate-600">
          Provide the public Dataspecer model URL of an existing Dataspecer specification and the
          base IRI it uses. The assistant fetches and persists the vocabulary, then creates a new design
          project bound to it.
        </p>

        <form className="mt-4 grid gap-3 md:grid-cols-2" onSubmit={handleImportSubmit}>
          <div>
            <label className="block text-sm font-medium text-slate-700" htmlFor="import-name">
              Project name
            </label>
            <input
              id="import-name"
              className="mt-1 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm"
              placeholder="Public Services Act — vocabulary draft"
              value={importForm.name}
              onChange={(event) =>
                setImportForm((prev) => ({ ...prev, name: event.target.value }))
              }
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700" htmlFor="import-domain-name">
              Domain name (optional)
            </label>
            <input
              id="import-domain-name"
              className="mt-1 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm"
              placeholder="Domain of public services"
              value={importForm.domainName}
              onChange={(event) =>
                setImportForm((prev) => ({ ...prev, domainName: event.target.value }))
              }
            />
          </div>

          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-slate-700" htmlFor="import-url">
              Dataspecer model URL
            </label>
            <input
              id="import-url"
              className="mt-1 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 font-mono text-xs"
              placeholder="https://backend.dataspecer.com/.../simplified-semantic-model.json"
              value={importForm.url}
              onChange={(event) =>
                setImportForm((prev) => ({ ...prev, url: event.target.value }))
              }
            />
          </div>

          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-slate-700" htmlFor="import-base-uri">
              Base IRI of the vocabulary
            </label>
            <input
              id="import-base-uri"
              className="mt-1 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 font-mono text-xs"
              placeholder="https://slovník.gov.cz/legislativni/sbirka/2021/250/"
              value={importForm.baseUri}
              onChange={(event) =>
                setImportForm((prev) => ({ ...prev, baseUri: event.target.value }))
              }
            />
          </div>

          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-slate-700" htmlFor="import-domain-desc">
              Domain description (optional)
            </label>
            <textarea
              id="import-domain-desc"
              rows={2}
              className="mt-1 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm"
              placeholder="Short summary of the domain this vocabulary covers."
              value={importForm.domainDescription}
              onChange={(event) =>
                setImportForm((prev) => ({ ...prev, domainDescription: event.target.value }))
              }
            />
          </div>

          {importError ? (
            <div className="md:col-span-2 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-900">
              {importError}
            </div>
          ) : null}

          <div className="md:col-span-2 flex flex-wrap items-center justify-end gap-2">
            <button
              type="submit"
              disabled={importMutation.isPending}
              className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {importMutation.isPending
                ? 'Importing…'
                : 'Import vocabulary and create project'}
            </button>
          </div>
        </form>
      </section>

      {projectId ? (
        <section className="rounded-2xl border border-emerald-200/80 bg-emerald-50/40 p-6 shadow-sm">
          <h3 className="text-sm font-semibold uppercase tracking-wide text-emerald-800">
            Step 3 · Active project
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
      ) : null} */}

      {projectId ? (
        <KnowledgeBaseSection projectId={projectId} />
      ) : (
        <section className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm">
          <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
            Knowledge base
          </h3>
          <p className="mt-2 text-sm text-slate-600">
            Pick or create a project above to manage its legal and expert documents.
          </p>
        </section>
      )}

      <div className="flex justify-end">
        <Link
          to="/domain-areas"
          search={{ projectId }}
          className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
        >
          Continue to domain map
        </Link>
      </div>
    </div>
  )
}
