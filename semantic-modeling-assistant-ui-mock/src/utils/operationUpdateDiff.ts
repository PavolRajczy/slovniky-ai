import type { OntologyModel, OntologyOperationModel } from '@/api/types'

export type OperationFieldChange = {
  field: string
  before: string
  after: string
}

type ComparableField = {
  key: keyof Pick<
    OntologyOperationModel,
    | 'label'
    | 'definition'
    | 'description'
    | 'kind'
    | 'owning_class_uri'
    | 'source_class_uri'
    | 'target_class_uri'
  >
  label: string
}

const COMPARABLE_FIELDS: ComparableField[] = [
  { key: 'label', label: 'Label' },
  { key: 'definition', label: 'Definition' },
  { key: 'description', label: 'Description' },
  { key: 'kind', label: 'Kind' },
  { key: 'owning_class_uri', label: 'Owning class' },
  { key: 'source_class_uri', label: 'Source class' },
  { key: 'target_class_uri', label: 'Target class' },
]

function formatValue(value: string | null | undefined): string {
  return value?.trim() ?? ''
}

function formatGeneralizations(values: string[] | null | undefined): string {
  if (!values || values.length === 0) return ''
  return values.join(', ')
}

export function buildOperationFieldChanges(
  ontology: OntologyModel | undefined,
  operation: OntologyOperationModel,
): OperationFieldChange[] {
  if (operation.operation_type !== 'update' || !ontology) return []

  const current = findOntologyElement(ontology, operation)
  if (!current) return []

  const changes: OperationFieldChange[] = []

  for (const field of COMPARABLE_FIELDS) {
    const before = formatValue(current[field.key])
    const after = formatValue(operation[field.key])
    if (before !== after) {
      changes.push({
        field: field.label,
        before: before || '—',
        after: after || '—',
      })
    }
  }

  const beforeGeneralizations = formatGeneralizations(current.generalization_uris)
  const afterGeneralizations = formatGeneralizations(operation.generalization_uris)
  if (beforeGeneralizations !== afterGeneralizations) {
    changes.push({
      field: 'Generalizations',
      before: beforeGeneralizations || '—',
      after: afterGeneralizations || '—',
    })
  }

  return changes
}

type OntologySnapshot = {
  label?: string | null
  definition?: string | null
  description?: string | null
  kind?: string | null
  generalization_uris?: string[] | null
  owning_class_uri?: string | null
  source_class_uri?: string | null
  target_class_uri?: string | null
}

function findOntologyElement(
  ontology: OntologyModel,
  operation: OntologyOperationModel,
): OntologySnapshot | null {
  if (operation.target_type === 'class') {
    const ontologyClass = ontology.classes.find((item) => item.uri === operation.uri)
    if (!ontologyClass) return null
    return {
      label: ontologyClass.label,
      definition: ontologyClass.definition,
      description: ontologyClass.description,
      generalization_uris: ontologyClass.parent_classes,
    }
  }

  if (operation.target_type === 'attribute') {
    const attribute = ontology.attributes.find((item) => item.uri === operation.uri)
    if (!attribute) return null
    return {
      label: attribute.label,
      definition: attribute.definition,
      description: attribute.description,
      owning_class_uri: attribute.domain_class,
    }
  }

  const relationship = ontology.relationships.find((item) => item.uri === operation.uri)
  if (!relationship) return null
  return {
    label: relationship.label,
    definition: relationship.definition,
    description: relationship.description,
    source_class_uri: relationship.domain_class,
    target_class_uri: relationship.range_class,
  }
}
