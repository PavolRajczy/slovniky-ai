/** Static copy for mock UI — no API. */

export const mockProject = {
  ontologyUri: 'https://example.org/vocab/zakon-2024',
  name: 'Public Services Act — vocabulary draft',
}

export const mockDocuments = [
  {
    id: '1',
    name: 'zakon_hlava_1-3.pdf',
    size: '2.4 MB',
    indexed: true,
    kind: 'key' as const,
  },
  {
    id: '2',
    name: 'methodology-addendum.txt',
    size: '128 KB',
    indexed: true,
    kind: 'expert' as const,
  },
  {
    id: '3',
    name: 'internal-concept-notes.docx',
    size: '86 KB',
    indexed: false,
    kind: 'expert' as const,
  },
]

export const mockDomainAreas = [
  {
    id: 'a1',
    label: 'Scope of the act and term definitions',
    description: 'Core definitions and applicability scope.',
    keyConcepts: ['public service', 'provider', 'user'],
  },
  {
    id: 'a2',
    label: 'Obligations and rights of parties',
    description: 'Relations between entities and registration details.',
    keyConcepts: ['obligation', 'entitlement', 'registration'],
  },
  {
    id: 'a3',
    label: 'Control and sanctions',
    description: 'Inspection, violations, and consequences.',
    keyConcepts: ['inspection', 'sanction', 'appeal'],
  },
]

export const mockIterations = [
  {
    id: 'it-1',
    title: 'Identify core entities',
    status: 'done' as const,
    domainId: 'a1',
    domainArea: mockDomainAreas[0].label,
  },
  {
    id: 'it-2',
    title: 'Attributes of key classes',
    status: 'prepared' as const,
    domainId: 'a1',
    domainArea: mockDomainAreas[0].label,
  },
  {
    id: 'it-3',
    title: 'Relationships between entities',
    status: 'planned' as const,
    domainId: 'a2',
    domainArea: mockDomainAreas[1].label,
  },
]

export const mockTasks = [
  {
    id: 'task-1',
    title: 'Complete definition for class VerejnaSluzba',
    status: 'todo' as const,
    domainId: 'a1',
    iterationId: 'it-2',
  },
  {
    id: 'task-2',
    title: 'Propose attribute trvaniePoskytovania',
    status: 'in_progress' as const,
    domainId: 'a1',
    iterationId: 'it-2',
  },
  {
    id: 'task-3',
    title: 'Review cardinalities of relationship poskytuje',
    status: 'done' as const,
    domainId: 'a2',
    iterationId: 'it-3',
  },
  {
    id: 'task-4',
    title: 'Prepare draft sanction classes',
    status: 'todo' as const,
    domainId: 'a3',
    iterationId: null,
  },
]

export const mockActivityHistory = [
  {
    id: 'h-1',
    at: 'Today 14:12',
    action: 'Selected domain area',
    detail: mockDomainAreas[0].label,
    domainId: 'a1',
    iterationId: null,
  },
  {
    id: 'h-2',
    at: 'Today 14:18',
    action: 'Prepared iteration',
    detail: 'Attributes of key classes',
    domainId: 'a1',
    iterationId: 'it-2',
  },
  {
    id: 'h-3',
    at: 'Today 14:26',
    action: 'Reviewed operations',
    detail: 'Approved selected operations for export',
    domainId: 'a1',
    iterationId: 'it-2',
  },
  {
    id: 'h-4',
    at: 'Today 14:44',
    action: 'Opened tasks board',
    detail: 'Focused on ontology relationship checks',
    domainId: 'a2',
    iterationId: 'it-3',
  },
]

/** Each operation belongs to exactly one task run; review UI is scoped per task. */
export type MockOperation = {
  id: string
  taskId: string
  summary: string
  kind: string
  approved: boolean
}

