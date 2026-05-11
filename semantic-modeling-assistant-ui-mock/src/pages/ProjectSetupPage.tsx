import { Link } from '@tanstack/react-router'
import { mockDocuments, mockProject } from '@/data/mockContent'

export function ProjectSetupPage() {
  const keyDocument = mockDocuments.find((doc) => doc.kind === 'key')
  const expertDocuments = mockDocuments.filter((doc) => doc.kind === 'expert')
  const keyDocumentUrl = 'https://opendata.eselpoint.cz/esel-esb/eli/cz/sb/2021/250/2021-07-01'

  return (
    <div className="mx-auto max-w-4xl space-y-8">
      <div>
        <h2 className="text-2xl font-semibold tracking-tight text-slate-900">Project & knowledge base</h2>
        <p className="mt-1 text-sm text-slate-600">
          Create or open a project and load domain documents for retrieval.
        </p>
      </div>

      <section className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Ontology</h3>
        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <div className="sm:col-span-2">
            <label className="block text-sm font-medium text-slate-700" htmlFor="title">
              Project title
            </label>
            <input
              id="title"
              readOnly
              className="mt-1 w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm"
              value={mockProject.name}
            />
          </div>
          <details className="sm:col-span-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2">
            <summary className="cursor-pointer text-sm font-medium text-slate-700">Advanced info</summary>
            <div className="mt-3">
              <label className="block text-sm font-medium text-slate-700" htmlFor="uri">
                Target ontology URI
              </label>
              <input
                id="uri"
                readOnly
                className="mt-1 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 font-mono text-sm text-slate-800"
                value={mockProject.ontologyUri}
              />
            </div>
          </details>
        </div>
      </section>

      <section className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Knowledge base</h3>
            <p className="mt-1 text-sm text-slate-600">
              Upload a key document for area analysis and separate domain expert documents for supporting context.
            </p>
          </div>
        </div>

        <div className="mt-6 grid gap-4 md:grid-cols-2">
          <section className="rounded-xl border border-slate-200 bg-slate-50/80 p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h4 className="text-sm font-semibold text-slate-900">Key document</h4>
                <p className="mt-1 text-xs text-slate-600">
                  Primary legal source for domain-area analysis (link from Czech legal information system).
                </p>
              </div>
            </div>
            <div className="mt-4 space-y-2 rounded-lg border border-slate-200 bg-white p-3">
              <div>
                <label className="text-xs font-medium text-slate-700" htmlFor="key-document-url">
                  Legal act URL
                </label>
                <input
                  id="key-document-url"
                  readOnly
                  className="mt-1 w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 font-mono text-xs text-slate-800"
                  value={keyDocumentUrl}
                />
                <div className="mt-2 flex justify-end">
                  <button
                    type="button"
                    className="rounded-lg bg-slate-900 px-3 py-1.5 text-xs font-medium text-white hover:bg-slate-800"
                  >
                    Link key document
                  </button>
                </div>
              </div>
              <div className="border-t border-slate-100 pt-3">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs font-medium text-slate-700">Or upload directly</span>
                  <button
                    type="button"
                    className="rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-medium text-white shadow-sm hover:bg-emerald-700"
                  >
                    Upload key document…
                  </button>
                </div>
                <div className="mt-2 rounded-lg border border-dashed border-slate-300 bg-slate-50 px-4 py-4 text-center text-xs text-slate-500">
                  Drop 1 primary legal/domain file here (mock).
                </div>
              </div>
            </div>
            {keyDocument ? (
              <div className="mt-3 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm">
                <div className="font-medium text-slate-800">{keyDocument.name}</div>
                <div className="mt-1 text-xs text-slate-500">{keyDocument.size}</div>
              </div>
            ) : null}
          </section>

          <section className="rounded-xl border border-slate-200 bg-slate-50/80 p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h4 className="text-sm font-semibold text-slate-900">Domain expert documents</h4>
                <p className="mt-1 text-xs text-slate-600">Supplementary material for retrieval and task context.</p>
              </div>
              <button
                type="button"
                className="rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-medium text-white shadow-sm hover:bg-emerald-700"
              >
                Upload expert documents…
              </button>
            </div>
            <div className="mt-4 rounded-lg border border-dashed border-slate-300 bg-white px-4 py-6 text-center text-xs text-slate-500">
              Drop supporting PDFs/text files here (mock).
            </div>
            <ul className="mt-3 divide-y divide-slate-100 rounded-lg border border-slate-200 bg-white">
              {expertDocuments.map((doc) => (
                <li key={doc.id} className="flex items-center justify-between gap-3 px-3 py-2 text-sm">
                  <span className="font-medium text-slate-800">{doc.name}</span>
                  <span className="text-xs text-slate-500">
                    {doc.size}
                    {doc.indexed ? (
                      <span className="ml-2 rounded-md bg-emerald-50 px-2 py-0.5 text-[11px] font-medium text-emerald-800">
                        indexed
                      </span>
                    ) : (
                      <span className="ml-2 rounded-md bg-amber-50 px-2 py-0.5 text-[11px] font-medium text-amber-800">
                        pending
                      </span>
                    )}
                  </span>
                </li>
              ))}
            </ul>
          </section>
        </div>
      </section>

      <div className="flex justify-end">
        <Link
          to="/domain-areas"
          className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
        >
          Continue to domain areas
        </Link>
      </div>
    </div>
  )
}
