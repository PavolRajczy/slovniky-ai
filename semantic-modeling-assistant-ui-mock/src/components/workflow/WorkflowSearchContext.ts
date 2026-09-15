import { mockWorkflowContext } from '@/data/mockContent'

/** Resolves URL search + defaults for links in the workflow stepper and context capsule. */
export type WorkflowLinkContext = {
  /** Currently active project, propagated via URL search across all routes. */
  projectId: string | undefined
  domainId: string
  iterationId: string
  /** Which task's proposed operations are being reviewed (unique per task). */
  taskId: string
}

export function resolveWorkflowContext(search: {
  projectId?: string
  domainId?: string
  iterationId?: string
  taskId?: string
}): WorkflowLinkContext {
  return {
    projectId: search.projectId,
    domainId: search.domainId ?? mockWorkflowContext.domainId,
    iterationId: search.iterationId ?? mockWorkflowContext.iterationId,
    taskId: search.taskId ?? mockWorkflowContext.taskId,
  }
}
