import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'

export interface NodePosition {
  x: number
  y: number
  timestamp: number
}

export interface NodePositionsState {
  // Map structure: key = `${projectId}:${nodeUri}`
  positions: Map<string, NodePosition>
  
  // Actions
  pinNode: (projectId: string, nodeUri: string, x: number, y: number) => void
  unpinNode: (projectId: string, nodeUri: string) => void
  getPosition: (projectId: string, nodeUri: string) => NodePosition | null
  hasPosition: (projectId: string, nodeUri: string) => boolean
  clearProject: (projectId: string) => void
  clearAll: () => void
  pruneOldPositions: (maxAgeMs: number) => void
  getProjectPositions: (projectId: string) => Map<string, NodePosition>
}

export const useNodePositionsStore = create<NodePositionsState>()(
  persist(
    (set, get) => ({
      positions: new Map(),
      
      pinNode: (projectId, nodeUri, x, y) => {
        set(state => {
          const key = `${projectId}:${nodeUri}`
          const newPositions = new Map(state.positions)
          newPositions.set(key, { x, y, timestamp: Date.now() })
          return { positions: newPositions }
        })
      },
      
      unpinNode: (projectId, nodeUri) => {
        set(state => {
          const key = `${projectId}:${nodeUri}`
          const newPositions = new Map(state.positions)
          newPositions.delete(key)
          return { positions: newPositions }
        })
      },
      
      getPosition: (projectId, nodeUri) => {
        const key = `${projectId}:${nodeUri}`
        return get().positions.get(key) || null
      },
      
      hasPosition: (projectId, nodeUri) => {
        const key = `${projectId}:${nodeUri}`
        return get().positions.has(key)
      },
      
      clearProject: (projectId) => {
        set(state => {
          const newPositions = new Map(state.positions)
          for (const key of newPositions.keys()) {
            if (key.startsWith(`${projectId}:`)) {
              newPositions.delete(key)
            }
          }
          return { positions: newPositions }
        })
      },
      
      clearAll: () => {
        set({ positions: new Map() })
      },
      
      pruneOldPositions: (maxAgeMs) => {
        set(state => {
          const now = Date.now()
          const newPositions = new Map(state.positions)
          let prunedCount = 0
          
          for (const [key, pos] of newPositions.entries()) {
            if (now - pos.timestamp > maxAgeMs) {
              newPositions.delete(key)
              prunedCount++
            }
          }
          
          if (prunedCount > 0) {
            console.log(`🧹 Pruned ${prunedCount} old node positions`)
          }
          
          return { positions: newPositions }
        })
      },
      
      getProjectPositions: (projectId) => {
        const projectPositions = new Map<string, NodePosition>()
        const allPositions = get().positions
        
        for (const [key, pos] of allPositions.entries()) {
          if (key.startsWith(`${projectId}:`)) {
            const nodeUri = key.substring(projectId.length + 1)
            projectPositions.set(nodeUri, pos)
          }
        }
        
        return projectPositions
      },
    }),
    {
      name: 'ontology-node-positions',
      storage: createJSONStorage(() => localStorage),
      // Custom serialization for Map -> Array conversion
      serialize: (state) => {
        return JSON.stringify({
          ...state,
          state: {
            ...state.state,
            positions: Array.from(state.state.positions.entries()),
          },
        })
      },
      // Custom deserialization for Array -> Map conversion
      deserialize: (str) => {
        const parsed = JSON.parse(str)
        return {
          ...parsed,
          state: {
            ...parsed.state,
            positions: new Map(parsed.state.positions || []),
          },
        }
      },
      // Version for future schema changes
      version: 1,
    }
  )
)
