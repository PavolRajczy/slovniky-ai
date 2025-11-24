import { create } from 'zustand'

type ProjectState = {
  projectId: string | null
  areaId: string | null
  iterationId: string | null
  taskId: string | null
  setProjectId: (id: string | null) => void
  setAreaId: (id: string | null) => void
  setIterationId: (id: string | null) => void
  setTaskId: (id: string | null) => void
}

export const useProjectStore = create<ProjectState>((set) => ({
  projectId: null,
  areaId: null,
  iterationId: null,
  taskId: null,
  setProjectId: (projectId) => set({ projectId }),
  setAreaId: (areaId) => set({ areaId }),
  setIterationId: (iterationId) => set({ iterationId }),
  setTaskId: (taskId) => set({ taskId }),
}))
