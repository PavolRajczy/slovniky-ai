import { useProjectStore } from '@/store/projectStore'
import { useQuery } from '@tanstack/react-query'
import { api, DesignIterationModel, DesignTaskModel } from '@/lib/api'
import { useEffect, useState } from 'react'
import { Modal } from '@/components/Modal'
import { OperationsModal } from '@/components/OperationsModal'
import { useOperationsStore } from '@/store/operationsStore'
import { useOntologyChangesStore } from '@/store/ontologyChangesStore'
import { useQueryClient } from '@tanstack/react-query'
import { GenerateDomainAreas } from '@/components/GenerateDomainAreas'

export function StoryboardPage() {
  const { projectId, areaId } = useProjectStore()
  const ops = useOperationsStore()
  const qc = useQueryClient()
  const [openSuggest, setOpenSuggest] = useState(false)
  const [suggestCount, setSuggestCount] = useState(3)
  const [selectedAreaForSuggest, setSelectedAreaForSuggest] = useState<string | ''>('')
  const [viewingTasks, setViewingTasks] = useState<string | null>(null)
  const [viewingOperations, setViewingOperations] = useState<string | null>(null)
  const [expandedIteration, setExpandedIteration] = useState<string | null>(null)
  
  // Use global loading states from operationsStore
  const { planningTasks, preparingIteration, applyingIteration, suggestingIterations, autopilotRunning } = ops
  
  // Helper function to get user-friendly status labels
  const getTaskStatusLabel = (status: string) => {
    const statusLabels: Record<string, string> = {
      planned: 'Planned',
      generating: 'Generating',
      completed: 'Completed',
    }
    return statusLabels[status] || status
  }
  
  const getIterationStatusLabel = (status: string) => {
    const statusLabels: Record<string, string> = {
      suggested: 'Suggested',
      planned: 'Tasks Planned',
      prepared: 'Ready to Apply',
      completed: 'Completed',
    }
    return statusLabels[status] || status
  }
  
  // Helper function to get status badge styling
  const getIterationStatusBadge = (status: string) => {
    const statusStyles: Record<string, { color: string; icon: string }> = {
      suggested: { color: 'bg-gray-100 text-gray-700', icon: '�' },
      planned: { color: 'bg-blue-100 text-blue-700', icon: '📋' },
      prepared: { color: 'bg-green-100 text-green-700', icon: '✓' },
      completed: { color: 'bg-green-100 text-green-800', icon: '✓' },
    }
    return statusStyles[status] || { color: 'bg-gray-100 text-gray-700', icon: '•' }
  }
  
  const areasQ = useQuery({
    enabled: !!projectId,
    queryKey: ['areas', projectId],
    queryFn: () => api.listAreas(projectId!),
  })
  const iterationsQ = useQuery({
    enabled: !!projectId,
    queryKey: ['iterations', projectId, areaId],
    queryFn: () => api.listIterations(projectId!, areaId ?? undefined),
  })

  // Query for viewing tasks of a specific iteration
  const tasksQ = useQuery({
    enabled: !!projectId && !!viewingTasks,
    queryKey: ['tasks', projectId, viewingTasks],
    queryFn: () => api.listTasks(projectId!, viewingTasks!),
  })

  if (!projectId) return <div>Select a project to view the storyboard.</div>

  // Separate iterations into suggested (no tasks) and planned (with tasks)
  const suggestedIterations = iterationsQ.data?.planned_iterations.filter(it => it.status === 'suggested') ?? []
  const plannedIterations = iterationsQ.data?.planned_iterations.filter(it => (it.planned_tasks_count ?? 0) > 0) ?? []
  
  // Get prepared iterations (current_iteration with status 'prepared')
  const preparedIterations = iterationsQ.data?.current_iteration?.status === 'prepared' 
    ? [iterationsQ.data.current_iteration] 
    : []
  
  const completedIterations = iterationsQ.data?.finished_iterations ?? []

  const handlePlanTasks = async (iterationId: string) => {
    if (!projectId) return
    ops.setPlanningTasks(iterationId)
    try {
      await api.planTasks(projectId, iterationId)
      await qc.invalidateQueries({ queryKey: ['iterations', projectId, areaId] })
      ops.setPlanningTasks(null)
    } catch (error) {
      console.error('Failed to plan tasks:', error)
      ops.setPlanningTasks(null)
    }
  }

  const handleApplyIteration = async (iterationId: string) => {
    if (!projectId) return
    ops.setApplyingIteration(iterationId)
    const changesStore = useOntologyChangesStore.getState()
    try {
      // Check if we have client-filtered operations
      const cachedOps = ops.operationsCache[iterationId]
      
      // Apply with filtered operations if available, otherwise use server-side ops
      await api.applyIteration(projectId, iterationId, cachedOps)
      
      // Record the changes for highlighting in ontology view
      if (cachedOps && cachedOps.length > 0) {
        changesStore.recordChanges(iterationId, cachedOps)
      }
      
      // Invalidate ontology query to refetch the updated ontology
      await qc.invalidateQueries({ queryKey: ['ontology', projectId] })
      await qc.invalidateQueries({ queryKey: ['iterations', projectId, areaId] })
      
      // Clear the drawer if it's open for this iteration
      if (ops.iterationId === iterationId) {
        ops.close()
        ops.clear()
      }
      
      ops.setApplyingIteration(null)
    } catch (error) {
      console.error('Failed to apply iteration:', error)
      alert('Failed to apply iteration. Please try again.')
      ops.setApplyingIteration(null)
    }
  }

  const handleAutopilot = async (iterationId: string) => {
    if (!projectId) return
    
    ops.setAutopilotRunning(iterationId)
    const changesStore = useOntologyChangesStore.getState()
    
    try {
      // Step 1: Plan Tasks
      ops.setPlanningTasks(iterationId)
      await api.planTasks(projectId, iterationId)
      await qc.invalidateQueries({ queryKey: ['iterations', projectId, areaId] })
      ops.setPlanningTasks(null)
      
      // Step 2: Prepare Iteration
      ops.setPreparingIteration(iterationId)
      const prepared = await api.prepareIteration(projectId, iterationId)
      ops.open(prepared.iteration_id, prepared.operations)
      await qc.invalidateQueries({ queryKey: ['iterations', projectId, areaId] })
      ops.setPreparingIteration(null)
      
      // Step 3: Apply Iteration
      ops.setApplyingIteration(iterationId)
      const cachedOps = ops.operationsCache[iterationId]
      await api.applyIteration(projectId, iterationId, cachedOps)
      
      // Record the changes for highlighting in ontology view
      if (cachedOps && cachedOps.length > 0) {
        changesStore.recordChanges(iterationId, cachedOps)
      }
      
      // Invalidate ontology query to refetch the updated ontology
      await qc.invalidateQueries({ queryKey: ['ontology', projectId] })
      await qc.invalidateQueries({ queryKey: ['iterations', projectId, areaId] })
      
      // Clear the drawer if it's open for this iteration
      if (ops.iterationId === iterationId) {
        ops.close()
        ops.clear()
      }
      
      ops.setApplyingIteration(null)
      ops.setAutopilotRunning(null)
    } catch (error) {
      console.error('Autopilot failed:', error)
      alert(`Autopilot failed: ${error instanceof Error ? error.message : 'Unknown error'}. Please check the iteration status and try again.`)
      ops.setPlanningTasks(null)
      ops.setPreparingIteration(null)
      ops.setApplyingIteration(null)
      ops.setAutopilotRunning(null)
    }
  }

  const hasAreas = (areasQ.data?.length ?? 0) > 0

  return (
    <div className="space-y-4">
      {/* Show Generate Domain Areas if no areas exist */}
      {!hasAreas && <GenerateDomainAreas projectId={projectId} />}
      
      {/* Show area selector and iterations only if areas exist */}
      {hasAreas && (
        <>
          <div className="flex items-center gap-2">
            <select
              className="border rounded-card px-2 py-1"
              value={areaId ?? ''}
              onChange={(e) => useProjectStore.setState({ areaId: e.target.value || null })}
            >
              <option value="">All Areas</option>
              {areasQ.data?.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.label}
                </option>
              ))}
            </select>
            <button className="px-3 py-1 bg-ai text-white rounded-card" onClick={() => setOpenSuggest(true)}>
              ✨ Suggest Iterations
            </button>
          </div>
          <div className="grid grid-cols-4 gap-4">
        {/* Suggested Column */}
        <div className="bg-white rounded-card border p-3">
          <div className="font-semibold mb-2">Suggested</div>
          <div className="text-xs text-gray-500 mb-2">AI or user suggested, no tasks yet</div>
          <div className="space-y-2">
            {suggestedIterations.map((it) => {
              const statusBadge = getIterationStatusBadge(it.status)
              return (
                <div key={it.id} className="border rounded-card p-2 space-y-2">
                  <div className="flex items-start justify-between gap-2">
                    <div 
                      className="font-medium cursor-pointer hover:text-blue-600 flex-1"
                      onClick={() => setExpandedIteration(expandedIteration === it.id ? null : it.id)}
                    >
                      {it.name}
                    </div>
                    <span className={`text-xs px-2 py-0.5 rounded ${statusBadge.color}`}>
                      {statusBadge.icon} {getIterationStatusLabel(it.status)}
                    </span>
                  </div>
                  <div 
                    className={`text-xs text-gray-600 cursor-pointer ${expandedIteration === it.id ? '' : 'line-clamp-2'}`}
                    onClick={() => setExpandedIteration(expandedIteration === it.id ? null : it.id)}
                  >
                    {it.specification}
                  </div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <button
                      className="text-xs px-2 py-1 bg-ai text-white rounded-card disabled:opacity-50"
                      onClick={() => handlePlanTasks(it.id)}
                      disabled={!!planningTasks || !!autopilotRunning}
                    >
                      {planningTasks === it.id ? '⏳ Planning...' : '✨ Plan Tasks'}
                    </button>
                    <button
                      className="text-xs px-2 py-1 bg-purple-600 text-white rounded-card disabled:opacity-50 disabled:cursor-not-allowed"
                      onClick={() => handleAutopilot(it.id)}
                      disabled={!!autopilotRunning || !!planningTasks || !!preparingIteration || !!applyingIteration}
                      title="Automatically execute Plan Tasks, Prepare, and Apply"
                    >
                      {autopilotRunning === it.id ? '🤖 Running...' : '🤖 Autopilot'}
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Planned Column */}
        <div className="bg-white rounded-card border p-3">
          <div className="font-semibold mb-2">Planned</div>
          <div className="text-xs text-gray-500 mb-2">With planned tasks</div>
          <div className="space-y-2">
            {plannedIterations.map((it) => {
              const statusBadge = getIterationStatusBadge(it.status)
              return (
                <div key={it.id} className="border rounded-card p-2 space-y-2">
                  <div className="flex items-start justify-between gap-2">
                    <div 
                      className="font-medium cursor-pointer hover:text-blue-600 flex-1"
                      onClick={() => setExpandedIteration(expandedIteration === it.id ? null : it.id)}
                    >
                      {it.name}
                    </div>
                    <span className={`text-xs px-2 py-0.5 rounded ${statusBadge.color}`}>
                      {statusBadge.icon} {getIterationStatusLabel(it.status)}
                    </span>
                  </div>
                  <div 
                    className={`text-xs text-gray-600 cursor-pointer ${expandedIteration === it.id ? '' : 'line-clamp-2'}`}
                    onClick={() => setExpandedIteration(expandedIteration === it.id ? null : it.id)}
                  >
                    {it.specification}
                  </div>
                  <div className="text-xs text-gray-500">Tasks: {it.planned_tasks_count}</div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <button
                      className="text-xs px-2 py-1 border rounded-card"
                      onClick={() => setViewingTasks(it.id)}
                    >
                      View Tasks
                    </button>
                    <button
                      className="text-xs px-2 py-1 bg-primary-600 text-white rounded-card disabled:opacity-50 disabled:cursor-not-allowed"
                      onClick={async () => {
                        if (!projectId) return
                        ops.setPreparingIteration(it.id)
                        try {
                          const prepared = await api.prepareIteration(projectId, it.id)
                          ops.open(prepared.iteration_id, prepared.operations)
                          await qc.invalidateQueries({ queryKey: ['iterations', projectId, areaId] })
                        } catch (error) {
                          console.error('Failed to prepare iteration:', error)
                          alert('Failed to prepare iteration. Please try again.')
                        } finally {
                          ops.setPreparingIteration(null)
                        }
                      }}
                      disabled={preparingIteration === it.id}
                    >
                      {preparingIteration === it.id ? '⏳ Preparing...' : 'Prepare ▶'}
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Prepared Column */}
        <div className="bg-white rounded-card border p-3">
          <div className="font-semibold mb-2">Prepared</div>
          <div className="text-xs text-gray-500 mb-2">Ready to apply</div>
          <div className="space-y-2">
            {preparedIterations.map((it) => {
              const statusBadge = getIterationStatusBadge(it.status)
              return (
                <div key={it.id} className="border rounded-card p-2 space-y-2">
                  <div className="flex items-start justify-between gap-2">
                    <div 
                      className="font-medium cursor-pointer hover:text-blue-600 flex-1"
                      onClick={() => setExpandedIteration(expandedIteration === it.id ? null : it.id)}
                    >
                      {it.name}
                    </div>
                    <span className={`text-xs px-2 py-0.5 rounded ${statusBadge.color}`}>
                      {statusBadge.icon} {getIterationStatusLabel(it.status)}
                    </span>
                  </div>
                  <div 
                    className={`text-xs text-gray-600 cursor-pointer ${expandedIteration === it.id ? '' : 'line-clamp-2'}`}
                    onClick={() => setExpandedIteration(expandedIteration === it.id ? null : it.id)}
                  >
                    {it.specification}
                  </div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <button
                      className="text-xs px-2 py-1 border rounded-card"
                      onClick={async () => {
                        if (!projectId) return
                        // Check if we have cached operations for this iteration
                        const cachedOps = ops.operationsCache[it.id]
                        if (cachedOps && cachedOps.length > 0) {
                          // Use cached operations and show modal
                          ops.open(it.id, cachedOps)
                          setViewingOperations(it.id)
                        } else {
                          // Fetch operations from backend using GET endpoint (not prepare)
                          try {
                            const result = await api.getIterationOperations(projectId, it.id)
                            ops.open(it.id, result.operations)
                            setViewingOperations(it.id)
                          } catch (error) {
                            console.error('Failed to get operations:', error)
                            alert('Failed to load operations. Please try again.')
                          }
                        }
                      }}
                    >
                      View Operations
                    </button>
                    <button
                      className="text-xs px-2 py-1 bg-success text-white rounded-card disabled:opacity-50"
                      onClick={() => handleApplyIteration(it.id)}
                      disabled={applyingIteration === it.id}
                    >
                      {applyingIteration === it.id ? '⚡ Applying...' : 'Apply Changes'}
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Completed Column */}
        <div className="bg-white rounded-card border p-3">
          <div className="font-semibold mb-2">Completed</div>
          <div className="text-xs text-gray-500 mb-2">Applied to ontology</div>
          <div className="space-y-2">
            {completedIterations.map((it) => {
              const statusBadge = getIterationStatusBadge(it.status)
              return (
                <div key={it.id} className="border rounded-card p-2 space-y-2">
                  <div className="flex items-start justify-between gap-2">
                    <div 
                      className="font-medium cursor-pointer hover:text-blue-600 flex-1"
                      onClick={() => setExpandedIteration(expandedIteration === it.id ? null : it.id)}
                    >
                      {it.name}
                    </div>
                    <span className={`text-xs px-2 py-0.5 rounded ${statusBadge.color}`}>
                      {statusBadge.icon} {getIterationStatusLabel(it.status)}
                    </span>
                  </div>
                  <div 
                    className={`text-xs text-gray-600 cursor-pointer ${expandedIteration === it.id ? '' : 'line-clamp-2'}`}
                    onClick={() => setExpandedIteration(expandedIteration === it.id ? null : it.id)}
                  >
                    {it.specification}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* View Tasks Modal */}
      {viewingTasks && (
        <Modal 
          title="Iteration Tasks" 
          onClose={() => setViewingTasks(null)}
        >
          <div className="space-y-3">
            {tasksQ.isLoading ? (
              <div className="text-center py-4">Loading tasks...</div>
            ) : tasksQ.data ? (
              <>
                <div className="text-sm text-gray-600 mb-2">
                  Planned: {tasksQ.data.planned_tasks?.length ?? 0} | 
                  In Progress: {tasksQ.data.current_task ? 1 : 0} | 
                  Finished: {tasksQ.data.finished_tasks?.length ?? 0}
                </div>
                
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {tasksQ.data.planned_tasks?.map((task: DesignTaskModel) => (
                    <div key={task.id} className="border rounded-card p-3">
                      <div className="font-medium">{task.name}</div>
                      <div className="text-xs text-gray-600 mt-1">{task.specification}</div>
                      <div className="text-xs text-gray-500 mt-1">Status: {getTaskStatusLabel(task.status)}</div>
                    </div>
                  ))}
                  {tasksQ.data.current_task && (
                    <div key={tasksQ.data.current_task.id} className="border rounded-card p-3 bg-blue-50">
                      <div className="font-medium">{tasksQ.data.current_task.name}</div>
                      <div className="text-xs text-gray-600 mt-1">{tasksQ.data.current_task.specification}</div>
                      <div className="text-xs text-blue-600 mt-1">Status: {getTaskStatusLabel(tasksQ.data.current_task.status)}</div>
                    </div>
                  )}
                  {tasksQ.data.finished_tasks?.map((task: DesignTaskModel) => (
                    <div key={task.id} className="border rounded-card p-3 bg-green-50">
                      <div className="font-medium">{task.name}</div>
                      <div className="text-xs text-gray-600 mt-1">{task.specification}</div>
                      <div className="text-xs text-green-600 mt-1">Status: {getTaskStatusLabel(task.status)}</div>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div className="text-center py-4 text-gray-500">No tasks found</div>
            )}
          </div>
        </Modal>
      )}

      {/* View Operations Modal */}
      {viewingOperations && (
        <OperationsModal
          iterationId={viewingOperations}
          operations={ops.operationsCache[viewingOperations] ?? []}
          onClose={() => setViewingOperations(null)}
        />
      )}

      {openSuggest && (
        <Modal title="Suggest Iterations" onClose={() => setOpenSuggest(false)}>
          <div className="space-y-3">
            <label className="block text-sm">Focused Area</label>
            <select
              className="border rounded-card px-2 py-1 w-full"
              value={selectedAreaForSuggest}
              onChange={(e) => setSelectedAreaForSuggest(e.target.value)}
            >
              {areasQ.data?.map((a: any) => (
                <option key={a.id} value={a.id}>
                  {a.label}
                </option>
              ))}
            </select>
            <label className="block text-sm">Count</label>
            <input
              type="number"
              min={1}
              max={20}
              className="border rounded-card px-2 py-1 w-24"
              value={suggestCount}
              onChange={(e) => setSuggestCount(Number(e.target.value))}
            />
            <div className="flex justify-end gap-2">
              <button className="px-3 py-1" onClick={() => setOpenSuggest(false)}>Cancel</button>
              <button
                className="px-3 py-1 bg-ai text-white rounded-card disabled:opacity-50"
                disabled={suggestingIterations}
                onClick={async () => {
                  if (!projectId) return
                  const focused = selectedAreaForSuggest || areaId
                  if (!focused) return
                  
                  ops.setSuggestingIterations(true)
                  try {
                    await api.suggestIterations(projectId, { focused_area_id: focused, count: suggestCount })
                    await qc.invalidateQueries({ queryKey: ['iterations', projectId] })
                    setOpenSuggest(false)
                  } catch (error) {
                    console.error('Failed to suggest iterations:', error)
                  } finally {
                    ops.setSuggestingIterations(false)
                  }
                }}
              >
                {suggestingIterations ? '⏳ Suggesting...' : '✨ Suggest'}
              </button>
            </div>
          </div>
        </Modal>
      )}
      </>
      )}
    </div>
  )
}
