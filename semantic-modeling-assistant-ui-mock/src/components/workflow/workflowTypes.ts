export type WorkflowStepId = 'domain-areas' | 'iterations' | 'tasks' | 'operations' | 'export'

export const WORKFLOW_STEP_ORDER: WorkflowStepId[] = [
  'domain-areas',
  'iterations',
  'tasks',
  'operations',
  'export',
]

export function getWorkflowStepIndex(step: WorkflowStepId): number {
  return WORKFLOW_STEP_ORDER.indexOf(step)
}