export const mockOperations: MockOperation[] = [
  {
    id: 'task2-op-101',
    taskId: 'task-2',
    summary: 'Add class `VerejnaSluzba`',
    kind: 'add_class',
    approved: true,
  },
  {
    id: 'task2-op-102',
    taskId: 'task-2',
    summary: 'Add attribute `nazov` → `VerejnaSluzba`',
    kind: 'add_attribute',
    approved: true,
  },
  {
    id: 'task2-op-103',
    taskId: 'task-2',
    summary: 'Add class `PoskytovatelSluzby`',
    kind: 'add_class',
    approved: false,
  },
  {
    id: 'task2-op-104',
    taskId: 'task-2',
    summary: 'Add relationship `poskytuje` (Poskytovatel → VerejnaSluzba)',
    kind: 'add_relationship',
    approved: true,
  },
  {
    id: 'task3-op-201',
    taskId: 'task-3',
    summary: 'Set cardinality `poskytuje` to 1..* on `PoskytovatelSluzby`',
    kind: 'edit_relationship',
    approved: true,
  },
  {
    id: 'task3-op-202',
    taskId: 'task-3',
    summary: 'Add inverse label `je_poskytovana` on `VerejnaSluzba`',
    kind: 'edit_relationship',
    approved: false,
  },
]

export function getOperationsForTask(taskId: string): MockOperation[] {
  return mockOperations.filter((op) => op.taskId === taskId)
}

export const mockPreviewDiff = {
  classesAdded: ['VerejnaSluzba', 'PoskytovatelSluzby'],
  attributesAdded: ['VerejnaSluzba.nazov (xsd:string)'],
  relationshipsAdded: ['PoskytovatelSluzby —poskytuje→ VerejnaSluzba'],
}

export const mockPreviewDiffByTaskId: Record<
  string,
  { classesAdded: string[]; attributesAdded: string[]; relationshipsAdded: string[] }
> = {
  'task-2': {
    classesAdded: ['VerejnaSluzba', 'PoskytovatelSluzby'],
    attributesAdded: ['VerejnaSluzba.nazov (xsd:string)'],
    relationshipsAdded: ['PoskytovatelSluzby —poskytuje→ VerejnaSluzba'],
  },
  'task-3': {
    classesAdded: [],
    attributesAdded: [],
    relationshipsAdded: ['poskytuje: cardinality 1..*', 'je_poskytovana (inverse label)'],
  },
}

export function getPreviewDiffForTask(taskId: string) {
  return (
    mockPreviewDiffByTaskId[taskId] ?? {
      classesAdded: [] as string[],
      attributesAdded: [] as string[],
      relationshipsAdded: [] as string[],
    }
  )
}

export const mockWorkingCopyStats = {
  classes: 24,
  attributes: 61,
  relationships: 38,
}

export const mockDiffSummary = {
  addedNodes: 12,
  modifiedNodes: 3,
  removedNodes: 0,
}

export const mockGuidanceItems = [
  {
    id: 'g-1',
    type: 'instruction' as const,
    text: 'Prefer English labels for readability; keep URIs ASCII only.',
    source: 'manual',
  },
  {
    id: 'g-2',
    type: 'correction' as const,
    text: 'For legal entities, use prefix `has_` instead of `is_linked_to`.',
    source: 'rejection',
  },
  {
    id: 'g-3',
    type: 'preference' as const,
    text: 'Always provide `skos:definition` for newly created classes.',
    source: 'saved_from_request',
  },
]

export const mockSubareaClassUris = [
  'https://example.org/vocab/zakon-2024#VerejnaSluzba',
  'https://example.org/vocab/zakon-2024#PoskytovatelSluzby',
]

/** Default focus for mock workflow links and context capsule when URL has no search params. */
export const mockWorkflowContext = {
  domainId: 'a1',
  iterationId: 'it-2',
  /** Default task for operations review when no task is in the URL (e.g. stepper). */
  taskId: 'task-2',
  goal: 'Add missing attributes for Section 12 classes in the selected subarea.',
} as const

/** Used when export page has no search params (deep link). */
export const mockExportRecapDefaults = {
  approved: 3,
  pending: 1,
  rejected: 0,
  regenerated: 0,
  guidanceUpdated: false,
} as const

/** Shown in operations review after regenerating an operation (mock diff vs previous proposal). */
export const mockOperationProposalSwap: Record<string, { previousLabel: string; nextLabel: string }> = {
  'task2-op-103': {
    previousLabel: 'Add class `PoskytovatelSluzby`',
    nextLabel: 'Add class `PoskytovatelSluzba` (singular per methodology)',
  },
  'task3-op-202': {
    previousLabel: 'Add inverse label `je_poskytovana` on `VerejnaSluzba`',
    nextLabel: 'Add inverse label `je_poskytovany_sluzbou` on `VerejnaSluzba`',
  },
}
