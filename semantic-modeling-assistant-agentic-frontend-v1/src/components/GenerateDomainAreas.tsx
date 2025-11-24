import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { useState } from 'react'

interface GenerateDomainAreasProps {
  projectId: string
}

export function GenerateDomainAreas({ projectId }: GenerateDomainAreasProps) {
  const qc = useQueryClient()
  const [showInstructionInput, setShowInstructionInput] = useState(false)
  const [userInstruction, setUserInstruction] = useState('')

  const projectQ = useQuery({
    enabled: !!projectId,
    queryKey: ['project', projectId],
    queryFn: () => api.getProject(projectId),
  })

  const kbQ = useQuery({
    enabled: !!projectId,
    queryKey: ['kb', projectId],
    queryFn: () => api.getProjectKnowledgeBase(projectId),
  })

  const generateAreas = useMutation({
    mutationFn: (userInstruction?: string | null) => api.generateDomainAreas(projectId, userInstruction),
    onSuccess: async (areas) => {
      // Invalidate queries to refresh domain areas
      await qc.invalidateQueries({ queryKey: ['project', projectId] })
      await qc.invalidateQueries({ queryKey: ['areas', projectId] })
      console.log('Generated domain areas:', areas)
      // Reset form state
      setUserInstruction('')
      setShowInstructionInput(false)
    },
    onError: (error) => {
      console.error('Failed to generate domain areas:', error)
    },
  })

  const keyDocumentId = projectQ.data?.key_knowledge_document_id
  const hasDocuments = (kbQ.data?.legal_documents?.length ?? 0) > 0 || (kbQ.data?.expert_documents?.length ?? 0) > 0

  // Only show if key document is set and there are documents
  if (!keyDocumentId || !hasDocuments) {
    return null
  }

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-card p-4">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <h3 className="font-semibold text-blue-900 mb-1">Generate Domain Areas</h3>
          <p className="text-sm text-blue-800 mb-3">
            Key document is set. Generate domain areas to structure your knowledge domain and start the design process.
          </p>
          {showInstructionInput && (
            <div className="mb-3">
              <label className="block text-sm text-blue-900 mb-1">
                Custom instruction (optional):
              </label>
              <textarea
                className="w-full border rounded-card px-2 py-1 text-sm"
                rows={3}
                placeholder="E.g., Focus on administrative processes, Create 3-5 high-level areas..."
                value={userInstruction}
                onChange={(e) => setUserInstruction(e.target.value)}
              />
            </div>
          )}
        </div>
        <div className="flex flex-col gap-2 flex-shrink-0">
          <button
            className="px-4 py-2 bg-blue-600 text-white rounded-card hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
            onClick={() => {
              generateAreas.mutate(userInstruction || null)
            }}
            disabled={generateAreas.isPending}
          >
            {generateAreas.isPending ? 'Generating...' : '🚀 Generate Domain Areas'}
          </button>
          {!showInstructionInput && (
            <button
              className="text-xs px-2 py-1 border border-blue-300 text-blue-700 rounded-card hover:bg-blue-100"
              onClick={() => setShowInstructionInput(true)}
            >
              + Add instruction
            </button>
          )}
        </div>
      </div>
      {generateAreas.isSuccess && (
        <div className="mt-3 text-sm text-green-700 bg-green-50 border border-green-200 rounded px-3 py-2">
          ✓ Successfully generated {generateAreas.data?.length ?? 0} domain area(s)! Check the Storyboard page to see them.
        </div>
      )}
      {generateAreas.isError && (
        <div className="mt-3 text-sm text-red-700 bg-red-50 border border-red-200 rounded px-3 py-2">
          ✗ Failed to generate domain areas. Make sure the key document is set and try again.
        </div>
      )}
    </div>
  )
}
