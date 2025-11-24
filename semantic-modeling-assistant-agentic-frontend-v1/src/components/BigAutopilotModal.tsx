import { Modal } from './Modal'
import { useState } from 'react'
import { useOperationsStore } from '@/store/operationsStore'
import { useProjectStore } from '@/store/projectStore'
import { api } from '@/lib/api'
import { useQueryClient } from '@tanstack/react-query'
import { useOntologyChangesStore } from '@/store/ontologyChangesStore'

interface BigAutopilotModalProps {
  onClose: () => void
}

export function BigAutopilotModal({ onClose }: BigAutopilotModalProps) {
  const { projectId } = useProjectStore()
  const ops = useOperationsStore()
  const [maxIterationsPerArea, setMaxIterationsPerArea] = useState(10)
  const qc = useQueryClient()

  const handleStart = async () => {
    if (!projectId) {
      alert('Please select a project first')
      return
    }

    // Start the big autopilot
    ops.startBigAutopilot(maxIterationsPerArea)
    onClose()

    // Run the big autopilot loop
    await runBigAutopilot(projectId, maxIterationsPerArea)
  }

  const runBigAutopilot = async (projectId: string, maxIterationsPerArea: number) => {
    const changesStore = useOntologyChangesStore.getState()
    
    // Track which areas should not request more iterations (received < 3)
    const areasNoMoreSuggestions = new Set<string>()
    
    try {
      // Get all areas
      const areas = await api.listAreas(projectId)
      
      if (areas.length === 0) {
        alert('No domain areas found. Please generate domain areas first.')
        ops.stopBigAutopilot()
        return
      }

      let totalIterationsCompleted = 0

      // Main loop - keep processing until we're done
      while (true) {
        // Check if stop was requested
        if (useOperationsStore.getState().bigAutopilotStopRequested) {
          console.log('Big autopilot stop requested')
          break
        }

        // Step 1: Check all areas for iterations in 'planned' or 'prepared' state
        let foundPlannedOrPrepared = false
        for (const area of areas) {
          if (useOperationsStore.getState().bigAutopilotStopRequested) break

          const iterationsList = await api.listIterations(projectId, area.id)
          
          // Find iterations in planned or prepared state
          const plannedOrPreparedIterations = [
            ...iterationsList.planned_iterations,
            ...(iterationsList.current_iteration ? [iterationsList.current_iteration] : [])
          ].filter(it => it.status === 'planned' || it.status === 'prepared')

          if (plannedOrPreparedIterations.length > 0) {
            foundPlannedOrPrepared = true
            
            // Update progress
            ops.updateBigAutopilotProgress({
              currentAreaId: area.id,
              currentAreaName: area.label,
            })

            // Execute each one completely before moving to the next
            for (const iteration of plannedOrPreparedIterations) {
              if (useOperationsStore.getState().bigAutopilotStopRequested) break

              // Update progress with iteration name
              ops.updateBigAutopilotProgress({
                currentIterationName: iteration.name,
              })

              await executeIteration(projectId, iteration.id, area.id, changesStore)
              totalIterationsCompleted++
              
              // Update progress
              const currentProgress = useOperationsStore.getState().bigAutopilotProgress
              ops.updateBigAutopilotProgress({
                totalIterationsCompleted: totalIterationsCompleted,
                currentIterationName: null,
              })

              // Refresh ontology after each iteration
              await qc.invalidateQueries({ queryKey: ['ontology', projectId] })
              await qc.invalidateQueries({ queryKey: ['iterations', projectId] })
            }
          }
        }

        // If we found and executed planned/prepared iterations, start over
        if (foundPlannedOrPrepared) {
          continue
        }

        // Step 2: Check all areas for iterations in 'suggested' state
        let foundSuggested = false
        for (const area of areas) {
          if (useOperationsStore.getState().bigAutopilotStopRequested) break

          const iterationsList = await api.listIterations(projectId, area.id)
          
          // Find iterations in suggested state
          const suggestedIterations = [
            ...iterationsList.planned_iterations,
            ...(iterationsList.current_iteration ? [iterationsList.current_iteration] : [])
          ].filter(it => it.status === 'suggested')

          if (suggestedIterations.length > 0) {
            foundSuggested = true
            
            // Update progress
            ops.updateBigAutopilotProgress({
              currentAreaId: area.id,
              currentAreaName: area.label,
            })

            // Execute each one completely before moving to the next
            for (const iteration of suggestedIterations) {
              if (useOperationsStore.getState().bigAutopilotStopRequested) break

              // Update progress with iteration name
              ops.updateBigAutopilotProgress({
                currentIterationName: iteration.name,
              })

              await executeIteration(projectId, iteration.id, area.id, changesStore)
              totalIterationsCompleted++
              
              // Update progress
              const currentProgress = useOperationsStore.getState().bigAutopilotProgress
              ops.updateBigAutopilotProgress({
                totalIterationsCompleted: totalIterationsCompleted,
                currentIterationName: null,
              })

              // Refresh ontology after each iteration
              await qc.invalidateQueries({ queryKey: ['ontology', projectId] })
              await qc.invalidateQueries({ queryKey: ['iterations', projectId] })
            }
          }
        }

        // If we found and executed suggested iterations, start over
        if (foundSuggested) {
          continue
        }

        // Step 3: No planned iterations exist - find first area under the limit and suggest new ones
        let foundAreaToSuggest = false
        
        for (const area of areas) {
          if (useOperationsStore.getState().bigAutopilotStopRequested) break
          
          // Skip areas that already returned < 3 iterations
          if (areasNoMoreSuggestions.has(area.id)) {
            continue
          }

          // Get iterations for this area
          const iterationsList = await api.listIterations(projectId, area.id)
          
          // Count completed iterations for this area
          const completedCount = iterationsList.finished_iterations.length

          // Check if this area is under the limit
          if (completedCount < maxIterationsPerArea) {
            foundAreaToSuggest = true
            
            // Update progress
            ops.updateBigAutopilotProgress({
              currentAreaId: area.id,
              currentAreaName: area.label,
            })

            // Suggest 3 new iterations
            const newIterations = await api.suggestIterations(projectId, {
              focused_area_id: area.id,
              count: 3,
            })

            // If we got less than 3, mark this area as done
            if (newIterations.length < 3) {
              areasNoMoreSuggestions.add(area.id)
            }

            // If no iterations were returned, continue to next area
            if (newIterations.length === 0) {
              continue
            }

            // Refresh iterations list
            await qc.invalidateQueries({ queryKey: ['iterations', projectId, area.id] })
            
            // Break out to start over from step 1 (the new iterations will be picked up as 'suggested')
            break
          }
        }

        // If we found an area and requested suggestions, start over
        if (foundAreaToSuggest) {
          continue
        }

        // Step 4: No more work to do - all areas are either at limit or can't get more suggestions
        break
      }

      // All areas processed or stopped
      ops.stopBigAutopilot()
      alert('Big autopilot completed!')
    } catch (error) {
      console.error('Big autopilot failed:', error)
      alert(`Big autopilot failed: ${error instanceof Error ? error.message : 'Unknown error'}`)
      ops.stopBigAutopilot()
    }
  }

  const executeIteration = async (
    projectId: string,
    iterationId: string,
    areaId: string,
    changesStore: ReturnType<typeof useOntologyChangesStore.getState>
  ) => {
    const opsStore = useOperationsStore.getState()

    try {
      // Get the iteration details
      const iteration = await api.getIteration(projectId, iterationId)

      // Step 1: Plan Tasks (if not already planned)
      if (iteration.status === 'suggested') {
        ops.setPlanningTasks(iterationId)
        await api.planTasks(projectId, iterationId)
        await qc.invalidateQueries({ queryKey: ['iterations', projectId, areaId] })
        ops.setPlanningTasks(null)
      }

      // Step 2: Prepare Iteration (if not already prepared)
      if (iteration.status === 'planned' || iteration.status === 'suggested') {
        ops.setPreparingIteration(iterationId)
        const prepared = await api.prepareIteration(projectId, iterationId)
        ops.open(prepared.iteration_id, prepared.operations)
        await qc.invalidateQueries({ queryKey: ['iterations', projectId, areaId] })
        ops.setPreparingIteration(null)
      }

      // Step 3: Apply Iteration
      ops.setApplyingIteration(iterationId)
      const cachedOps = opsStore.operationsCache[iterationId]
      await api.applyIteration(projectId, iterationId, cachedOps)

      // Record the changes for highlighting in ontology view
      if (cachedOps && cachedOps.length > 0) {
        changesStore.recordChanges(iterationId, cachedOps)
      }

      // Invalidate queries
      await qc.invalidateQueries({ queryKey: ['ontology', projectId] })
      await qc.invalidateQueries({ queryKey: ['iterations', projectId, areaId] })

      // Clear the drawer if it's open for this iteration
      if (opsStore.iterationId === iterationId) {
        ops.close()
        ops.clear()
      }

      ops.setApplyingIteration(null)
    } catch (error) {
      console.error('Failed to execute iteration:', error)
      ops.setPlanningTasks(null)
      ops.setPreparingIteration(null)
      ops.setApplyingIteration(null)
      throw error
    }
  }

  return (
    <Modal title="Big Autopilot Configuration" onClose={onClose}>
      <div className="space-y-4">
        <div className="text-sm text-gray-600">
          The big autopilot will automatically process all domain areas in your project following this algorithm:
        </div>
        <ul className="text-sm text-gray-600 list-disc list-inside space-y-1">
          <li>First, complete all iterations in 'planned' or 'prepared' state across all areas (one at a time)</li>
          <li>Then, complete all iterations in 'suggested' state across all areas (one at a time)</li>
          <li>Finally, for areas under the limit, suggest 3 new iterations and repeat the process</li>
          <li>If an area returns fewer than 3 iterations, it won't request more for that area</li>
        </ul>
        <div className="text-sm text-red-600">
          ⚠️ This process can take a significant amount of time. The ontology will be updated
          after each iteration so you can monitor progress.
        </div>
        <div className="space-y-2">
          <label className="block text-sm font-medium">
            Maximum Completed Iterations Per Area
          </label>
          <input
            type="number"
            min={1}
            max={100}
            className="border rounded-card px-3 py-2 w-32"
            value={maxIterationsPerArea}
            onChange={(e) => setMaxIterationsPerArea(Number(e.target.value))}
          />
          <div className="text-xs text-gray-500">
            The autopilot will stop requesting new iterations for an area once it has this many completed iterations.
          </div>
        </div>
        <div className="flex justify-end gap-2 pt-4">
          <button
            className="px-4 py-2 border rounded-card hover:bg-gray-50"
            onClick={onClose}
          >
            Cancel
          </button>
          <button
            className="px-4 py-2 bg-purple-600 text-white rounded-card hover:bg-purple-700"
            onClick={handleStart}
          >
            🤖 Start Big Autopilot
          </button>
        </div>
      </div>
    </Modal>
  )
}
