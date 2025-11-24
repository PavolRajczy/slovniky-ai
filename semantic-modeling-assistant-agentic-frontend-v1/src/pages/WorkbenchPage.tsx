import { useProjectStore } from '@/store/projectStore'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api, KnowledgeDomainAreaModel, DesignIterationModel } from '@/lib/api'
import { useState } from 'react'
import { Modal } from '@/components/Modal'
import { useOperationsStore } from '@/store/operationsStore'
import { useOntologyChangesStore } from '@/store/ontologyChangesStore'

// Helper function for iteration status badges (like Storyboard)
function getIterationStatusBadge(status: string) {
  const statusStyles: Record<string, { color: string; icon: string; label: string }> = {
    suggested: { color: 'bg-gray-100 text-gray-700', icon: '💡', label: 'Suggested' },
    planned: { color: 'bg-blue-100 text-blue-700', icon: '📋', label: 'Tasks Planned' },
    prepared: { color: 'bg-green-100 text-green-700', icon: '✓', label: 'Ready to Apply' },
    completed: { color: 'bg-green-100 text-green-800', icon: '✓', label: 'Completed' },
  }
  return statusStyles[status] || { color: 'bg-gray-100 text-gray-700', icon: '•', label: status }
}

// Area Edit Form Component
function AreaEditForm({ area, projectId, allAreas, onCancel }: { 
  area: KnowledgeDomainAreaModel
  projectId: string
  allAreas: KnowledgeDomainAreaModel[]
  onCancel: () => void
}) {
  const qc = useQueryClient()
  const [label, setLabel] = useState(area.label)
  const [description, setDescription] = useState(area.description)
  const [parentId, setParentId] = useState(area.parent_id || '')
  const [keyConcepts, setKeyConcepts] = useState((area.key_concepts || []).join(', '))
  
  const updateMut = useMutation({
    mutationFn: () => api.updateArea(projectId, area.id, {
      label,
      description,
      parent_id: parentId || null,
      key_concepts: keyConcepts ? keyConcepts.split(',').map(k => k.trim()) : []
    }),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ['areas', projectId] })
      await qc.invalidateQueries({ queryKey: ['area', projectId, area.id] })
      onCancel() // Return to detail view after save
    }
  })
  
  const deleteMut = useMutation({
    mutationFn: () => api.deleteArea(projectId, area.id),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ['areas', projectId] })
      useProjectStore.setState({ areaId: null })
    }
  })
  
  const availableParents = allAreas.filter(a => a.id !== area.id)
  
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">Edit Area</h2>
      </div>
      
      <div>
        <label className="block text-sm font-medium mb-1">Label</label>
        <input
          type="text"
          className="w-full border rounded-card px-3 py-2"
          value={label}
          onChange={(e) => setLabel(e.target.value)}
        />
      </div>
      
      <div>
        <label className="block text-sm font-medium mb-1">Description</label>
        <textarea
          className="w-full border rounded-card px-3 py-2"
          rows={4}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
      </div>
      
      <div>
        <label className="block text-sm font-medium mb-1">Parent Area</label>
        <select
          className="w-full border rounded-card px-3 py-2"
          value={parentId}
          onChange={(e) => setParentId(e.target.value)}
        >
          <option value="">None (Top-level)</option>
          {availableParents.map(a => (
            <option key={a.id} value={a.id}>{a.label}</option>
          ))}
        </select>
      </div>
      
      <div>
        <label className="block text-sm font-medium mb-1">Key Concepts (comma-separated)</label>
        <input
          type="text"
          className="w-full border rounded-card px-3 py-2"
          value={keyConcepts}
          onChange={(e) => setKeyConcepts(e.target.value)}
          placeholder="concept1, concept2, concept3"
        />
      </div>
      
      <div className="flex gap-2">
        <button
          className="px-4 py-2 bg-primary-600 text-white rounded-card hover:bg-primary-700 disabled:opacity-50"
          onClick={() => updateMut.mutate()}
          disabled={updateMut.isPending}
        >
          {updateMut.isPending ? 'Saving...' : 'Save'}
        </button>
        <button
          className="px-4 py-2 border rounded-card hover:bg-gray-50"
          onClick={onCancel}
        >
          Cancel
        </button>
        <button
          className="px-4 py-2 border border-red-300 text-red-600 rounded-card hover:bg-red-50 disabled:opacity-50 ml-auto"
          onClick={() => {
            if (window.confirm('Are you sure you want to delete this area?')) {
              deleteMut.mutate()
            }
          }}
          disabled={deleteMut.isPending}
        >
          Delete
        </button>
      </div>
      
      {updateMut.isError && (
        <div className="text-sm text-red-600">✗ Failed to save area</div>
      )}
    </div>
  )
}

