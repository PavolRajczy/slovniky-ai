import { mockWorkflowContext } from '@/data/mockContent'

/** Resolves URL search + defaults for links in the workflow stepper and context capsule. */
export type WorkflowLinkContext = {
  domainId: string
  iterationId: string
  /** Which task's proposed operations are being reviewed (unique per task). */
  taskId: string
}

export function resolveWorkflowContext(search: {
  domainId?: string
  iterationId?: string
  taskId?: string
}): WorkflowLinkContext {
  return {
    domainId: search.domainId ?? mockWorkflowContext.domainId,
    iterationId: search.iterationId ?? mockWorkflowContext.iterationId,
    taskId: search.taskId ?? mockWorkflowContext.taskId,
  }
}
