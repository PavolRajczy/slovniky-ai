import { create } from 'zustand'
import type { OntologyOperationModel, OntologyModel } from '@/lib/api'
import { computeFilteredElements } from '@/lib/ontologyFiltering'

export type ChangeType = 'created' | 'deleted' | 'modified'

export type OntologyChanges = {
  classes: Map<string, ChangeType>
  attributes: Map<string, ChangeType>
  relationships: Map<string, ChangeType>
  inheritances: Map<string, ChangeType> // key: "childUri->parentUri"
}

export type FilterMode = 'all' | 'changed' | 'connected'

export type FilteredElements = {
  // Elements that were directly changed
  changedClasses: Set<string>
  changedAttributes: Set<string>
  changedRelationships: Set<string>
  
  // Classes needed as endpoints (not changed themselves)
  requiredClasses: Set<string>
  
  // Classes connected to changed elements (1-hop)
  connectedClasses: Set<string>
  
  // Final sets to display
  visibleClasses: Set<string>
  visibleAttributes: Set<string>
  visibleRelationships: Set<string>
  visibleInheritances: Set<string> // "childUri->parentUri"
}

type OntologyChangesState = {
  changes: OntologyChanges | null
  lastAppliedIterationId: string | null
  lastAppliedOperations: OntologyOperationModel[] | null
  showChanges: boolean
  filterMode: FilterMode
  filteredElements: FilteredElements | null
  
  recordChanges: (iterationId: string, operations: OntologyOperationModel[]) => void
  clearChanges: () => void
  toggleShowChanges: () => void
  setShowChanges: (show: boolean) => void
  setFilterMode: (mode: FilterMode) => void
  updateFilteredElements: (ontology: OntologyModel) => void
}

// Helper to compute changes from operations
function computeChangesFromOperations(operations: OntologyOperationModel[]): OntologyChanges {
  // First pass: collect all operations by element URI
  const classOps = new Map<string, OntologyOperationModel[]>()
  const attributeOps = new Map<string, OntologyOperationModel[]>()
  const relationshipOps = new Map<string, OntologyOperationModel[]>()

  operations.forEach(op => {
    switch (op.target_type) {
      case 'class':
        if (!classOps.has(op.uri)) classOps.set(op.uri, [])
        classOps.get(op.uri)!.push(op)
        break
      case 'attribute':
        if (!attributeOps.has(op.uri)) attributeOps.set(op.uri, [])
        attributeOps.get(op.uri)!.push(op)
        break
      case 'relationship':
        if (!relationshipOps.has(op.uri)) relationshipOps.set(op.uri, [])
        relationshipOps.get(op.uri)!.push(op)
        break
    }
  })

  // Helper to determine the final change type for an element
  const resolveFinalChangeType = (ops: OntologyOperationModel[]): ChangeType | null => {
    const hasCreate = ops.some(op => op.operation_type === 'create')
    const hasDelete = ops.some(op => op.operation_type === 'delete')
    const hasUpdate = ops.some(op => op.operation_type === 'update')

    // Rule 4: Created and then deleted = no net change (element won't exist)
    if (hasCreate && hasDelete) {
      return null
    }

    // Rule 3: Edited (one or more times) and then deleted = deleted
    if (hasDelete) {
      return 'deleted'
    }

    // Rule 1: Created (and optionally edited) = created
    if (hasCreate) {
      return 'created'
    }

    // Rule 2: Only edits = modified
    if (hasUpdate) {
      return 'modified'
    }

    return null
  }

  const changes: OntologyChanges = {
    classes: new Map(),
    attributes: new Map(),
    relationships: new Map(),
    inheritances: new Map(),
  }

  // Process classes
  for (const [uri, ops] of classOps.entries()) {
    const changeType = resolveFinalChangeType(ops)
    if (changeType) {
      changes.classes.set(uri, changeType)

      // Track inheritance changes for classes
      // Use the last operation that has generalization_uris
      const lastOpWithGeneralizations = [...ops].reverse().find(op => 
        op.generalization_uris && op.generalization_uris.length > 0
      )
      
      if (lastOpWithGeneralizations?.generalization_uris) {
        lastOpWithGeneralizations.generalization_uris.forEach(parentUri => {
          const key = `${uri}->${parentUri}`
          // Inheritance change type follows the class change type
          changes.inheritances.set(key, changeType)
        })
      }
    }
  }

  // Process attributes
  for (const [uri, ops] of attributeOps.entries()) {
    const changeType = resolveFinalChangeType(ops)
    if (changeType) {
      changes.attributes.set(uri, changeType)
    }
  }

  // Process relationships
  for (const [uri, ops] of relationshipOps.entries()) {
    const changeType = resolveFinalChangeType(ops)
    if (changeType) {
      changes.relationships.set(uri, changeType)
      console.log('📝 Recording relationship change:', {
        uri,
        changeType,
        label: ops[ops.length - 1].label,
        operationCount: ops.length,
      })
    } else {
      console.log('📝 Relationship created and deleted (no net change):', {
        uri,
        label: ops[ops.length - 1].label,
      })
    }
  }

  console.log('📊 Changes summary:', {
    classes: changes.classes.size,
    attributes: changes.attributes.size,
    relationships: changes.relationships.size,
    inheritances: changes.inheritances.size,
    relationshipDetails: Array.from(changes.relationships.entries()),
  })

  return changes
}

export const useOntologyChangesStore = create<OntologyChangesState>((set, get) => ({
  changes: null,
  lastAppliedIterationId: null,
  lastAppliedOperations: null,
  showChanges: true, // Show changes by default
  filterMode: 'all', // Show all elements by default
  filteredElements: null,
  
  recordChanges: (iterationId, operations) => {
    const changes = computeChangesFromOperations(operations)
    set({
      changes,
      lastAppliedIterationId: iterationId,
      lastAppliedOperations: operations,
    })
  },
  
  clearChanges: () => {
    set({
      changes: null,
      lastAppliedIterationId: null,
      lastAppliedOperations: null,
      filterMode: 'all', // Reset filter mode when clearing
      filteredElements: null,
    })
  },
  
  toggleShowChanges: () => {
    set(state => ({ showChanges: !state.showChanges }))
  },
  
  setShowChanges: (show) => {
    set({ showChanges: show })
  },
  
  setFilterMode: (mode) => {
    set({ filterMode: mode })
    // Trigger recomputation if we have changes and ontology
    // (will be called by components after this)
  },
  
  updateFilteredElements: (ontology) => {
    const state = get()
    if (!state.changes) {
      set({ filteredElements: null })
      return
    }
    
    const filtered = computeFilteredElements(ontology, state.changes, state.filterMode)
    set({ filteredElements: filtered })
  },
}))
