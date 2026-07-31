import type { DiffSummary } from '@/api/operations'
import type { AppliedRejectedOperation } from '@/utils/appliedReviewStorage'
import { buildTargetReviewSummaries, type TargetReviewSummary } from '@/utils/reviewSummaryGroups'

type AppliedReviewSummaryModalProps = {
  title: string
  subtitle?: string
  keptCount: number
  rejectedCount: number
  summaries: TargetReviewSummary[]
  focusTaskName?: string | null
  onClose: () => void
}

export function AppliedReviewSummaryModal({
  title,
  subtitle,
  keptCount,
  rejectedCount,
  summaries,
  focusTaskName,
  onClose,
}: AppliedReviewSummaryModalProps) {
  const empty = summaries.length === 0

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center sm:items-center"
      role="dialog"
      aria-modal="true"
      aria-labelledby="applied-review-summary-title"
    >
      <button
        type="button"
        className="absolute inset-0 bg-slate-900/40"
        aria-label="Close applied review summary"
        onClick={onClose}
      />
      <div className="relative z-10 m-4 flex max-h-[85vh] w-full max-w-3xl flex-col rounded-2xl border border-slate-200 bg-white shadow-xl">
        <div className="border-b border-slate-100 px-5 py-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Applied review summary</p>
          <h3 id="applied-review-summary-title" className="mt-1 text-lg font-semibold text-slate-900">
            {title}
          </h3>
          {subtitle ? <p className="mt-1 text-sm text-slate-600">{subtitle}</p> : null}
          <div className="mt-3 flex flex-wrap gap-2 text-xs">
            <span className="rounded-full bg-emerald-50 px-2.5 py-0.5 font-semibold text-emerald-900">
              Applied {keptCount}
            </span>
            <span className="rounded-full bg-rose-50 px-2.5 py-0.5 font-semibold text-rose-900">
              Rejected {rejectedCount}
            </span>
            {focusTaskName ? (
              <span className="rounded-full bg-slate-100 px-2.5 py-0.5 font-medium text-slate-700">
                Opened from: {focusTaskName}
              </span>
            ) : null}
          </div>
        </div>

        <div className="overflow-y-auto px-5 py-4">
          {empty ? (
            <p className="rounded-lg border border-dashed border-slate-200 bg-slate-50 px-4 py-5 text-sm text-slate-600">
              No saved review summary is available yet. Summaries are stored when you finalize a work item
              from the review screen.
            </p>
          ) : (
            <div className="space-y-4">
              {summaries.map((group) => (
                <section
                  key={group.targetType}
                  className="rounded-xl border border-slate-200 bg-slate-50/60 p-4"
                >
                  <h4 className="text-sm font-semibold text-slate-900">{group.title}</h4>
                  <div className="mt-3 grid gap-4 md:grid-cols-2">
                    <SummaryDiffPanel title="Applied to ontology" diff={group.kept} tone="kept" />
                    <SummaryDiffPanel
                      title="Rejected"
                      diff={group.rejected}
                      tone="rejected"
                      rejectedDetails={group.rejectedWithReasons}
                    />
                  </div>
                </section>
              ))}
            </div>
          )}
        </div>

        <div className="border-t border-slate-100 px-5 py-4">
          <div className="flex justify-end">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

type SummaryDiffPanelProps = {
  title: string
  diff: DiffSummary
  tone: 'kept' | 'rejected'
  rejectedDetails?: AppliedRejectedOperation[]
}

function SummaryDiffPanel({ title, diff, tone, rejectedDetails = [] }: SummaryDiffPanelProps) {
  const rows = [
    ...diff.classesAdded.map((label) => ({ kind: 'added' as const, label })),
    ...diff.classesUpdated.map((label) => ({ kind: 'updated' as const, label })),
    ...diff.classesDeleted.map((label) => ({ kind: 'deleted' as const, label })),
    ...diff.attributesAdded.map((label) => ({ kind: 'added' as const, label })),
    ...diff.attributesUpdated.map((label) => ({ kind: 'updated' as const, label })),
    ...diff.attributesDeleted.map((label) => ({ kind: 'deleted' as const, label })),
    ...diff.relationshipsAdded.map((label) => ({ kind: 'added' as const, label })),
    ...diff.relationshipsUpdated.map((label) => ({ kind: 'updated' as const, label })),
    ...diff.relationshipsDeleted.map((label) => ({ kind: 'deleted' as const, label })),
  ]

  const reasonsByLabel = new Map<string, string>()
  for (const operation of rejectedDetails) {
    const label = operation.label?.trim() || operation.uri
    const reason = operation.rejectionReason?.trim()
    if (reason) reasonsByLabel.set(label, reason)
  }

  return (
    <div
      className={`rounded-lg border bg-white p-3 ${
        tone === 'kept' ? 'border-emerald-200' : 'border-rose-200'
      }`}
    >
      <p
        className={`text-xs font-semibold uppercase tracking-wide ${
          tone === 'kept' ? 'text-emerald-800' : 'text-rose-800'
        }`}
      >
        {title}
      </p>
      {rows.length === 0 ? (
        <p className="mt-2 text-xs text-slate-400">—</p>
      ) : (
        <ul className="mt-2 space-y-2">
          {rows.map((row) => (
            <li key={`${tone}-${row.kind}-${row.label}`} className="text-[11px] text-slate-700">
              <span
                className={
                  row.kind === 'added'
                    ? 'font-mono text-emerald-700'
                    : row.kind === 'updated'
                      ? 'font-mono text-amber-700'
                      : 'font-mono text-rose-700'
                }
              >
                {row.kind === 'added' ? '+ ' : row.kind === 'updated' ? '~ ' : '− '}
                {row.label}
              </span>
              {tone === 'rejected' && reasonsByLabel.get(row.label) ? (
                <p className="mt-1 rounded border border-rose-100 bg-rose-50 px-2 py-1 text-[11px] leading-5 text-rose-900">
                  {reasonsByLabel.get(row.label)}
                </p>
              ) : null}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export function buildModalReviewGroups(
  kept: Parameters<typeof buildTargetReviewSummaries>[0],
  rejected: Parameters<typeof buildTargetReviewSummaries>[1],
) {
  return buildTargetReviewSummaries(kept, rejected)
}
