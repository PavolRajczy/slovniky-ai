import { Link } from '@tanstack/react-router'
import { mockActivityHistory, mockGuidanceItems, mockWorkflowContext } from '@/data/mockContent'

const typeStyles = {
  instruction: 'bg-sky-50 text-sky-900',
  correction: 'bg-rose-50 text-rose-900',
  preference: 'bg-violet-50 text-violet-900',
  constraint: 'bg-amber-50 text-amber-950',
} as const

export function GuidancePage() {
  return (
    <div className="mx-auto max-w-4xl space-y-8">
      <div>
        <h2 className="text-2xl font-semibold tracking-tight text-slate-900">Project guidance</h2>
        <p className="mt-1 text-sm text-slate-600">
          Persistent instructions, corrections, preferences, and constraints merged into every agent call (Type B
          HITL).
        </p>
      </div>

      <section className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-sm">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Add guidance</h3>
        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <div>
            <label className="block text-sm font-medium text-slate-700" htmlFor="g-type">
              Type
            </label>
            <select
              id="g-type"
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
              defaultValue="instruction"
            >
              <option value="instruction">instruction</option>
              <option value="correction">correction</option>
              <option value="preference">preference</option>
              <option value="constraint">constraint</option>
            </select>
          </div>
          <div className="sm:col-span-2">
            <label className="block text-sm font-medium text-slate-700" htmlFor="g-text">
              Text
            </label>
            <textarea
              id="g-text"
              rows={3}
              placeholder="Write guidance the assistant should follow in all future steps…"
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
            />
          </div>
        </div>
        <button
          type="button"
          className="mt-4 rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
        >
          Save guidance item
        </button>
      </section>

      <section>
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">Active items</h3>
        <ul className="mt-4 space-y-3">
          {mockGuidanceItems.map((g) => (
            <li
              key={g.id}
              className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm"
            >
              <div className="flex flex-wrap items-center gap-2">
                <span
                  className={`rounded-full px-2 py-0.5 text-xs font-semibold capitalize ${typeStyles[g.type]}`}
                >
                  {g.type}
                </span>
                <span className="text-xs text-slate-400">{g.id}</span>
                <span className="rounded-md bg-slate-100 px-2 py-0.5 text-xs text-slate-600">source: {g.source}</span>
              </div>
              <p className="mt-2 text-sm leading-relaxed text-slate-800">{g.text}</p>
              <div className="mt-3 flex gap-3 text-xs font-medium">
                <button type="button" className="text-emerald-700">
                  Edit
                </button>
                <button type="button" className="text-rose-700">
                  Delete
                </button>
              </div>
            </li>
          ))}
        </ul>
      </section>

      <section className="rounded-xl border border-dashed border-slate-200 bg-slate-50/50 p-4 text-sm text-slate-600">
        <strong className="text-slate-800">History</strong>
        <ul className="mt-2 space-y-1">
          {mockActivityHistory.slice(0, 3).map((entry) => (
            <li key={entry.id} className="text-sm text-slate-600">
              {entry.at} — {entry.action}: {entry.detail}
            </li>
          ))}
        </ul>
      </section>

      <div className="flex justify-end">
        <Link
          to="/operations"
          search={{
            domainId: mockWorkflowContext.domainId,
            iterationId: mockWorkflowContext.iterationId,
            taskId: mockWorkflowContext.taskId,
          }}
          className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
        >
          Continue to operations review
        </Link>
      </div>
    </div>
  )
}
