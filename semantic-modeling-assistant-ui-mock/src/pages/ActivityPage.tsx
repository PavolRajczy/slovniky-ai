import { Link, getRouteApi } from '@tanstack/react-router'
import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { listProjectActivity } from '@/api/activity'
import type { ProjectActivityEventModel, ProjectActivityEventType } from '@/api/types'
import { resolveWorkflowContext } from '@/components/workflow'

const activityRouteApi = getRouteApi('/activity')

const eventLabels: Record<ProjectActivityEventType, string> = {
  guidance_added: 'Guidance added',
  guidance_updated: 'Guidance edited',
  guidance_deleted: 'Guidance removed',
  domain_areas_generated: 'Domain areas generated',
  iterations_suggested: 'Iterations suggested',
  tasks_planned: 'Tasks planned',
  operations_generated: 'Changes proposed',
  iteration_prepared: 'Iteration prepared',
  iteration_applied: 'Changes applied',
  operation_approved: 'Change kept',
  operation_rejected: 'Change rejected',
  ontology_exported: 'Ontology exported',
}

const eventStyles: Record<ProjectActivityEventType, string> = {
  guidance_added: 'bg-violet-50 text-violet-900',
  guidance_updated: 'bg-violet-50 text-violet-900',
  guidance_deleted: 'bg-violet-50 text-violet-900',
  domain_areas_generated: 'bg-sky-50 text-sky-900',
  iterations_suggested: 'bg-sky-50 text-sky-900',
  tasks_planned: 'bg-sky-50 text-sky-900',
  operations_generated: 'bg-sky-50 text-sky-900',
  iteration_prepared: 'bg-sky-50 text-sky-900',
  iteration_applied: 'bg-emerald-50 text-emerald-900',
  operation_approved: 'bg-emerald-50 text-emerald-900',
  operation_rejected: 'bg-rose-50 text-rose-900',
  ontology_exported: 'bg-amber-50 text-amber-950',
}

type FilterId = 'all' | 'assistant' | 'decisions' | 'guidance' | 'applied'

const filters: { id: FilterId; label: string; types?: ProjectActivityEventType[] }[] = [
  { id: 'all', label: 'Everything' },
  {
    id: 'assistant',
    label: 'Assistant proposals',
    types: [
      'domain_areas_generated',
      'iterations_suggested',
      'tasks_planned',
      'operations_generated',
      'iteration_prepared',
    ],
  },
  {
    id: 'decisions',
    label: 'Your decisions',
    types: ['operation_approved', 'operation_rejected'],
  },
  {
    id: 'guidance',
    label: 'Guidance',
    types: ['guidance_added', 'guidance_updated', 'guidance_deleted'],
  },
  {
    id: 'applied',
    label: 'Applied & exported',
    types: ['iteration_applied', 'ontology_exported'],
  },
]

export function ActivityPage() {
  const { projectId } = activityRouteApi.useSearch()
  const linkContext = resolveWorkflowContext({ projectId })
  const [filter, setFilter] = useState<FilterId>('all')

  const activeFilter = filters.find((entry) => entry.id === filter) ?? filters[0]

  const activityQuery = useQuery({
    queryKey: ['project-activity', projectId, activeFilter.id],
    queryFn: ({ signal }) =>
      listProjectActivity(projectId!, { types: activeFilter.types }, signal),
    enabled: Boolean(projectId),
  })

  const groups = useMemo(
    () => groupEventsByDay(activityQuery.data?.events ?? []),
    [activityQuery.data?.events],
  )

  if (!projectId) {
    return (
      <div className="mx-auto max-w-3xl space-y-4">
        <div className="rounded-2xl border border-amber-200 bg-amber-50 p-6 text-sm text-amber-900">
          No project selected. Open the{' '}
          <Link to="/project" search={{ projectId: undefined }} className="font-medium underline">
            project setup page
          </Link>{' '}
          and pick or create a project first.
        </div>
      </div>
    )
  }

  const approved = activityQuery.data?.approved_count ?? 0
  const rejected = activityQuery.data?.rejected_count ?? 0
  const total = approved + rejected
  const keepRate = total > 0 ? Math.round((approved / total) * 100) : null

  return (
    <div className="mx-auto max-w-4xl space-y-8">
      <div>
        <h2 className="text-2xl font-semibold tracking-tight text-slate-900">Activity</h2>
        <p className="mt-1 text-sm text-slate-600">
          A record of what the assistant proposed and what you decided, kept on the server so it
          survives reloads and other machines.
        </p>
      </div>

      <section className="grid gap-4 sm:grid-cols-3">
        <StatCard label="Changes kept" value={approved} tone="text-emerald-700" />
        <StatCard label="Changes rejected" value={rejected} tone="text-rose-700" />
        <StatCard
          label="Keep rate"
          value={keepRate === null ? '—' : `${keepRate}%`}
          tone="text-slate-900"
        />
      </section>

      <div className="flex flex-wrap gap-2">
        {filters.map((entry) => (
          <button
            key={entry.id}
            type="button"
            onClick={() => setFilter(entry.id)}
            className={
              entry.id === filter
                ? 'rounded-full bg-slate-900 px-3 py-1.5 text-xs font-medium text-white'
                : 'rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50'
            }
          >
            {entry.label}
          </button>
        ))}
      </div>

      {activityQuery.isError ? (
        <p className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-900">
          Could not load activity: {(activityQuery.error as Error).message}
        </p>
      ) : null}

      {activityQuery.isSuccess && groups.length === 0 ? (
        <p className="rounded-xl border border-dashed border-slate-200 bg-slate-50/70 p-4 text-sm text-slate-600">
          Nothing recorded yet for this filter. Prepare an iteration or review some proposed changes
          and they will show up here.
        </p>
      ) : null}

      <div className="space-y-8">
        {groups.map((group) => (
          <section key={group.day}>
            <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-500">
              {group.day}
            </h3>
            <ol className="mt-3 space-y-3 border-l border-slate-200 pl-4">
              {group.events.map((event) => (
                <li key={event.id} className="relative">
                  <span className="absolute -left-5.25 top-2 h-2 w-2 rounded-full bg-slate-300" />
                  <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                    <div className="flex flex-wrap items-center gap-2">
                      <span
                        className={`rounded-full px-2 py-0.5 text-xs font-semibold ${eventStyles[event.type]}`}
                      >
                        {eventLabels[event.type]}
                      </span>
                      <span className="rounded-md bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
                        {event.actor === 'assistant' ? 'Assistant' : 'You'}
                      </span>
                      <span className="text-xs text-slate-400">{formatTime(event.at)}</span>
                    </div>
                    <p className="mt-2 text-sm leading-relaxed text-slate-800">{event.summary}</p>
                    <EventDetail event={event} />
                    <EventLinks event={event} projectId={projectId} domainId={linkContext.domainId} />
                  </div>
                </li>
              ))}
            </ol>
          </section>
        ))}
      </div>
    </div>
  )
}

