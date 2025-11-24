import type { OntologyModel } from './api'
import type { OntologyChanges, FilteredElements, FilterMode } from '@/store/ontologyChangesStore'

/**
 * Computes which elements should be visible based on the filter mode
 */
export function computeFilteredElements(
  ontology: OntologyModel,
  changes: OntologyChanges,
  filterMode: FilterMode
): FilteredElements {
  
  // Start with directly changed elements
  const changedClasses = new Set(changes.classes.keys())
  const changedAttributes = new Set(changes.attributes.keys())
  const changedRelationships = new Set(changes.relationships.keys())
  
  // Find classes required as endpoints for changed relationships
  const requiredClasses = new Set<string>()
  
  // Add classes needed for changed relationships
  ontology.relationships?.forEach(rel => {
    if (changedRelationships.has(rel.uri)) {
      if (!changedClasses.has(rel.domain_class)) {
        requiredClasses.add(rel.domain_class)
      }
      if (!changedClasses.has(rel.range_class)) {
        requiredClasses.add(rel.range_class)
      }
    }
  })
  
  // Add classes needed for changed inheritance (entire chain from root to changed class)
  const addInheritanceChain = (classUri: string, visitedChain = new Set<string>()) => {
    // Prevent infinite loops
    if (visitedChain.has(classUri)) return
    visitedChain.add(classUri)
    
    const cls = ontology.classes?.find(c => c.uri === classUri)
    if (!cls) return
    
    // Add all parent classes recursively (going up to root)
    cls.parent_classes?.forEach(parentUri => {
      if (!changedClasses.has(parentUri)) {
        requiredClasses.add(parentUri)
      }
      // Recursively add parent's parents
      addInheritanceChain(parentUri, visitedChain)
    })
  }
  
  // For each changed class, add its inheritance chain to root
  changedClasses.forEach(classUri => {
    addInheritanceChain(classUri)
  })
  
  // Also check if any unchanged class has changed children (add it as required)
  ontology.classes?.forEach(cls => {
    const hasChangedChildren = ontology.classes?.some(child =>
      changedClasses.has(child.uri) && 
      child.parent_classes?.includes(cls.uri)
    )
    if (hasChangedChildren && !changedClasses.has(cls.uri)) {
      requiredClasses.add(cls.uri)
    }
  })
  
  // Find connected classes (1-hop from changed elements)
  const connectedClasses = new Set<string>()
  
  if (filterMode === 'connected') {
    // Add classes connected via relationships (in either direction)
    ontology.relationships?.forEach(rel => {
      // If domain is changed, add range
      if (changedClasses.has(rel.domain_class)) {
        if (!changedClasses.has(rel.range_class) && !requiredClasses.has(rel.range_class)) {
          connectedClasses.add(rel.range_class)
        }
      }
      // If range is changed, add domain
      if (changedClasses.has(rel.range_class)) {
        if (!changedClasses.has(rel.domain_class) && !requiredClasses.has(rel.domain_class)) {
          connectedClasses.add(rel.domain_class)
        }
      }
    })
    
    // Add classes connected via inheritance (children and parents)
    ontology.classes?.forEach(cls => {
      // If class has changed parents, add the class
      const hasChangedParents = cls.parent_classes?.some(p => changedClasses.has(p))
      if (hasChangedParents && !changedClasses.has(cls.uri) && !requiredClasses.has(cls.uri)) {
        connectedClasses.add(cls.uri)
      }
      
      // If class is parent of changed class, was already added by addInheritanceChain
      // But we need to add siblings and children
      if (changedClasses.has(cls.uri)) {
        // Add all children
        ontology.classes?.forEach(child => {
          if (child.parent_classes?.includes(cls.uri) &&
              !changedClasses.has(child.uri) &&
              !requiredClasses.has(child.uri)) {
            connectedClasses.add(child.uri)
          }
        })
        
        // Add siblings (classes with same parents)
        cls.parent_classes?.forEach(parentUri => {
          ontology.classes?.forEach(sibling => {
            if (sibling.uri !== cls.uri &&
                sibling.parent_classes?.includes(parentUri) &&
                !changedClasses.has(sibling.uri) &&
                !requiredClasses.has(sibling.uri)) {
              connectedClasses.add(sibling.uri)
            }
          })
        })
      }
    })
  }
  
  // Compute final visible sets based on filter mode
  let visibleClasses: Set<string>
  let visibleAttributes: Set<string>
  let visibleRelationships: Set<string>
  let visibleInheritances: Set<string>
  
  switch (filterMode) {
    case 'all':
      // Show everything
      visibleClasses = new Set(ontology.classes?.map(c => c.uri) || [])
      visibleAttributes = new Set(ontology.attributes?.map(a => a.uri) || [])
      visibleRelationships = new Set(ontology.relationships?.map(r => r.uri) || [])
      visibleInheritances = new Set<string>()
      ontology.classes?.forEach(cls => {
        cls.parent_classes?.forEach(parentUri => {
          visibleInheritances.add(`${cls.uri}->${parentUri}`)
        })
      })
      break
      
    case 'changed':
      // Show only changed + required
      visibleClasses = new Set([...changedClasses, ...requiredClasses])
      
      // Attributes: only changed ones that belong to visible classes
      visibleAttributes = new Set<string>()
      ontology.attributes?.forEach(attr => {
        if (changedAttributes.has(attr.uri) && visibleClasses.has(attr.domain_class)) {
          visibleAttributes.add(attr.uri)
        }
      })
      
      // Relationships: only changed ones (endpoints already in visibleClasses)
      visibleRelationships = new Set(changedRelationships)
      
      // Inheritances: only between visible classes
      visibleInheritances = new Set<string>()
      ontology.classes?.forEach(cls => {
        if (visibleClasses.has(cls.uri)) {
          cls.parent_classes?.forEach(parentUri => {
            if (visibleClasses.has(parentUri)) {
              visibleInheritances.add(`${cls.uri}->${parentUri}`)
            }
          })
        }
      })
      break
      
    case 'connected':
      // Show changed + required + connected
      visibleClasses = new Set([...changedClasses, ...requiredClasses, ...connectedClasses])
      
      // Attributes: changed ones + attributes of connected classes
      visibleAttributes = new Set<string>()
      ontology.attributes?.forEach(attr => {
        if ((changedAttributes.has(attr.uri) || connectedClasses.has(attr.domain_class)) &&
            visibleClasses.has(attr.domain_class)) {
          visibleAttributes.add(attr.uri)
        }
      })
      
      // Relationships: changed ones + relationships involving connected classes
      visibleRelationships = new Set<string>()
      ontology.relationships?.forEach(rel => {
        if (changedRelationships.has(rel.uri) ||
            (connectedClasses.has(rel.domain_class) || connectedClasses.has(rel.range_class))) {
          // Only include if both endpoints are visible
          if (visibleClasses.has(rel.domain_class) && visibleClasses.has(rel.range_class)) {
            visibleRelationships.add(rel.uri)
          }
        }
      })
      
      // Inheritances: all between visible classes
      visibleInheritances = new Set<string>()
      ontology.classes?.forEach(cls => {
        if (visibleClasses.has(cls.uri)) {
          cls.parent_classes?.forEach(parentUri => {
            if (visibleClasses.has(parentUri)) {
              visibleInheritances.add(`${cls.uri}->${parentUri}`)
            }
          })
        }
      })
      break
  }
  
  return {
    changedClasses,
    changedAttributes,
    changedRelationships,
    requiredClasses,
    connectedClasses,
    visibleClasses,
    visibleAttributes,
    visibleRelationships,
    visibleInheritances,
  }
}

/**
 * Helper to determine if a class is required (shown as endpoint) vs changed
 */
export function getClassDisplayType(
  classUri: string,
  filtered: FilteredElements
): 'changed' | 'required' | 'connected' | 'normal' {
  if (filtered.changedClasses.has(classUri)) return 'changed'
  if (filtered.requiredClasses.has(classUri)) return 'required'
  if (filtered.connectedClasses.has(classUri)) return 'connected'
  return 'normal'
}
