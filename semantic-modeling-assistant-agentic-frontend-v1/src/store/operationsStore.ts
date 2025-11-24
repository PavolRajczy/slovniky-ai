import { create } from 'zustand'
import type { OntologyOperationModel } from '@/lib/api'

type OperationsState = {
  visible: boolean
  iterationId: string | null
  operations: OntologyOperationModel[]
  // Cache operations by iteration ID so we can reopen them
  operationsCache: Record<string, OntologyOperationModel[]>
  
  // Loading states for async operations (persisted across tab switches)
  planningTasks: string | null // iterationId currently planning tasks
  preparingIteration: string | null // iterationId currently being prepared
  applyingIteration: string | null // iterationId currently being applied
  suggestingIterations: boolean // true when suggesting iterations
  autopilotRunning: string | null // iterationId currently running in autopilot mode
  
  // Big autopilot state
  bigAutopilotRunning: boolean // true when big autopilot is running across all areas
  bigAutopilotStopRequested: boolean // true when user requested to stop big autopilot
  bigAutopilotConfig: {
    maxIterationsPerArea: number
  }
  bigAutopilotProgress: {
    currentAreaId: string | null
    currentAreaName: string | null
    currentIterationName: string | null
    iterationsCompletedInArea: number
    totalAreasProcessed: number
    totalIterationsCompleted: number
  }
  
  open: (iterationId: string, operations: OntologyOperationModel[]) => void
  close: () => void
  clear: () => void
  
  // Loading state setters
  setPlanningTasks: (iterationId: string | null) => void
  setPreparingIteration: (iterationId: string | null) => void
  setApplyingIteration: (iterationId: string | null) => void
  setSuggestingIterations: (suggesting: boolean) => void
  setAutopilotRunning: (iterationId: string | null) => void
  
  // Big autopilot control
  startBigAutopilot: (maxIterationsPerArea: number) => void
  stopBigAutopilot: () => void
  requestStopBigAutopilot: () => void
  updateBigAutopilotProgress: (progress: Partial<OperationsState['bigAutopilotProgress']>) => void
}

export const useOperationsStore = create<OperationsState>((set, get) => ({
  visible: false,
  iterationId: null,
  operations: [],
  operationsCache: {},
  planningTasks: null,
  preparingIteration: null,
  applyingIteration: null,
  suggestingIterations: false,
  autopilotRunning: null,
  
  // Big autopilot initial state
  bigAutopilotRunning: false,
  bigAutopilotStopRequested: false,
  bigAutopilotConfig: {
    maxIterationsPerArea: 10,
  },
  bigAutopilotProgress: {
    currentAreaId: null,
    currentAreaName: null,
    currentIterationName: null,
    iterationsCompletedInArea: 0,
    totalAreasProcessed: 0,
    totalIterationsCompleted: 0,
  },
  
  open: (iterationId, operations) => {
    // Cache the operations for this iteration
    const cache = { ...get().operationsCache, [iterationId]: operations }
    set({ visible: true, iterationId, operations, operationsCache: cache })
  },
  close: () => set({ visible: false }),
  clear: () => set({ iterationId: null, operations: [] }),
  // Note: We keep operationsCache even after clear, so we can reopen later
  
  setPlanningTasks: (iterationId) => set({ planningTasks: iterationId }),
  setPreparingIteration: (iterationId) => set({ preparingIteration: iterationId }),
  setApplyingIteration: (iterationId) => set({ applyingIteration: iterationId }),
  setSuggestingIterations: (suggesting) => set({ suggestingIterations: suggesting }),
  setAutopilotRunning: (iterationId) => set({ autopilotRunning: iterationId }),
  
  // Big autopilot control functions
  startBigAutopilot: (maxIterationsPerArea) => set({
    bigAutopilotRunning: true,
    bigAutopilotStopRequested: false,
    bigAutopilotConfig: { maxIterationsPerArea },
    bigAutopilotProgress: {
      currentAreaId: null,
      currentAreaName: null,
      currentIterationName: null,
      iterationsCompletedInArea: 0,
      totalAreasProcessed: 0,
      totalIterationsCompleted: 0,
    },
  }),
  requestStopBigAutopilot: () => set({ bigAutopilotStopRequested: true }),
  stopBigAutopilot: () => set({
    bigAutopilotRunning: false,
    bigAutopilotStopRequested: false,
  }),
  updateBigAutopilotProgress: (progress) => set((state) => ({
    bigAutopilotProgress: { ...state.bigAutopilotProgress, ...progress },
  })),
}))