// Area Detail View Component (Read-only)
function AreaDetailView({ area, projectId, allAreas, onEdit }: {
  area: KnowledgeDomainAreaModel
  projectId: string
  allAreas: KnowledgeDomainAreaModel[]
  onEdit: () => void
}) {
  const qc = useQueryClient()
  const [reidentifyPrompt, setReidentifyPrompt] = useState('')
  const [showReidentify, setShowReidentify] = useState(false)
  
  const reidentifyMut = useMutation({
    mutationFn: () => api.reidentifyAreas(projectId, reidentifyPrompt),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ['areas', projectId] })
      setReidentifyPrompt('')
      setShowReidentify(false)
    }
  })
  
  const parentArea = area.parent_id ? allAreas.find(a => a.id === area.parent_id) : null
  
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">{area.label}</h2>
        <button
          className="px-3 py-2 border rounded-card hover:bg-gray-50"
          onClick={onEdit}
        >
          ✏️ Edit
        </button>
      </div>
      
      <div>
        <div className="text-sm font-medium text-gray-600 mb-1">Description</div>
        <p className="text-gray-800">{area.description}</p>
      </div>
      
      {parentArea && (
        <div>
          <div className="text-sm font-medium text-gray-600 mb-1">Parent Area</div>
          <p className="text-gray-800">{parentArea.label}</p>
        </div>
      )}
      
      {area.key_concepts && area.key_concepts.length > 0 && (
        <div>
          <div className="text-sm font-medium text-gray-600 mb-1">Key Concepts</div>
          <div className="flex flex-wrap gap-2">
            {area.key_concepts.map((concept, idx) => (
              <span
                key={idx}
                className="px-2 py-1 bg-blue-50 text-blue-700 rounded text-sm"
              >
                {concept}
              </span>
            ))}
          </div>
        </div>
      )}
      
      {/* Refine Area Scope Section */}
      <div className="border-t pt-4 mt-4">
        <button
          className="px-3 py-2 bg-ai text-white rounded-card hover:opacity-90"
          onClick={() => setShowReidentify(!showReidentify)}
          title="Use AI to refine this area's definition and potentially split or merge areas"
        >
          ✨ Refine Area Scope
        </button>
        <p className="text-xs text-gray-500 mt-2">
          Use AI to refine this area's definition and potentially restructure related areas
        </p>
        
        {showReidentify && (
          <div className="mt-3 space-y-2">
            <label className="block text-sm font-medium">Instructions for refinement</label>
            <textarea
              className="w-full border rounded-card px-3 py-2"
              rows={3}
              placeholder="E.g., Split this area into two parts, Merge with another area, Focus on specific aspects..."
              value={reidentifyPrompt}
              onChange={(e) => setReidentifyPrompt(e.target.value)}
            />
            <div className="flex gap-2">
              <button
                className="px-3 py-2 bg-primary-600 text-white rounded-card hover:bg-primary-700 disabled:opacity-50"
                onClick={() => reidentifyMut.mutate()}
                disabled={reidentifyMut.isPending || !reidentifyPrompt.trim()}
              >
                {reidentifyMut.isPending ? 'Processing...' : 'Apply Refinement'}
              </button>
              <button
                className="px-3 py-2 border rounded-card hover:bg-gray-50"
                onClick={() => {
                  setShowReidentify(false)
                  setReidentifyPrompt('')
                }}
              >
                Cancel
              </button>
            </div>
            {reidentifyMut.isSuccess && (
              <div className="text-sm text-green-600">✓ Areas refined successfully</div>
            )}
            {reidentifyMut.isError && (
              <div className="text-sm text-red-600">✗ Failed to refine areas</div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

// Iteration Edit Form Component
function IterationEditForm({ iteration, projectId, areas, onViewTasks, onViewOperations }: {
  iteration: DesignIterationModel
  projectId: string
  areas: KnowledgeDomainAreaModel[]
  onViewTasks: () => void
  onViewOperations: () => void
}) {
  const qc = useQueryClient()
  const ops = useOperationsStore()
  const { setIterationId } = useProjectStore()
  const [name, setName] = useState(iteration.name)
  const [specification, setSpecification] = useState(iteration.specification)
  const [focusedAreaId, setFocusedAreaId] = useState(iteration.focused_area_id)
  
  const updateMut = useMutation({
    mutationFn: () => api.updateIteration(projectId, iteration.id, {
      name,
      specification,
      focused_area_id: focusedAreaId
    }),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ['iterations', projectId] })
      await qc.invalidateQueries({ queryKey: ['iteration', projectId, iteration.id] })
    }
  })

  const deleteMut = useMutation({
    mutationFn: () => api.deleteIteration(projectId, iteration.id),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ['iterations', projectId] })
      // Clear the selection after deletion
      setIterationId(null)
    }
  })

  const handleDelete = () => {
    if (window.confirm(`Are you sure you want to delete the iteration "${iteration.name}"? This action cannot be undone.`)) {
      deleteMut.mutate()
    }
  }

  const handlePrepareIteration = async () => {
    ops.setPreparingIteration(iteration.id)
    try {
      const prepared = await api.prepareIteration(projectId, iteration.id)
      ops.open(prepared.iteration_id, prepared.operations)
      await qc.invalidateQueries({ queryKey: ['iterations', projectId] })
      await qc.invalidateQueries({ queryKey: ['iteration', projectId, iteration.id] })
      // Switch to operations view after preparing
      onViewOperations()
    } catch (error) {
      console.error('Failed to prepare iteration:', error)
      alert('Failed to prepare iteration. Please try again.')
    } finally {
      ops.setPreparingIteration(null)
    }
  }

  const handleApplyIteration = async () => {
    ops.setApplyingIteration(iteration.id)
    const changesStore = useOntologyChangesStore.getState()
    try {
      // Check if we have cached operations for this iteration
      const cachedOps = ops.operationsCache[iteration.id]
      
      // Apply with filtered operations if available, otherwise use server-side ops
      await api.applyIteration(projectId, iteration.id, cachedOps)
      
      // Record the changes for highlighting in ontology view
      if (cachedOps && cachedOps.length > 0) {
        changesStore.recordChanges(iteration.id, cachedOps)
      }
      
      // Invalidate ontology query to refetch the updated ontology
      await qc.invalidateQueries({ queryKey: ['ontology', projectId] })
      await qc.invalidateQueries({ queryKey: ['iterations', projectId] })
      await qc.invalidateQueries({ queryKey: ['iteration', projectId, iteration.id] })
      
      // Clear the drawer if it's open for this iteration
      if (ops.iterationId === iteration.id) {
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

  const canDelete = iteration.status === 'suggested' || iteration.status === 'planned' || iteration.status === 'prepared'
  const canPrepare = iteration.status === 'planned'
  const canApply = iteration.status === 'prepared'
  const isPreparingThis = ops.preparingIteration === iteration.id
  const isApplyingThis = ops.applyingIteration === iteration.id
  
  const focusedArea = areas.find(a => a.id === focusedAreaId)
  const badge = getIterationStatusBadge(iteration.status)
  
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">{iteration.name}</h2>
        <span className={`px-2 py-1 rounded text-sm ${badge.color}`}>
          {badge.icon} {badge.label}
        </span>
      </div>
      
      <div>
        <label className="block text-sm font-medium mb-1">Name</label>
        <input
          type="text"
          className="w-full border rounded-card px-3 py-2"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
      </div>
      
      <div>
        <label className="block text-sm font-medium mb-1">Focused Area</label>
        <select
          className="w-full border rounded-card px-3 py-2"
          value={focusedAreaId}
          onChange={(e) => setFocusedAreaId(e.target.value)}
        >
          {areas.map(a => (
            <option key={a.id} value={a.id}>{a.label}</option>
          ))}
        </select>
        {focusedArea && (
          <p className="text-sm text-gray-600 mt-1">{focusedArea.description}</p>
        )}
      </div>
      
      <div>
        <label className="block text-sm font-medium mb-1">Specification</label>
        <textarea
          className="w-full border rounded-card px-3 py-2"
          rows={6}
          value={specification}
          onChange={(e) => setSpecification(e.target.value)}
        />
      </div>
      
      <div className="flex gap-2 items-center">
        <button
          className="px-4 py-2 bg-primary-600 text-white rounded-card hover:bg-primary-700 disabled:opacity-50"
          onClick={() => updateMut.mutate()}
          disabled={updateMut.isPending}
        >
          {updateMut.isPending ? 'Saving...' : 'Save'}
        </button>
        {iteration.status === 'prepared' ? (
          <button
            className="px-4 py-2 border rounded-card hover:bg-gray-50"
            onClick={onViewOperations}
          >
            View Operations →
          </button>
        ) : (
          <button
            className="px-4 py-2 border rounded-card hover:bg-gray-50"
            onClick={onViewTasks}
          >
            📋 Switch to Tasks View →
          </button>
        )}
        {canPrepare && (
          <button
            className="px-4 py-2 bg-green-600 text-white rounded-card hover:bg-green-700 disabled:opacity-50"
            onClick={handlePrepareIteration}
            disabled={isPreparingThis}
          >
            {isPreparingThis ? '⏳ Preparing...' : 'Prepare ▶'}
          </button>
        )}
        {canApply && (
          <button
            className="px-4 py-2 bg-success text-white rounded-card hover:bg-success/90 disabled:opacity-50"
            onClick={handleApplyIteration}
            disabled={isApplyingThis}
          >
            {isApplyingThis ? '⚡ Applying...' : 'Apply Changes'}
          </button>
        )}
        {canDelete && (
          <button
            className="px-4 py-2 border border-red-300 text-red-600 rounded-card hover:bg-red-50 disabled:opacity-50 ml-auto"
            onClick={handleDelete}
            disabled={deleteMut.isPending}
          >
            {deleteMut.isPending ? 'Deleting...' : 'Delete Iteration'}
          </button>
        )}
      </div>
      
      {updateMut.isSuccess && (
        <div className="text-sm text-green-600">✓ Iteration saved successfully</div>
      )}
      {updateMut.isError && (
        <div className="text-sm text-red-600">✗ Failed to save iteration</div>
      )}
      {deleteMut.isError && (
        <div className="text-sm text-red-600">✗ Failed to delete iteration</div>
      )}
    </div>
  )
}

// Tasks Panel Component
function TasksPanel({ projectId, iterationId, iteration, tasks, onBack }: {
  projectId: string
  iterationId: string
  iteration: DesignIterationModel | undefined
  tasks: any
  onBack: () => void
}) {
  const qc = useQueryClient()
  const ops = useOperationsStore()
  const [showAddTaskModal, setShowAddTaskModal] = useState(false)
  const [editingTask, setEditingTask] = useState<any>(null)
  const [taskName, setTaskName] = useState('')
  const [taskSpec, setTaskSpec] = useState('')
  const [taskPatternId, setTaskPatternId] = useState('')
  const [draggedTaskId, setDraggedTaskId] = useState<string | null>(null)
  const [dragOverTaskId, setDragOverTaskId] = useState<string | null>(null)
  
  // Fetch patterns for the project
  const patternsQ = useQuery({
    enabled: !!projectId,
    queryKey: ['patterns', projectId],
    queryFn: () => api.listPatterns(projectId),
  })
  
  // Use global planning state
  const isPlanningThisIteration = ops.planningTasks === iterationId
  
  const handlePlanTasks = async () => {
    ops.setPlanningTasks(iterationId)
    try {
      await api.planTasks(projectId, iterationId)
      await qc.invalidateQueries({ queryKey: ['tasks', projectId, iterationId] })
      // Invalidate iteration queries to update status from 'suggested' to 'planned'
      await qc.invalidateQueries({ queryKey: ['iterations', projectId] })
      await qc.invalidateQueries({ queryKey: ['iteration', projectId, iterationId] })
      ops.setPlanningTasks(null)
    } catch (error) {
      console.error('Failed to plan tasks:', error)
      ops.setPlanningTasks(null)
    }
  }
  
  const handlePrepareIteration = async () => {
    ops.setPreparingIteration(iterationId)
    try {
      const prepared = await api.prepareIteration(projectId, iterationId)
      ops.open(prepared.iteration_id, prepared.operations)
      await qc.invalidateQueries({ queryKey: ['iterations', projectId] })
      await qc.invalidateQueries({ queryKey: ['iteration', projectId, iterationId] })
      // Go back to iteration view to see the updated status
      onBack()
    } catch (error) {
      console.error('Failed to prepare iteration:', error)
      alert('Failed to prepare iteration. Please try again.')
    } finally {
      ops.setPreparingIteration(null)
    }
  }
  
  const canPrepare = iteration?.status === 'planned'
  const isPreparingThis = ops.preparingIteration === iterationId
  
  const createTaskMut = useMutation({
    mutationFn: () => api.createTask(projectId, iterationId, {
      name: taskName,
      specification: taskSpec,
      followed_pattern_id: taskPatternId
    }),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ['tasks', projectId, iterationId] })
      setShowAddTaskModal(false)
      setTaskName('')
      setTaskSpec('')
      setTaskPatternId('')
    }
  })
  
  const updateTaskMut = useMutation({
    mutationFn: () => api.updateTask(projectId, iterationId, editingTask.id, {
      name: taskName,
      specification: taskSpec,
      followed_pattern_id: taskPatternId
    }),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ['tasks', projectId, iterationId] })
      setEditingTask(null)
      setTaskName('')
      setTaskSpec('')
      setTaskPatternId('')
    }
  })
  
  const deleteTaskMut = useMutation({
    mutationFn: (taskId: string) => api.deleteTask(projectId, iterationId, taskId),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ['tasks', projectId, iterationId] })
    }
  })
  
  const reorderTasksMut = useMutation({
    mutationFn: (taskIds: string[]) => api.reorderTasks(projectId, iterationId, taskIds),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ['tasks', projectId, iterationId] })
    }
  })
  
  const handleEditTask = (task: any) => {
    setEditingTask(task)
    setTaskName(task.name)
    setTaskSpec(task.specification)
    setTaskPatternId(task.followed_pattern_id)
  }
  
  const handleCloseModal = () => {
    setShowAddTaskModal(false)
    setEditingTask(null)
    setTaskName('')
    setTaskSpec('')
    setTaskPatternId('')
  }
  
  const handleDragStart = (e: React.DragEvent, taskId: string) => {
    setDraggedTaskId(taskId)
    e.dataTransfer.effectAllowed = 'move'
  }
  
  const handleDragOver = (e: React.DragEvent, taskId: string) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
    setDragOverTaskId(taskId)
  }
  
  const handleDragLeave = () => {
    setDragOverTaskId(null)
  }
  
  const handleDrop = (e: React.DragEvent, dropTargetId: string) => {
    e.preventDefault()
    setDragOverTaskId(null)
    
    if (!draggedTaskId || draggedTaskId === dropTargetId) {
      setDraggedTaskId(null)
      return
    }
    
    // Reorder tasks
    const taskIds = allTasks.map(t => t.id)
    const draggedIndex = taskIds.indexOf(draggedTaskId)
    const targetIndex = taskIds.indexOf(dropTargetId)
    
    if (draggedIndex === -1 || targetIndex === -1) {
      setDraggedTaskId(null)
      return
    }
    
    // Remove dragged item and insert at new position
    const newTaskIds = [...taskIds]
    newTaskIds.splice(draggedIndex, 1)
    newTaskIds.splice(targetIndex, 0, draggedTaskId)
    
    // Call API to reorder
    reorderTasksMut.mutate(newTaskIds)
    setDraggedTaskId(null)
  }
  
  const handleDragEnd = () => {
    setDraggedTaskId(null)
    setDragOverTaskId(null)
  }
  
  const allTasks = [
    ...(tasks?.planned_tasks || []),
    ...(tasks?.current_task ? [tasks.current_task] : []),
    ...(tasks?.finished_tasks || [])
  ]
  
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Tasks</h2>
        <button
          className="text-sm text-blue-600 hover:underline"
          onClick={onBack}
        >
          ← Back to Iteration
        </button>
      </div>
      
      <div className="flex gap-2">
        <button
          className="px-3 py-2 bg-ai text-white rounded-card hover:opacity-90 disabled:opacity-50"
          onClick={handlePlanTasks}
          disabled={isPlanningThisIteration}
        >
          {isPlanningThisIteration ? '⏳ Planning...' : '✨ Plan Tasks'}
        </button>
        <button 
          className="px-3 py-2 border rounded-card hover:bg-gray-50"
          onClick={() => setShowAddTaskModal(true)}
        >
          + Add Task
        </button>
        {canPrepare && (
          <button
            className="px-3 py-2 bg-green-600 text-white rounded-card hover:bg-green-700 disabled:opacity-50"
            onClick={handlePrepareIteration}
            disabled={isPreparingThis}
          >
            {isPreparingThis ? '⏳ Preparing...' : 'Prepare ▶'}
          </button>
        )}
      </div>
      
      <div className="space-y-2">
        {allTasks.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            No tasks yet. Click "✨ Plan Tasks" to generate tasks with AI.
          </div>
        ) : (
          allTasks.map((task: any) => (
            <div 
              key={task.id} 
              draggable
              onDragStart={(e) => handleDragStart(e, task.id)}
              onDragOver={(e) => handleDragOver(e, task.id)}
              onDragLeave={handleDragLeave}
              onDrop={(e) => handleDrop(e, task.id)}
              onDragEnd={handleDragEnd}
              className={`border rounded-card p-3 transition-all ${
                draggedTaskId === task.id ? 'opacity-50' : ''
              } ${
                dragOverTaskId === task.id && draggedTaskId !== task.id 
                  ? 'border-blue-500 border-2 bg-blue-50' 
                  : ''
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-2 flex-1">
                  <div 
                    className="mt-1 text-gray-400 hover:text-gray-600 transition-colors select-none"
                    style={{ cursor: 'grab' }}
                    title="Drag to reorder"
                  >
                    ⋮⋮
                  </div>
                  <div className="flex-1">
                    <div className="font-medium">{task.name}</div>
                    <div className="text-sm text-gray-600 mt-1">{task.specification}</div>
                    <div className="flex items-center gap-2 mt-2">
                      <span className={`text-xs px-2 py-1 rounded ${
                        task.status === 'completed' ? 'bg-green-100 text-green-800' :
                        task.status === 'generating' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {task.status}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex gap-2">
                  <button 
                    className="text-sm px-2 py-1 border rounded-card hover:bg-gray-50"
                    onClick={() => handleEditTask(task)}
                  >
                    Edit
                  </button>
                  <button 
                    className="text-sm px-2 py-1 border rounded-card hover:bg-gray-50"
                    onClick={() => {
                      if (window.confirm('Are you sure you want to delete this task?')) {
                        deleteTaskMut.mutate(task.id)
                      }
                    }}
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
      
      {/* Add/Edit Task Modal */}
      {(showAddTaskModal || editingTask) && (
        <Modal title={editingTask ? "Edit Task" : "Add Task"} onClose={handleCloseModal}>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Task Name</label>
              <input
                type="text"
                className="w-full border rounded-card px-3 py-2"
                placeholder="Enter task name"
                value={taskName}
                onChange={(e) => setTaskName(e.target.value)}
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-1">Specification</label>
              <textarea
                className="w-full border rounded-card px-3 py-2"
                rows={4}
                placeholder="Describe what this task should accomplish"
                value={taskSpec}
                onChange={(e) => setTaskSpec(e.target.value)}
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-1">Pattern</label>
              <select
                className="w-full border rounded-card px-3 py-2"
                value={taskPatternId}
                onChange={(e) => setTaskPatternId(e.target.value)}
                disabled={patternsQ.isLoading}
              >
                <option value="">
                  {patternsQ.isLoading ? 'Loading patterns...' : 'Select a pattern...'}
                </option>
                {patternsQ.data?.patterns?.map((pattern) => (
                  <option key={pattern.id} value={pattern.id}>
                    {pattern.name} ({pattern.category})
                  </option>
                ))}
              </select>
              {patternsQ.isError && (
                <p className="text-xs text-red-500 mt-1">
                  Failed to load patterns
                </p>
              )}
              {!patternsQ.isLoading && !patternsQ.isError && (
                <p className="text-xs text-gray-500 mt-1">
                  The modeling pattern this task follows
                </p>
              )}
            </div>
            
            <div className="flex justify-end gap-2 pt-2">
              <button
                className="px-4 py-2 border rounded-card hover:bg-gray-50"
                onClick={handleCloseModal}
              >
                Cancel
              </button>
              <button
                className="px-4 py-2 bg-primary-600 text-white rounded-card hover:bg-primary-700 disabled:opacity-50"
                onClick={() => editingTask ? updateTaskMut.mutate() : createTaskMut.mutate()}
                disabled={(editingTask ? updateTaskMut.isPending : createTaskMut.isPending) || !taskName.trim() || !taskSpec.trim() || !taskPatternId.trim()}
              >
                {editingTask 
                  ? (updateTaskMut.isPending ? 'Saving...' : 'Save Changes')
                  : (createTaskMut.isPending ? 'Creating...' : 'Create Task')
                }
              </button>
            </div>
            
            {(createTaskMut.isError || updateTaskMut.isError) && (
              <div className="text-sm text-red-600">
                ✗ Failed to {editingTask ? 'update' : 'create'} task
              </div>
            )}
          </div>
        </Modal>
      )}
    </div>
  )
}

// Operations Panel Component
function OperationsPanel({ projectId, iterationId, iteration, operations, onBack }: {
  projectId: string
  iterationId: string
  iteration: DesignIterationModel | undefined
  operations: any[]
  onBack: () => void
}) {
  const qc = useQueryClient()
  const ops = useOperationsStore()
  const [editingOperation, setEditingOperation] = useState<any>(null)
  const [opLabel, setOpLabel] = useState('')
  const [opDefinition, setOpDefinition] = useState('')
  const [opDescription, setOpDescription] = useState('')
  const [draggedOpId, setDraggedOpId] = useState<string | null>(null)
  const [dragOverOpId, setDragOverOpId] = useState<string | null>(null)
  const [deleteConfirmation, setDeleteConfirmation] = useState<{
    operation: any
    dependentOps: any[]
  } | null>(null)

  const updateOperationMut = useMutation({
    mutationFn: () => api.updateOperation(projectId, iterationId, editingOperation.id, {
      label: opLabel || null,
      definition: opDefinition || null,
      description: opDescription || null,
    }),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ['operations', projectId, iterationId] })
      setEditingOperation(null)
      setOpLabel('')
      setOpDefinition('')
      setOpDescription('')
    }
  })

  const deleteOperationMut = useMutation({
    mutationFn: (operationId: string) => api.deleteOperation(projectId, iterationId, operationId),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ['operations', projectId, iterationId] })
    }
  })

  const deleteCascadeMut = useMutation({
    mutationFn: async (operationIds: string[]) => {
      // Delete operations sequentially in reverse order (dependencies first)
      for (const opId of [...operationIds].reverse()) {
        await api.deleteOperation(projectId, iterationId, opId)
      }
    },
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ['operations', projectId, iterationId] })
      setDeleteConfirmation(null)
    }
  })

  // Analyze dependencies for a CREATE operation
  const findDependentOperations = (operation: any, allOperations: any[]): any[] => {
    if (operation.operation_type !== 'create') {
      return []
    }

    const targetUri = operation.uri
    const dependents: any[] = []

    // Find operations that come after this one
    const opIndex = allOperations.findIndex(op => op.id === operation.id)
    const laterOperations = allOperations.slice(opIndex + 1)

    for (const op of laterOperations) {
      let isDependant = false
      let dependencyReason = ''

      // Check if this operation references the target URI
      if (operation.target_type === 'class') {
        // Check attributes with owning_class_uri
        if (op.target_type === 'attribute' && op.owning_class_uri === targetUri) {
          isDependant = true
          dependencyReason = `Attribute's domain class`
        }
        
        // Check relationships with source_class_uri or target_class_uri
        if (op.target_type === 'relationship') {
          if (op.source_class_uri === targetUri) {
            isDependant = true
            dependencyReason = `Relationship's source class`
          } else if (op.target_class_uri === targetUri) {
            isDependant = true
            dependencyReason = `Relationship's target class`
          }
        }
        
        // Check classes with generalization_uris
        if (op.target_type === 'class' && op.generalization_uris?.includes(targetUri)) {
          isDependant = true
          dependencyReason = `Parent class in generalization`
        }
        
        // Check update/delete operations on the class
        if (op.uri === targetUri && (op.operation_type === 'update' || op.operation_type === 'delete')) {
          isDependant = true
          dependencyReason = `${op.operation_type === 'update' ? 'Updates' : 'Deletes'} this class`
        }
      } else if (operation.target_type === 'attribute') {
        // Check update/delete operations on the attribute
        if (op.uri === targetUri && (op.operation_type === 'update' || op.operation_type === 'delete')) {
          isDependant = true
          dependencyReason = `${op.operation_type === 'update' ? 'Updates' : 'Deletes'} this attribute`
        }
      } else if (operation.target_type === 'relationship') {
        // Check update/delete operations on the relationship
        if (op.uri === targetUri && (op.operation_type === 'update' || op.operation_type === 'delete')) {
          isDependant = true
          dependencyReason = `${op.operation_type === 'update' ? 'Updates' : 'Deletes'} this relationship`
        }
      }

      if (isDependant) {
        dependents.push({ ...op, dependencyReason })
      }
    }

    return dependents
  }

  const handleDeleteOperation = (op: any) => {
    // For CREATE operations, check for dependencies
    if (op.operation_type === 'create') {
      const dependents = findDependentOperations(op, operations)
      
      if (dependents.length > 0) {
        // Show confirmation modal with dependent operations
        setDeleteConfirmation({
          operation: op,
          dependentOps: dependents
        })
      } else {
        // No dependencies, proceed with simple delete
        if (window.confirm('Are you sure you want to delete this operation?')) {
          deleteOperationMut.mutate(op.id)
        }
      }
    } else {
      // For UPDATE and DELETE operations, simple delete
      if (window.confirm('Are you sure you want to delete this operation?')) {
        deleteOperationMut.mutate(op.id)
      }
    }
  }

  const handleConfirmCascadeDelete = () => {
    if (!deleteConfirmation) return
    
    const opsToDelete = [
      deleteConfirmation.operation.id,
      ...deleteConfirmation.dependentOps.map(op => op.id)
    ]
    
    deleteCascadeMut.mutate(opsToDelete)
  }

  const reorderOperationsMut = useMutation({
    mutationFn: (operationIds: string[]) => api.reorderOperations(projectId, iterationId, operationIds),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ['operations', projectId, iterationId] })
    }
  })

  const handleEditOperation = (op: any) => {
    setEditingOperation(op)
    setOpLabel(op.label || '')
    setOpDefinition(op.definition || '')
    setOpDescription(op.description || '')
  }

  const handleCloseModal = () => {
    setEditingOperation(null)
    setOpLabel('')
    setOpDefinition('')
    setOpDescription('')
  }

  const handleDragStart = (e: React.DragEvent, opId: string) => {
    setDraggedOpId(opId)
    e.dataTransfer.effectAllowed = 'move'
  }

  const handleDragOver = (e: React.DragEvent, opId: string) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
    setDragOverOpId(opId)
  }

  const handleDragLeave = () => {
    setDragOverOpId(null)
  }

  const handleDrop = (e: React.DragEvent, dropTargetId: string) => {
    e.preventDefault()
    setDragOverOpId(null)

    if (!draggedOpId || draggedOpId === dropTargetId) {
      setDraggedOpId(null)
      return
    }

    // Reorder operations
    const opIds = operations.map(op => op.id)
    const draggedIndex = opIds.indexOf(draggedOpId)
    const targetIndex = opIds.indexOf(dropTargetId)

    if (draggedIndex === -1 || targetIndex === -1) {
      setDraggedOpId(null)
      return
    }

    // Remove dragged item and insert at new position
    const newOpIds = [...opIds]
    newOpIds.splice(draggedIndex, 1)
    newOpIds.splice(targetIndex, 0, draggedOpId)

    // Call API to reorder
    reorderOperationsMut.mutate(newOpIds)
    setDraggedOpId(null)
  }

  const handleDragEnd = () => {
    setDraggedOpId(null)
    setDragOverOpId(null)
  }

  const getOperationLabel = (op: any) => {
    const action = op.operation_type === 'create' ? 'Add' : op.operation_type === 'delete' ? 'Remove' : 'Modify'
    const target = op.target_type.charAt(0).toUpperCase() + op.target_type.slice(1)
    return `${action} ${target}`
  }

  const getBadgeColor = (opType: 'create' | 'update' | 'delete') => {
    if (opType === 'create') return 'bg-green-100 text-green-800'
    if (opType === 'delete') return 'bg-red-100 text-red-800'
    return 'bg-blue-100 text-blue-800'
  }

  const handleApplyIteration = async () => {
    ops.setApplyingIteration(iterationId)
    const changesStore = useOntologyChangesStore.getState()
    try {
      // Check if we have cached operations for this iteration
      const cachedOps = ops.operationsCache[iterationId]
      
      // Apply with filtered operations if available, otherwise use server-side ops
      await api.applyIteration(projectId, iterationId, cachedOps)
      
      // Record the changes for highlighting in ontology view
      if (cachedOps && cachedOps.length > 0) {
        changesStore.recordChanges(iterationId, cachedOps)
      }
      
      // Invalidate ontology query to refetch the updated ontology
      await qc.invalidateQueries({ queryKey: ['ontology', projectId] })
      await qc.invalidateQueries({ queryKey: ['iterations', projectId] })
      await qc.invalidateQueries({ queryKey: ['iteration', projectId, iterationId] })
      
      // Clear the drawer if it's open for this iteration
      if (ops.iterationId === iterationId) {
        ops.close()
        ops.clear()
      }
      
      // Go back to iteration view to see the updated status
      onBack()
      
      ops.setApplyingIteration(null)
    } catch (error) {
      console.error('Failed to apply iteration:', error)
      alert('Failed to apply iteration. Please try again.')
      ops.setApplyingIteration(null)
    }
  }

  const canApply = iteration?.status === 'prepared'
  const isApplyingThis = ops.applyingIteration === iterationId

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Operations</h2>
        <button
          className="text-sm text-blue-600 hover:underline"
          onClick={onBack}
        >
          ← Back to Iteration
        </button>
      </div>

      {canApply && (
        <div className="flex gap-2">
          <button
            className="px-4 py-2 bg-success text-white rounded-card hover:bg-success/90 disabled:opacity-50"
            onClick={handleApplyIteration}
            disabled={isApplyingThis}
          >
            {isApplyingThis ? '⚡ Applying...' : 'Apply Changes'}
          </button>
          <p className="text-sm text-gray-600 self-center">
            {operations.length} operation{operations.length !== 1 ? 's' : ''} ready to apply
          </p>
        </div>
      )}

      <div className="space-y-2">
        {operations.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            No operations available.
          </div>
        ) : (
          operations.map((op: any) => (
            <div
              key={op.id}
              draggable
              onDragStart={(e) => handleDragStart(e, op.id)}
              onDragOver={(e) => handleDragOver(e, op.id)}
              onDragLeave={handleDragLeave}
              onDrop={(e) => handleDrop(e, op.id)}
              onDragEnd={handleDragEnd}
              className={`border rounded-card p-3 cursor-move transition-all ${
                draggedOpId === op.id ? 'opacity-50' : ''
              } ${
                dragOverOpId === op.id && draggedOpId !== op.id
                  ? 'border-blue-500 border-2 bg-blue-50'
                  : ''
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-2 flex-1">
                  <div 
                    className="mt-1 text-gray-400 hover:text-gray-600 transition-colors select-none"
                    style={{ cursor: 'grab' }}
                    title="Drag to reorder"
                  >
                    ⋮⋮
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className={`text-xs px-2 py-1 rounded ${getBadgeColor(op.operation_type)}`}>
                        {getOperationLabel(op)}
                      </span>
                      <span className="text-xs px-2 py-1 rounded bg-gray-100 text-gray-700">
                        {op.target_type}
                      </span>
                    </div>
                    <div className="font-medium text-sm">
                      <span className="text-gray-500">URI:</span> {op.uri}
                    </div>
                    {op.label && (
                      <div className="text-sm mt-1">
                        <span className="text-gray-500">Label:</span> {op.label}
                      </div>
                    )}
                    {op.definition && (
                      <div className="text-sm text-gray-600 mt-1">{op.definition}</div>
                    )}
                    {op.description && (
                      <div className="text-sm text-gray-600 mt-1">{op.description}</div>
                    )}
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    className="text-sm px-2 py-1 border rounded-card hover:bg-gray-50"
                    onClick={() => handleEditOperation(op)}
                  >
                    Edit
                  </button>
                  <button
                    className="text-sm px-2 py-1 border rounded-card hover:bg-gray-50 text-red-600"
                    onClick={() => handleDeleteOperation(op)}
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Edit Operation Modal */}
      {editingOperation && (
        <Modal title="Edit Operation" onClose={handleCloseModal}>
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium mb-1">Operation Type</label>
              <input
                type="text"
                className="w-full border rounded-card px-3 py-2 bg-gray-100"
                value={`${editingOperation.operation_type} ${editingOperation.target_type}`}
                disabled
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">URI</label>
              <input
                type="text"
                className="w-full border rounded-card px-3 py-2 bg-gray-100"
                value={editingOperation.uri}
                disabled
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Label</label>
              <input
                type="text"
                className="w-full border rounded-card px-3 py-2"
                value={opLabel}
                onChange={(e) => setOpLabel(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Definition</label>
              <textarea
                className="w-full border rounded-card px-3 py-2"
                rows={3}
                value={opDefinition}
                onChange={(e) => setOpDefinition(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Description</label>
              <textarea
                className="w-full border rounded-card px-3 py-2"
                rows={3}
                value={opDescription}
                onChange={(e) => setOpDescription(e.target.value)}
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button
                className="px-4 py-2 border rounded-card hover:bg-gray-50"
                onClick={handleCloseModal}
              >
                Cancel
              </button>
              <button
                className="px-4 py-2 bg-primary-600 text-white rounded-card hover:bg-primary-700 disabled:opacity-50"
                onClick={() => updateOperationMut.mutate()}
                disabled={updateOperationMut.isPending}
              >
                {updateOperationMut.isPending ? 'Saving...' : 'Save'}
              </button>
            </div>
            {updateOperationMut.isSuccess && (
              <div className="text-sm text-green-600">✓ Operation updated successfully</div>
            )}
            {updateOperationMut.isError && (
              <div className="text-sm text-red-600">✗ Failed to update operation</div>
            )}
          </div>
        </Modal>
      )}

      {/* Delete Confirmation Modal with Dependencies */}
      {deleteConfirmation && (
        <Modal 
          title="Delete Operation with Dependencies" 
          onClose={() => setDeleteConfirmation(null)}
        >
          <div className="space-y-4">
            <div className="bg-yellow-50 border border-yellow-200 rounded-card p-3">
              <div className="flex items-start gap-2">
                <span className="text-yellow-600 text-lg">⚠️</span>
                <div className="flex-1">
                  <p className="font-medium text-yellow-900">
                    This operation has dependent operations
                  </p>
                  <p className="text-sm text-yellow-800 mt-1">
                    Deleting this CREATE operation will break {deleteConfirmation.dependentOps.length} 
                    {deleteConfirmation.dependentOps.length === 1 ? ' operation' : ' operations'} that 
                    depend on it. All dependent operations must be deleted as well.
                  </p>
                </div>
              </div>
            </div>

            <div>
              <h3 className="font-medium text-sm mb-2">Operation to delete:</h3>
              <div className="border rounded-card p-3 bg-red-50">
                <div className="flex items-center gap-2 mb-1">
                  <span className={`text-xs px-2 py-1 rounded ${getBadgeColor(deleteConfirmation.operation.operation_type)}`}>
                    {getOperationLabel(deleteConfirmation.operation)}
                  </span>
                  <span className="text-xs px-2 py-1 rounded bg-gray-100 text-gray-700">
                    {deleteConfirmation.operation.target_type}
                  </span>
                </div>
                <div className="text-sm font-medium">
                  URI: <code className="text-xs bg-white px-1 py-0.5 rounded">{deleteConfirmation.operation.uri}</code>
                </div>
                {deleteConfirmation.operation.label && (
                  <div className="text-sm mt-1">Label: {deleteConfirmation.operation.label}</div>
                )}
              </div>
            </div>

            <div>
              <h3 className="font-medium text-sm mb-2">
                Dependent operations (will also be deleted):
              </h3>
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {deleteConfirmation.dependentOps.map((op, idx) => (
                  <div key={idx} className="border rounded-card p-3 bg-gray-50">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`text-xs px-2 py-1 rounded ${getBadgeColor(op.operation_type)}`}>
                        {getOperationLabel(op)}
                      </span>
                      <span className="text-xs px-2 py-1 rounded bg-gray-100 text-gray-700">
                        {op.target_type}
                      </span>
                      <span className="text-xs px-2 py-1 rounded bg-orange-100 text-orange-800">
                        {op.dependencyReason}
                      </span>
                    </div>
                    <div className="text-sm font-medium">
                      URI: <code className="text-xs bg-white px-1 py-0.5 rounded">{op.uri}</code>
                    </div>
                    {op.label && (
                      <div className="text-sm mt-1">Label: {op.label}</div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-gray-50 border border-gray-200 rounded-card p-3">
              <p className="text-sm text-gray-700">
                <strong>Total operations to delete:</strong> {1 + deleteConfirmation.dependentOps.length}
              </p>
            </div>

            <div className="flex gap-2 pt-2">
              <button
                onClick={() => setDeleteConfirmation(null)}
                disabled={deleteCascadeMut.isPending}
                className="flex-1 px-4 py-2 border rounded-card hover:bg-gray-50 disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmCascadeDelete}
                disabled={deleteCascadeMut.isPending}
                className="flex-1 px-4 py-2 bg-red-600 text-white rounded-card hover:bg-red-700 disabled:opacity-50"
              >
                {deleteCascadeMut.isPending ? 'Deleting...' : 'Delete All'}
              </button>
            </div>

            {deleteCascadeMut.isError && (
              <div className="text-sm text-red-600 mt-2">
                ✗ Failed to delete operations: {(deleteCascadeMut.error as Error).message}
              </div>
            )}
          </div>
        </Modal>
      )}
    </div>
  )
}

export function WorkbenchPage() {
  const { projectId, areaId, iterationId, setAreaId, setIterationId } = useProjectStore()
  const ops = useOperationsStore()
  const qc = useQueryClient()
  const [showTasksView, setShowTasksView] = useState(false)
  const [showOperationsView, setShowOperationsView] = useState(false)
  const [isEditingArea, setIsEditingArea] = useState(false)
  const [showSuggestModal, setShowSuggestModal] = useState(false)
  const [suggestAreaId, setSuggestAreaId] = useState<string>('')
  const [suggestCount, setSuggestCount] = useState(5)
  const [suggestInstruction, setSuggestInstruction] = useState('')
  const [leftPanelCollapsed, setLeftPanelCollapsed] = useState(false)
  const [hoveredIteration, setHoveredIteration] = useState<string | null>(null)
  const [showAddAreaModal, setShowAddAreaModal] = useState(false)
  const [showAddIterationModal, setShowAddIterationModal] = useState(false)
  const [newAreaLabel, setNewAreaLabel] = useState('')
  const [newAreaDescription, setNewAreaDescription] = useState('')
  const [newIterationName, setNewIterationName] = useState('')
  const [newIterationSpec, setNewIterationSpec] = useState('')
  
  // Use global loading state from operationsStore
  const { suggestingIterations } = ops
  
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
  
  const selectedAreaQ = useQuery({
    enabled: !!projectId && !!areaId,
    queryKey: ['area', projectId, areaId],
    queryFn: () => api.getArea(projectId!, areaId!),
  })
  
  const selectedIterationQ = useQuery({
    enabled: !!projectId && !!iterationId,
    queryKey: ['iteration', projectId, iterationId],
    queryFn: () => api.getIteration(projectId!, iterationId!),
  })
  
  const tasksQ = useQuery({
    enabled: !!projectId && !!iterationId && showTasksView,
    queryKey: ['tasks', projectId, iterationId],
    queryFn: () => api.listTasks(projectId!, iterationId!),
  })

  const operationsQ = useQuery({
    enabled: !!projectId && !!iterationId && showOperationsView,
    queryKey: ['operations', projectId, iterationId],
    queryFn: async () => {
      const result = await api.getIterationOperations(projectId!, iterationId!)
      return result.operations
    },
  })
  
  const [reidentifyPrompt, setReidentifyPrompt] = useState('')
  const reidentify = useMutation({
    mutationFn: () => api.reidentifyAreas(projectId!, reidentifyPrompt),
    onSuccess: async () => qc.invalidateQueries({ queryKey: ['areas', projectId] }),
  })
  
  const createAreaMut = useMutation({
    mutationFn: () => api.createArea(projectId!, {
      label: newAreaLabel,
      description: newAreaDescription,
      parent_id: null,
      key_concepts: []
    }),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ['areas', projectId] })
      setShowAddAreaModal(false)
      setNewAreaLabel('')
      setNewAreaDescription('')
    }
  })
  
  const createIterationMut = useMutation({
    mutationFn: () => api.createIteration(projectId!, {
      name: newIterationName,
      specification: newIterationSpec,
      focused_area_id: suggestAreaId || areaId || areasQ.data?.[0]?.id || ''
    }),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ['iterations', projectId] })
      setShowAddIterationModal(false)
      setNewIterationName('')
      setNewIterationSpec('')
    }
  })
  
  if (!projectId) return <div>Select a project to use the workbench.</div>
  
  // Group iterations by area for the tree view
  const iterationsByArea = new Map<string, any[]>()
  iterationsQ.data?.planned_iterations.forEach(it => {
    const area = it.focused_area_id
    if (!iterationsByArea.has(area)) {
      iterationsByArea.set(area, [])
    }
    iterationsByArea.get(area)!.push(it)
  })
  if (iterationsQ.data?.current_iteration) {
    const area = iterationsQ.data.current_iteration.focused_area_id
    if (!iterationsByArea.has(area)) {
      iterationsByArea.set(area, [])
    }
    iterationsByArea.get(area)!.push(iterationsQ.data.current_iteration)
  }
  
  const handleAreaClick = (id: string) => {
    setAreaId(id)
    setIterationId(null)
    setShowTasksView(false)
    setIsEditingArea(false) // Reset to detail view when selecting new area
  }
  
  const handleIterationClick = (id: string) => {
    setIterationId(id)
    setShowTasksView(false)
    setShowOperationsView(false)
    setIsEditingArea(false)
  }
  
  const handleSuggestIterations = async () => {
    if (!projectId || !suggestAreaId) return
    
    ops.setSuggestingIterations(true)
    try {
      await api.suggestIterations(projectId, {
        focused_area_id: suggestAreaId,
        count: suggestCount,
        user_instruction: suggestInstruction || null
      })
      await qc.invalidateQueries({ queryKey: ['iterations', projectId] })
      setShowSuggestModal(false)
      setSuggestInstruction('')
    } catch (error) {
      console.error('Failed to suggest iterations:', error)
    } finally {
      ops.setSuggestingIterations(false)
    }
  }
  
  return (
    <div className={`grid ${leftPanelCollapsed ? 'grid-cols-[48px,1fr]' : 'grid-cols-[280px,1fr]'} gap-4`}>
      {/* LEFT TREE */}
      <div className="bg-white border rounded-card p-3">
        <div className="flex items-center justify-between mb-3">
          <div className="font-semibold">
            {leftPanelCollapsed ? '📁' : 'Areas & Iterations'}
          </div>
          {!leftPanelCollapsed && (
            <div className="flex items-center gap-1">
              <button
                className="text-xs px-2 py-1 bg-ai text-white rounded hover:opacity-90"
                onClick={() => {
                  setSuggestAreaId(areaId || areasQ.data?.[0]?.id || '')
                  setShowSuggestModal(true)
                }}
                disabled={!areasQ.data || areasQ.data.length === 0}
                title="Generate AI-suggested design iterations for an area"
              >
                ✨ Suggest Iterations
              </button>
              <button 
                className="text-xs p-1 hover:bg-gray-100 rounded"
                onClick={() => setLeftPanelCollapsed(!leftPanelCollapsed)}
                title="Collapse panel"
              >
                ←
              </button>
            </div>
          )}
          {leftPanelCollapsed && (
            <button 
              className="text-xs p-1 hover:bg-gray-100 rounded"
              onClick={() => setLeftPanelCollapsed(!leftPanelCollapsed)}
              title="Expand panel"
            >
              →
            </button>
          )}
        </div>
        
        {!leftPanelCollapsed && (
          <>
            {/* Add Area/Iteration Buttons */}
            <div className="flex items-center gap-2 mb-3">
              <button
                className="flex-1 text-xs px-2 py-1 border rounded hover:bg-gray-50"
                onClick={() => setShowAddAreaModal(true)}
              >
                + Area
              </button>
              <button
                className="flex-1 text-xs px-2 py-1 border rounded hover:bg-gray-50"
                onClick={() => {
                  setSuggestAreaId(areaId || areasQ.data?.[0]?.id || '')
                  setShowAddIterationModal(true)
                }}
                disabled={!areaId && (!areasQ.data || areasQ.data.length === 0)}
                title={!areaId && (!areasQ.data || areasQ.data.length === 0) ? "Create an area first" : "Add new iteration"}
              >
                + Iteration
              </button>
            </div>
            
            {areasQ.isLoading ? (
              <div className="space-y-2">
                <div className="text-center text-gray-500 py-4 text-sm">
                  <div className="animate-spin inline-block w-4 h-4 border-2 border-gray-300 border-t-blue-500 rounded-full mr-2"></div>
                  Loading areas...
                </div>
              </div>
            ) : (
              <div className="space-y-1">
                {areasQ.data?.map((area) => {
                  const areaIterations = iterationsByArea.get(area.id) || []
                  const isSelected = areaId === area.id && !iterationId
                  const hasActiveIterations = areaIterations.some(it => 
                    it.status === 'prepared' || it.status === 'planned'
                  )
                  
                  return (
                    <div key={area.id}>
                      {/* Area Item */}
                      <div
                        className={`px-3 py-2 rounded-card cursor-pointer hover:bg-gray-50 border-l-4 transition-all ${
                          isSelected 
                            ? 'bg-blue-50 border-blue-400 font-medium' 
                            : hasActiveIterations 
                            ? 'border-blue-300'
                            : 'border-transparent'
                        }`}
                        onClick={() => handleAreaClick(area.id)}
                        title={area.description}
                      >
                        <div className="flex items-center gap-2">
                          {hasActiveIterations && (
                            <span className="w-2 h-2 bg-blue-500 rounded-full flex-shrink-0" title="Has active iterations"></span>
                          )}
                          {areaIterations.length > 0 ? (
                            <span className="text-gray-400 text-xs">▼</span>
                          ) : (
                            <span className="text-gray-300 text-xs">○</span>
                          )}
                          <span className="flex-1 truncate">{area.label}</span>
                          {areaIterations.length > 0 && (
                            <span className="text-xs px-1.5 py-0.5 bg-gray-100 text-gray-600 rounded">
                              {areaIterations.length}
                            </span>
                          )}
                        </div>
                      </div>
                      
                      {/* Nested Iterations */}
                      {areaIterations.length > 0 && (
                        <div className="ml-4 space-y-1 mt-1">
                          {areaIterations.map((iteration) => {
                            const isIterationSelected = iterationId === iteration.id
                            const badge = getIterationStatusBadge(iteration.status)
                            return (
                              <div
                                key={iteration.id}
                                className={`px-2 py-1.5 rounded cursor-pointer hover:bg-gray-100 text-sm ${
                                  isIterationSelected ? 'bg-blue-100 font-medium' : ''
                                }`}
                                onClick={(e) => {
                                  e.stopPropagation()
                                  handleIterationClick(iteration.id)
                                }}
                                onMouseEnter={() => setHoveredIteration(iteration.id)}
                                onMouseLeave={() => setHoveredIteration(null)}
                                title={iteration.specification}
                              >
                                <div className="flex items-start gap-2">
                                  <span className="text-gray-400 mt-0.5">•</span>
                                  <div className="flex-1 min-w-0">
                                    <div className="truncate">{iteration.name}</div>
                                    <div className="flex items-center gap-2 mt-1 flex-wrap">
                                      <span className={`text-xs px-1.5 py-0.5 rounded ${badge.color}`}>
                                        {badge.icon} {badge.label}
                                      </span>
                                      {(iteration.planned_tasks_count ?? 0) > 0 && (
                                        <span className="text-xs text-gray-500">
                                          📋 {iteration.planned_tasks_count}
                                        </span>
                                      )}
                                    </div>
                                  </div>
                                </div>
                              </div>
                            )
                          })}
                        </div>
                      )}
                      {areaIterations.length === 0 && isSelected && (
                        <div className="ml-4 text-xs text-gray-400 italic py-1">
                          No iterations yet. Click "✨ Suggest Iterations" to create some.
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            )}
          </>
        )}
      </div>

      {/* MAIN PANEL - Context Sensitive */}
      <div className="space-y-4">
        {/* Breadcrumb Navigation */}
        {(areaId || iterationId) && (
          <div className="flex items-center gap-2 text-sm text-gray-600 pb-2 border-b bg-white rounded-card px-4 py-2">
            {areaId && selectedAreaQ.data && (
              <>
                <span 
                  className="text-blue-600 cursor-pointer hover:underline"
                  onClick={() => {
                    setIterationId(null)
                    setShowTasksView(false)
                    setShowOperationsView(false)
                  }}
                >
                  📁 {selectedAreaQ.data.label}
                </span>
                {iterationId && selectedIterationQ.data && (
                  <>
                    <span>/</span>
                    <span 
                      className="text-blue-600 cursor-pointer hover:underline"
                      onClick={() => {
                        setShowTasksView(false)
                        setShowOperationsView(false)
                      }}
                    >
                      🔄 {selectedIterationQ.data.name}
                    </span>
                    {showTasksView && (
                      <>
                        <span>/</span>
                        <span className="text-gray-800">📋 Tasks</span>
                      </>
                    )}
                    {showOperationsView && (
                      <>
                        <span>/</span>
                        <span className="text-gray-800">⚙️ Operations</span>
                      </>
                    )}
                  </>
                )}
              </>
            )}
          </div>
        )}
        
        {/* Show Area Detail/Edit when area is selected */}
        {areaId && !iterationId && selectedAreaQ.data && (
          <div className="bg-white border rounded-card p-4">
            {isEditingArea ? (
              <AreaEditForm 
                area={selectedAreaQ.data} 
                projectId={projectId}
                allAreas={areasQ.data || []}
                onCancel={() => setIsEditingArea(false)}
              />
            ) : (
              <AreaDetailView
                area={selectedAreaQ.data}
                projectId={projectId}
                allAreas={areasQ.data || []}
                onEdit={() => setIsEditingArea(true)}
              />
            )}
          </div>
        )}
        
        {/* Show Iteration Tab when iteration is selected */}
        {iterationId && !showTasksView && !showOperationsView && selectedIterationQ.data && (
          <div className="bg-white border rounded-card p-4">
            <IterationEditForm 
              iteration={selectedIterationQ.data}
              projectId={projectId}
              areas={areasQ.data || []}
              onViewTasks={() => setShowTasksView(true)}
              onViewOperations={() => setShowOperationsView(true)}
            />
          </div>
        )}
        
        {/* Show Tasks Tab when viewing tasks */}
        {iterationId && showTasksView && (
          <div className="bg-white border rounded-card p-4">
            <TasksPanel
              projectId={projectId}
              iterationId={iterationId}
              iteration={selectedIterationQ.data}
              tasks={tasksQ.data}
              onBack={() => setShowTasksView(false)}
            />
          </div>
        )}

        {/* Show Operations Tab when viewing operations */}
        {iterationId && showOperationsView && operationsQ.data && (
          <div className="bg-white border rounded-card p-4">
            <OperationsPanel
              projectId={projectId}
              iterationId={iterationId}
              iteration={selectedIterationQ.data}
              operations={operationsQ.data}
              onBack={() => setShowOperationsView(false)}
            />
          </div>
        )}
        
        {/* Show welcome message when nothing is selected */}
        {!areaId && !iterationId && (
          <div className="bg-white border rounded-card p-4">
            <div className="text-center text-gray-500 py-8">
              <h3 className="text-lg font-medium mb-2">Workbench</h3>
              <p>Select an area or iteration from the left to edit</p>
            </div>
          </div>
        )}
      </div>
      
      {/* Suggest Iterations Modal */}
      {showSuggestModal && (
        <Modal title="Suggest Iterations" onClose={() => setShowSuggestModal(false)}>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">
                Select Area for Iteration Suggestions
              </label>
              <select
                className="w-full border rounded-card px-3 py-2"
                value={suggestAreaId}
                onChange={(e) => setSuggestAreaId(e.target.value)}
              >
                {areasQ.data?.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.label}
                  </option>
                ))}
              </select>
              <p className="text-xs text-gray-500 mt-1">
                Choose which domain area the iterations should focus on
              </p>
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-1">Number of Iterations</label>
              <input
                type="number"
                min={1}
                max={20}
                className="w-24 border rounded-card px-3 py-2"
                value={suggestCount}
                onChange={(e) => setSuggestCount(Number(e.target.value))}
              />
              <p className="text-xs text-gray-500 mt-1">
                Generate between 1-20 iteration suggestions
              </p>
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-1">Custom Instructions (optional)</label>
              <textarea
                className="w-full border rounded-card px-3 py-2"
                rows={3}
                placeholder="E.g., Focus on improving class definitions, Add more relationships..."
                value={suggestInstruction}
                onChange={(e) => setSuggestInstruction(e.target.value)}
              />
            </div>
            
            <div className="flex justify-end gap-2 pt-2">
              <button
                className="px-4 py-2 border rounded-card hover:bg-gray-50"
                onClick={() => {
                  setShowSuggestModal(false)
                  setSuggestInstruction('')
                }}
              >
                Cancel
              </button>
              <button
                className="px-4 py-2 bg-primary-600 text-white rounded-card hover:bg-primary-700 disabled:opacity-50"
                onClick={handleSuggestIterations}
                disabled={!suggestAreaId || suggestingIterations}
              >
                {suggestingIterations ? '⏳ Suggesting...' : '✨ Generate Iterations'}
              </button>
            </div>
          </div>
        </Modal>
      )}
      
      {/* Add Area Modal */}
      {showAddAreaModal && (
        <Modal title="Add New Area" onClose={() => setShowAddAreaModal(false)}>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Area Label</label>
              <input
                type="text"
                className="w-full border rounded-card px-3 py-2"
                placeholder="E.g., Customer Management, Products, Orders..."
                value={newAreaLabel}
                onChange={(e) => setNewAreaLabel(e.target.value)}
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-1">Description</label>
              <textarea
                className="w-full border rounded-card px-3 py-2"
                rows={4}
                placeholder="Describe what this domain area covers..."
                value={newAreaDescription}
                onChange={(e) => setNewAreaDescription(e.target.value)}
              />
            </div>
            
            <div className="flex justify-end gap-2 pt-2">
              <button
                className="px-4 py-2 border rounded-card hover:bg-gray-50"
                onClick={() => {
                  setShowAddAreaModal(false)
                  setNewAreaLabel('')
                  setNewAreaDescription('')
                }}
              >
                Cancel
              </button>
              <button
                className="px-4 py-2 bg-primary-600 text-white rounded-card hover:bg-primary-700 disabled:opacity-50"
                onClick={() => createAreaMut.mutate()}
                disabled={createAreaMut.isPending || !newAreaLabel.trim()}
              >
                {createAreaMut.isPending ? 'Creating...' : 'Create Area'}
              </button>
            </div>
            
            {createAreaMut.isError && (
              <div className="text-sm text-red-600">✗ Failed to create area</div>
            )}
          </div>
        </Modal>
      )}
      
      {/* Add Iteration Modal */}
      {showAddIterationModal && (
        <Modal title="Add New Iteration" onClose={() => setShowAddIterationModal(false)}>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Focused Area</label>
              <select
                className="w-full border rounded-card px-3 py-2"
                value={suggestAreaId}
                onChange={(e) => setSuggestAreaId(e.target.value)}
              >
                {areasQ.data?.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.label}
                  </option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-1">Iteration Name</label>
              <input
                type="text"
                className="w-full border rounded-card px-3 py-2"
                placeholder="E.g., Add customer validation, Refine product model..."
                value={newIterationName}
                onChange={(e) => setNewIterationName(e.target.value)}
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-1">Specification</label>
              <textarea
                className="w-full border rounded-card px-3 py-2"
                rows={4}
                placeholder="Describe what changes this iteration should make..."
                value={newIterationSpec}
                onChange={(e) => setNewIterationSpec(e.target.value)}
              />
            </div>
            
            <div className="flex justify-end gap-2 pt-2">
              <button
                className="px-4 py-2 border rounded-card hover:bg-gray-50"
                onClick={() => {
                  setShowAddIterationModal(false)
                  setNewIterationName('')
                  setNewIterationSpec('')
                }}
              >
                Cancel
              </button>
              <button
                className="px-4 py-2 bg-primary-600 text-white rounded-card hover:bg-primary-700 disabled:opacity-50"
                onClick={() => createIterationMut.mutate()}
                disabled={createIterationMut.isPending || !newIterationName.trim() || !newIterationSpec.trim()}
              >
                {createIterationMut.isPending ? 'Creating...' : 'Create Iteration'}
              </button>
            </div>
            
            {createIterationMut.isError && (
              <div className="text-sm text-red-600">✗ Failed to create iteration</div>
            )}
          </div>
        </Modal>
      )}
    </div>
  )
}