function StatCard({
  label,
  value,
  tone,
}: {
  label: string
  value: number | string
  tone: string
}) {
  return (
    <div className="rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm">
      <div className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</div>
      <div className={`mt-1 text-2xl font-semibold tabular-nums ${tone}`}>{value}</div>
    </div>
  )
}

function EventDetail({ event }: { event: ProjectActivityEventModel }) {
  const reason = readString(event.detail.reason)
  const content = readString(event.detail.content)
  const instruction = readString(event.detail.userInstruction)
  const names = readStringArray(event.detail.names)
  const savedAsGuidance = event.detail.savedAsGuidance === true

  const hasDetail = reason || content || instruction || names.length > 0
  if (!hasDetail) {
    return null
  }

  return (
    <div className="mt-2 space-y-1.5 text-xs text-slate-600">
      {reason ? (
        <p>
          <span className="font-medium text-slate-700">Reason:</span> {reason}
          {savedAsGuidance ? (
            <span className="ml-2 rounded bg-violet-50 px-1.5 py-0.5 text-violet-900">
              saved as guidance
            </span>
          ) : null}
        </p>
      ) : null}
      {content ? (
        <p>
          <span className="font-medium text-slate-700">Text:</span> {content}
        </p>
      ) : null}
      {instruction ? (
        <p>
          <span className="font-medium text-slate-700">Your instruction:</span> {instruction}
        </p>
      ) : null}
      {names.length > 0 ? (
        <p>
          <span className="font-medium text-slate-700">Items:</span> {names.join(' · ')}
        </p>
      ) : null}
    </div>
  )
}

function EventLinks({
  event,
  projectId,
  domainId,
}: {
  event: ProjectActivityEventModel
  projectId: string
  domainId?: string
}) {
  if (!event.iteration_id) {
    return null
  }

  return (
    <div className="mt-3 flex gap-3 text-xs font-medium">
      <Link
        to="/tasks"
        search={{ projectId, domainId, iterationId: event.iteration_id, taskId: undefined }}
        className="text-emerald-700"
      >
        Open iteration
      </Link>
      {event.task_id ? (
        <Link
          to="/operations"
          search={{
            projectId,
            domainId,
            iterationId: event.iteration_id,
            taskId: event.task_id,
          }}
          className="text-emerald-700"
        >
          Open review
        </Link>
      ) : null}
    </div>
  )
}

type ActivityDayGroup = {
  day: string
  events: ProjectActivityEventModel[]
}

function groupEventsByDay(events: ProjectActivityEventModel[]): ActivityDayGroup[] {
  const groups: ActivityDayGroup[] = []

  for (const event of events) {
    const day = formatDay(event.at)
    const last = groups[groups.length - 1]
    if (last && last.day === day) {
      last.events.push(event)
    } else {
      groups.push({ day, events: [event] })
    }
  }

  return groups
}

function formatDay(value: string): string {
  const date = new Date(value)
  if (!Number.isFinite(date.getTime())) {
    return 'Unknown date'
  }

  const today = new Date()
  const isSameDay = (left: Date, right: Date) =>
    left.getFullYear() === right.getFullYear() &&
    left.getMonth() === right.getMonth() &&
    left.getDate() === right.getDate()

  if (isSameDay(date, today)) {
    return 'Today'
  }

  const yesterday = new Date(today)
  yesterday.setDate(today.getDate() - 1)
  if (isSameDay(date, yesterday)) {
    return 'Yesterday'
  }

  return date.toLocaleDateString()
}

function formatTime(value: string): string {
  const date = new Date(value)
  if (!Number.isFinite(date.getTime())) {
    return value
  }
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function readString(value: unknown): string | undefined {
  return typeof value === 'string' && value.trim().length > 0 ? value : undefined
}

function readStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return []
  }
  return value.filter((entry): entry is string => typeof entry === 'string')
}
