import { Link } from '@tanstack/react-router'
import { useQuery } from '@tanstack/react-query'
import { listDomainAreas } from '@/api/domainAreas'
import { listIterations } from '@/api/iterations'
import { listTasks } from '@/api/tasks'
import type { DesignIterationModel, IterationsListResponse, TasksListResponse } from '@/api/types'

type WorkflowContextCapsuleProps = {
  projectId: string | undefined
  domainId?: string
  iterationId?: string
  taskId?: string
}

/** Where the user is in the modeling workflow: section, direction and work item of the project. */
export function WorkflowContextCapsule({ projectId, domainId, iterationId, taskId }: WorkflowContextCapsuleProps) {
  const areasQuery = useQuery({
    queryKey: ['project-domain-areas', projectId],
    queryFn: ({ signal }) => listDomainAreas(projectId!, signal),
    enabled: Boolean(projectId),
  })
  const iterationsQuery = useQuery({
    queryKey: ['project-iterations', projectId, 'all'],
    queryFn: ({ signal }) => listIterations(projectId!, {}, signal),
    enabled: Boolean(projectId),
  })
  const tasksQuery = useQuery({
    queryKey: ['iteration-tasks', projectId, iterationId],
    queryFn: ({ signal }) => listTasks(projectId!, iterationId!, signal),
    enabled: Boolean(projectId) && Boolean(iterationId),
  })

  const iteration = findIteration(iterationsQuery.data, iterationId)
  const sectionId = domainId ?? iteration?.focused_area_id
  const section = areasQuery.data?.find((area) => area.id === sectionId)
  const task = findTask(tasksQuery.data, taskId)
  const loading = areasQuery.isLoading || iterationsQuery.isLoading

  return (
    <section className="sticky top-0 z-10 rounded-xl border border-slate-200/90 bg-linear-to-r from-slate-50 to-white px-4 py-3 shadow-sm backdrop-blur-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <dl className="grid min-w-0 flex-1 grid-cols-[auto_minmax(0,1fr)] gap-x-3 gap-y-0.5 text-xs">
          <dt className="font-medium text-slate-500">Section</dt>
          <dd className="truncate font-semibold text-slate-900">{describe(section?.label, loading)}</dd>
          <dt className="font-medium text-slate-500">Direction</dt>
          <dd className="truncate text-slate-700">{describe(iteration?.name, loading)}</dd>
          {taskId ? (
            <>
              <dt className="font-medium text-slate-500">Work item</dt>
              <dd className="truncate text-slate-700">{describe(task?.name, tasksQuery.isLoading)}</dd>
            </>
          ) : null}
        </dl>
        <div className="flex shrink-0 flex-wrap gap-2">
          <Link
            to="/domain-areas"
            search={{ projectId, packageIri: undefined }}
            className="rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
          >
            Domain map
          </Link>
          <Link
            to="/iterations-v2"
            search={{ projectId, domainId: sectionId }}
            className="rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
          >
            Directions
          </Link>
          <Link
            to="/tasks"
            search={{ projectId, domainId: sectionId, iterationId, taskId }}
            className="rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
          >
            Prepare changes
          </Link>
        </div>
      </div>
    </section>
  )
}

function describe(value: string | undefined, loading: boolean): string {
  if (value) return value
  return loading ? 'Loading…' : 'Not selected'
}

function findIteration(
  data: IterationsListResponse | undefined,
  iterationId: string | undefined,
): DesignIterationModel | undefined {
  if (!data || !iterationId) return undefined
  return [
    ...data.planned_iterations,
    ...(data.current_iteration ? [data.current_iteration] : []),
    ...data.finished_iterations,
  ].find((iteration) => iteration.id === iterationId)
}

function findTask(data: TasksListResponse | undefined, taskId: string | undefined) {
  if (!data || !taskId) return undefined
  return [
    ...data.planned_tasks,
    ...(data.current_task ? [data.current_task] : []),
    ...data.finished_tasks,
  ].find((task) => task.id === taskId)
}
