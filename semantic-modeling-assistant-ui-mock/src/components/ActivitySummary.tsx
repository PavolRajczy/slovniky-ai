import { Link } from '@tanstack/react-router'
import { useQuery } from '@tanstack/react-query'
import { listProjectActivity } from '@/api/activity'

type ActivitySummaryProps = {
  projectId?: string
  /** When set, counts and the latest entry are limited to this iteration. */
  iterationId?: string
}

/**
 * Compact strip showing the keep/reject totals and the most recent activity entry,
 * so history is visible next to the work instead of only on the activity page.
 */
export function ActivitySummary({ projectId, iterationId }: ActivitySummaryProps) {
  const activityQuery = useQuery({
    queryKey: ['project-activity', projectId, 'summary', iterationId ?? 'all'],
    queryFn: ({ signal }) =>
      listProjectActivity(projectId!, { iterationId, limit: 1 }, signal),
    enabled: Boolean(projectId),
  })

  if (!projectId || !activityQuery.data) {
    return null
  }

  const { approved_count: approved, rejected_count: rejected, events } = activityQuery.data
  const latest = events[0]

  if (approved + rejected === 0 && !latest) {
    return null
  }

  return (
    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs text-slate-600 shadow-sm">
      <span>
        <span className="font-semibold tabular-nums text-emerald-700">{approved}</span> kept
      </span>
      <span className="text-slate-300">·</span>
      <span>
        <span className="font-semibold tabular-nums text-rose-700">{rejected}</span> rejected
      </span>
      {latest ? (
        <>
          <span className="text-slate-300">·</span>
          <span className="truncate">
            last: {latest.summary} {formatRelative(latest.at)}
          </span>
        </>
      ) : null}
      <Link
        to="/activity"
        search={{ projectId }}
        className="ml-auto shrink-0 font-medium text-emerald-700"
      >
        View activity
      </Link>
    </div>
  )
}

function formatRelative(value: string): string {
  const time = new Date(value).getTime()
  if (!Number.isFinite(time)) {
    return ''
  }

  const minutes = Math.round((Date.now() - time) / 60000)
  if (minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes} min ago`

  const hours = Math.round(minutes / 60)
  if (hours < 24) return `${hours} h ago`

  const days = Math.round(hours / 24)
  return days === 1 ? 'yesterday' : `${days} days ago`
}
