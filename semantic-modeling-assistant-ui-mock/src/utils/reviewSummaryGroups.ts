import type { OntologyOperationModel } from '@/api/types'
import { buildDiffSummary, type DiffSummary } from '@/api/operations'
import type { AppliedRejectedOperation } from '@/utils/appliedReviewStorage'

type TargetGroup = {
  id: OntologyOperationModel['target_type']
  label: string
}

const TARGET_GROUPS: TargetGroup[] = [
  { id: 'class', label: 'Classes' },
  { id: 'attribute', label: 'Attributes' },
  { id: 'relationship', label: 'Relationships' },
]

export type TargetReviewSummary = {
  targetType: OntologyOperationModel['target_type']
  title: string
  kept: DiffSummary
  rejected: DiffSummary
  rejectedWithReasons: AppliedRejectedOperation[]
}

export function buildTargetReviewSummaries(
  kept: OntologyOperationModel[],
  rejected: AppliedRejectedOperation[],
): TargetReviewSummary[] {
  return TARGET_GROUPS.map((group) => {
    const keptForTarget = kept.filter((operation) => operation.target_type === group.id)
    const rejectedForTarget = rejected.filter((operation) => operation.target_type === group.id)

    return {
      targetType: group.id,
      title: group.label,
      kept: buildDiffSummary(keptForTarget),
      rejected: buildDiffSummary(rejectedForTarget),
      rejectedWithReasons: rejectedForTarget,
    }
  }).filter(
    (group) =>
      hasDiff(group.kept) ||
      hasDiff(group.rejected) ||
      group.rejectedWithReasons.some((operation) => operation.rejectionReason?.trim()),
  )
}

function hasDiff(diff: DiffSummary): boolean {
  return (
    diff.classesAdded.length > 0 ||
    diff.classesUpdated.length > 0 ||
    diff.classesDeleted.length > 0 ||
    diff.attributesAdded.length > 0 ||
    diff.attributesUpdated.length > 0 ||
    diff.attributesDeleted.length > 0 ||
    diff.relationshipsAdded.length > 0 ||
    diff.relationshipsUpdated.length > 0 ||
    diff.relationshipsDeleted.length > 0
  )
}
