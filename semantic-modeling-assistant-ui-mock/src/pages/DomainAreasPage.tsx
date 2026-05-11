import { Link, getRouteApi } from '@tanstack/react-router'
import { WorkflowStepper } from '@/components/workflow'
import { resolveWorkflowContext } from '@/components/workflow'
import { mockDomainAreas } from '@/data/mockContent'

const domainAreasRouteApi = getRouteApi('/domain-areas')

export function DomainAreasPage() {
  const { projectId } = domainAreasRouteApi.useSearch()
  const linkContext = resolveWorkflowContext({ projectId })

  return (
    <div className="mx-auto max-w-5xl space-y-8">
      <WorkflowStepper activeStep="domain-areas" linkContext={linkContext} />

      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-slate-900">Domain areas</h2>
          <p className="mt-1 text-sm text-slate-600">
            Thematic sections derived from the knowledge base; edit labels or trigger analysis.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            Analyze knowledge base
          </button>
          <button
            type="button"
            className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
          >
            Create domain area
          </button>
        </div>
      </div>

      <section className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Create custom domain area</h3>
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          <input
            readOnly
            value="New custom domain area"
            className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-800"
          />
          <input
            readOnly
            value="key concept, another concept"
            className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-800"
          />
          <textarea
            readOnly
            rows={2}
            className="md:col-span-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-800"
            defaultValue="User-defined area focused on a specific legal chapter or modeling scope."
          />
        </div>
        <div className="mt-3">
          <button
            type="button"
            className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-emerald-700"
          >
            Save custom area
          </button>
        </div>
      </section>

      <div className="overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-sm">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-xs font-semibold uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-4 py-3">Area</th>
              <th className="px-4 py-3">Description</th>
              <th className="px-4 py-3">Key concepts</th>
              <th className="px-4 py-3 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {mockDomainAreas.map((area) => (
              <tr key={area.id} className="hover:bg-slate-50/80">
                <td className="px-4 py-4 font-medium text-slate-900">{area.label}</td>
                <td className="max-w-md px-4 py-4 text-slate-600">{area.description}</td>
                <td className="px-4 py-4">
                  <div className="flex flex-wrap gap-1">
                    {area.keyConcepts.map((c) => (
                      <span
                        key={c}
                        className="rounded-md bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700"
                      >
                        {c}
                      </span>
                    ))}
                  </div>
                </td>
                <td className="px-4 py-4 text-right">
                  <div className="inline-flex items-center gap-2">
                    <button
                      type="button"
                      className="whitespace-nowrap rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50"
                    >
                      Edit area
                    </button>
                    <Link
                      to="/iterations"
                      search={{ projectId, domainId: area.id }}
                      className="inline-flex whitespace-nowrap rounded-lg bg-emerald-600 px-3 py-2 text-xs font-semibold text-white shadow-sm hover:bg-emerald-700"
                    >
                      Open in iterations
                    </Link>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
