import type { OntologyModel, OntologyOperationModel } from '@/api/types'

export type MissingClass = {
  uri: string
  label: string
}

/** Class URIs the change refers to: attribute domain, relationship domain and range, or generalizations. */
function referencedClassUris(op: OntologyOperationModel): string[] {
  if (op.operation_type === 'delete') return []
  if (op.target_type === 'attribute') return op.owning_class_uri ? [op.owning_class_uri] : []
  if (op.target_type === 'relationship') {
    return [op.source_class_uri, op.target_class_uri].filter((uri): uri is string => Boolean(uri))
  }
  return op.generalization_uris ?? []
}

/**
 * Classes that a kept change needs but that are neither in the vocabulary nor created by
 * another kept change. Such a change cannot be applied.
 */
export function findMissingClasses(
  op: OntologyOperationModel,
  ontology: OntologyModel | undefined,
  keptOperations: OntologyOperationModel[],
  allOperations: OntologyOperationModel[],
): MissingClass[] {
  if (!ontology) return []
  const existing = new Set(ontology.classes.map((cls) => cls.uri))
  const keptCreates = new Set(
    keptOperations
      .filter((kept) => kept.target_type === 'class' && kept.operation_type === 'create')
      .map((kept) => kept.uri),
  )
  return referencedClassUris(op)
    .filter((uri) => !existing.has(uri) && !keptCreates.has(uri))
    .map((uri) => ({ uri, label: proposedClassLabel(uri, allOperations) }))
}

/** Label of a class from the vocabulary, or from the change that proposes it. */
export function classLabel(
  uri: string,
  ontology: OntologyModel | undefined,
  operations: OntologyOperationModel[],
): string {
  return ontology?.classes.find((cls) => cls.uri === uri)?.label ?? proposedClassLabel(uri, operations)
}

function proposedClassLabel(uri: string, operations: OntologyOperationModel[]): string {
  const proposal = operations.find(
    (op) => op.target_type === 'class' && op.operation_type === 'create' && op.uri === uri,
  )
  return proposal?.label ?? uri.split(/[#/]/).pop() ?? uri
}
