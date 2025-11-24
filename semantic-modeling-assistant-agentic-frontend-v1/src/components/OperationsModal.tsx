import { Modal } from './Modal'
import { OntologyOperationModel } from '@/lib/api'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { useProjectStore } from '@/store/projectStore'
import { useOperationsStore } from '@/store/operationsStore'

interface OperationsModalProps {
  onClose: () => void
  iterationId: string
  operations: OntologyOperationModel[]
}

export function OperationsModal({ onClose, iterationId, operations }: OperationsModalProps) {
  const queryClient = useQueryClient()
  const { projectId } = useProjectStore()
  const ops = useOperationsStore()

  const applyMutation = useMutation({
    mutationFn: async () => {
      if (!projectId) throw new Error('Project not selected')
      return api.applyIteration(projectId, iterationId, operations)
    },
    onSuccess: async () => {
      // Invalidate iterations query to refresh the storyboard
      await queryClient.invalidateQueries({ queryKey: ['iterations', projectId] })
      
      // Clear the operations cache for this iteration
      if (ops.iterationId === iterationId) {
        ops.close()
        ops.clear()
      }
      
      onClose()
    },
  })

  const handleApply = () => {
    applyMutation.mutate()
  }

  const getOperationLabel = (op: OntologyOperationModel) => {
    const action = op.operation_type === 'create' ? 'Add' : op.operation_type === 'delete' ? 'Remove' : 'Modify'
    const target = op.target_type.charAt(0).toUpperCase() + op.target_type.slice(1)
    return `${action} ${target}`
  }

  const getBadgeColor = (opType: 'create' | 'update' | 'delete') => {
    if (opType === 'create') return 'bg-green-100 text-green-800'
    if (opType === 'delete') return 'bg-red-100 text-red-800'
    if (opType === 'update') return 'bg-blue-100 text-blue-800'
    return 'bg-gray-100 text-gray-800'
  }

  return (
    <Modal onClose={onClose} title="Operations">
      <div className="space-y-4">
        {operations.length === 0 ? (
          <div className="text-center text-gray-500 py-4">No operations to display</div>
        ) : (
          <>
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {operations.map((op, idx) => (
                <div key={idx} className="border rounded-card p-3 bg-gray-50">
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <span
                      className={`px-2 py-1 rounded text-xs font-medium ${getBadgeColor(op.operation_type)}`}
                    >
                      {getOperationLabel(op)}
                    </span>
                    {op.uri && (
                      <code className="text-xs text-gray-600 bg-white px-2 py-1 rounded border flex-1 truncate">
                        {op.uri}
                      </code>
                    )}
                  </div>

                  {op.label && (
                    <div className="mb-1">
                      <span className="text-sm font-semibold text-gray-800">{op.label}</span>
                    </div>
                  )}

                  {op.definition && (
                    <div className="mb-1">
                      <span className="text-xs text-gray-500">Definition: </span>
                      <span className="text-sm text-gray-700">{op.definition}</span>
                    </div>
                  )}

                  {op.description && (
                    <div className="mb-1">
                      <span className="text-xs text-gray-500">Description: </span>
                      <span className="text-sm text-gray-700">{op.description}</span>
                    </div>
                  )}

                  {/* Class-specific fields */}
                  {op.target_type === 'class' && op.generalization_uris && op.generalization_uris.length > 0 && (
                    <div className="mb-1">
                      <span className="text-xs text-gray-500">Generalizations: </span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {op.generalization_uris.map((uri, i) => (
                          <code key={i} className="text-xs text-gray-700 bg-white px-1 rounded border">{uri}</code>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Attribute-specific fields */}
                  {op.target_type === 'attribute' && (
                    <>
                      {op.owning_class_uri && (
                        <div className="mb-1">
                          <span className="text-xs text-gray-500">Domain: </span>
                          <code className="text-xs text-gray-700 bg-white px-1 rounded">{op.owning_class_uri}</code>
                        </div>
                      )}
                      {op.kind && (
                        <div className="mb-1">
                          <span className="text-xs text-gray-500">Kind: </span>
                          <span className="text-sm text-gray-700">{op.kind}</span>
                        </div>
                      )}
                    </>
                  )}

                  {/* Relationship-specific fields */}
                  {op.target_type === 'relationship' && (
                    <>
                      {op.source_class_uri && (
                        <div className="mb-1">
                          <span className="text-xs text-gray-500">Source: </span>
                          <code className="text-xs text-gray-700 bg-white px-1 rounded">{op.source_class_uri}</code>
                        </div>
                      )}
                      {op.target_class_uri && (
                        <div className="mb-1">
                          <span className="text-xs text-gray-500">Target: </span>
                          <code className="text-xs text-gray-700 bg-white px-1 rounded">{op.target_class_uri}</code>
                        </div>
                      )}
                    </>
                  )}

                  {/* References */}
                  {op.definition_references && op.definition_references.length > 0 && (
                    <div className="mb-1">
                      <span className="text-xs text-gray-500">Definition Refs: </span>
                      <span className="text-sm text-gray-700">{op.definition_references.join(', ')}</span>
                    </div>
                  )}

                  {op.specification_references && op.specification_references.length > 0 && (
                    <div className="mb-1">
                      <span className="text-xs text-gray-500">Spec Refs: </span>
                      <span className="text-sm text-gray-700">{op.specification_references.join(', ')}</span>
                    </div>
                  )}

                  {op.references && op.references.length > 0 && (
                    <div className="mb-1">
                      <span className="text-xs text-gray-500">References: </span>
                      <span className="text-sm text-gray-700">{op.references.join(', ')}</span>
                    </div>
                  )}
                </div>
              ))}
            </div>

            <div className="flex gap-2 pt-4 border-t">
              <button
                onClick={handleApply}
                disabled={applyMutation.isPending}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {applyMutation.isPending ? 'Applying...' : 'Apply Changes'}
              </button>
              <button
                onClick={onClose}
                disabled={applyMutation.isPending}
                className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300 disabled:opacity-50"
              >
                Cancel
              </button>
            </div>

            {applyMutation.isError && (
              <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-800">
                Error applying changes: {(applyMutation.error as Error).message}
              </div>
            )}
          </>
        )}
      </div>
    </Modal>
  )
}
