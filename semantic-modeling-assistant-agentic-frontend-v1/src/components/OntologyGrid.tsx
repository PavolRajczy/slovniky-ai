import { OntologyModel, OntologyClassModel, OntologyAttributeModel, OntologyRelationshipModel } from '@/lib/api'
import { OntologyChanges, ChangeType, FilteredElements } from '@/store/ontologyChangesStore'
import { getClassDisplayType } from '@/lib/ontologyFiltering'
import { useMemo, useState, useEffect, useRef } from 'react'

export type SelectedElement = 
  | { type: 'class'; uri: string }
  | { type: 'attribute'; uri: string }
  | { type: 'relationship'; uri: string }
  | null

interface OntologyGridProps {
  ontology: OntologyModel
  searchQuery: string
  selectedElement?: SelectedElement
  onSelectElement?: (element: SelectedElement) => void
  changes?: OntologyChanges | null
  filteredElements?: FilteredElements | null
}

interface ClassTreeNode {
  class: OntologyClassModel
  children: ClassTreeNode[]
  level: number
}

export function OntologyGrid({ 
  ontology, 
  searchQuery, 
  selectedElement: externalSelectedElement,
  onSelectElement,
  changes,
  filteredElements
}: OntologyGridProps) {
  const [internalSelectedElement, setInternalSelectedElement] = useState<SelectedElement>(null)
  const [expandedClasses, setExpandedClasses] = useState<Set<string>>(new Set())
  const selectedRowRefs = useRef<{ [key: string]: HTMLTableRowElement | null }>({})

  // Use external state if provided, otherwise use internal state
  const selectedElement = externalSelectedElement !== undefined ? externalSelectedElement : internalSelectedElement

  // Helper to get change type for an element
  const getChangeType = (type: 'class' | 'attribute' | 'relationship', uri: string): ChangeType | null => {
    if (!changes) return null
    switch (type) {
      case 'class':
        return changes.classes.get(uri) || null
      case 'attribute':
        return changes.attributes.get(uri) || null
      case 'relationship':
        return changes.relationships.get(uri) || null
    }
  }

  // Helper to get change styling classes
  const getChangeClasses = (changeType: ChangeType | null): string => {
    if (!changeType) return ''
    switch (changeType) {
      case 'created':
        return 'bg-green-50 border-l-4 border-green-500'
      case 'modified':
        return 'bg-yellow-50 border-l-4 border-yellow-500'
      case 'deleted':
        return 'bg-red-50 border-l-4 border-red-500 opacity-60'
    }
  }

  // Helper to get change badge
  const getChangeBadge = (changeType: ChangeType | null): JSX.Element | null => {
    if (!changeType) return null
    switch (changeType) {
      case 'created':
        return <span className="ml-2 px-2 py-0.5 text-xs font-medium rounded bg-green-100 text-green-700">NEW</span>
      case 'modified':
        return <span className="ml-2 px-2 py-0.5 text-xs font-medium rounded bg-yellow-100 text-yellow-700">MODIFIED</span>
      case 'deleted':
        return <span className="ml-2 px-2 py-0.5 text-xs font-medium rounded bg-red-100 text-red-700">DELETED</span>
    }
  }

  const handleSelect = (element: SelectedElement) => {
    if (onSelectElement) {
      onSelectElement(element)
    } else {
      setInternalSelectedElement(element)
    }
  }

  const toggleExpand = (uri: string, event: React.MouseEvent) => {
    event.stopPropagation()
    setExpandedClasses(prev => {
      const next = new Set(prev)
      if (next.has(uri)) {
        next.delete(uri)
      } else {
        next.add(uri)
      }
      return next
    })
  }

  const expandAll = () => {
    const allParents = new Set<string>()
    ontology.classes?.forEach(cls => {
      if (cls.parent_classes && cls.parent_classes.length > 0) {
        cls.parent_classes.forEach(parent => allParents.add(parent))
      }
    })
    setExpandedClasses(allParents)
  }

  const collapseAll = () => {
    setExpandedClasses(new Set())
  }

  // Build class hierarchy tree
  const classHierarchy = useMemo(() => {
    if (!ontology.classes) return []
    
    const classMap = new Map<string, OntologyClassModel>()
    ontology.classes.forEach(cls => classMap.set(cls.uri, cls))
    
    const rootClasses: ClassTreeNode[] = []
    const visited = new Set<string>()
    
    // Helper to build tree recursively with cycle detection
    const buildNode = (cls: OntologyClassModel, level: number, ancestorChain: Set<string>): ClassTreeNode | null => {
      // Detect circular reference
      if (ancestorChain.has(cls.uri)) {
        console.warn(`Circular reference detected for class: ${cls.uri}`)
        return null
      }
      
      const newChain = new Set(ancestorChain)
      newChain.add(cls.uri)
      
      const children: ClassTreeNode[] = []
      
      // Find all children (classes that have this class as parent)
      ontology.classes?.forEach(potentialChild => {
        if (potentialChild.parent_classes?.includes(cls.uri)) {
          const childNode = buildNode(potentialChild, level + 1, newChain)
          if (childNode) {
            children.push(childNode)
          }
        }
      })
      
      // Sort children by label
      children.sort((a, b) => 
        (a.class.label || a.class.uri).localeCompare(b.class.label || b.class.uri)
      )
      
      return { class: cls, children, level }
    }
    
    // Find root classes (no parents or parents not in ontology)
    ontology.classes.forEach(cls => {
      const hasParentInOntology = cls.parent_classes?.some(parentUri => 
        classMap.has(parentUri)
      )
      
      if (!hasParentInOntology) {
        const node = buildNode(cls, 0, new Set())
        if (node) {
          rootClasses.push(node)
        }
      }
    })
    
    // Sort root classes by label
    rootClasses.sort((a, b) => 
      (a.class.label || a.class.uri).localeCompare(b.class.label || b.class.uri)
    )
    
    return rootClasses
  }, [ontology.classes])

  // Helper to get all ancestor URIs for a class
  const getAncestorChain = (classUri: string, ancestors: Set<string> = new Set()): Set<string> => {
    const cls = ontology.classes?.find(c => c.uri === classUri)
    if (!cls || !cls.parent_classes) return ancestors
    
    cls.parent_classes.forEach(parentUri => {
      if (!ancestors.has(parentUri)) {
        ancestors.add(parentUri)
        getAncestorChain(parentUri, ancestors)
      }
    })
    
    return ancestors
  }

  // Helper to check if a node or its descendants match the filter
  const nodeMatchesFilter = (node: ClassTreeNode, query: string): boolean => {
    const cls = node.class
    const lowerQuery = query.toLowerCase()
    
    // Check if this node matches
    const matches = 
      cls.label?.toLowerCase().includes(lowerQuery) ||
      cls.uri.toLowerCase().includes(lowerQuery) ||
      cls.description?.toLowerCase().includes(lowerQuery) ||
      cls.definition?.toLowerCase().includes(lowerQuery)
    
    if (matches) return true
    
    // Check if any descendant matches
    return node.children.some(child => nodeMatchesFilter(child, query))
  }

  // Helper to check if node should be visible based on semantic filter
  const nodeMatchesSemanticFilter = (node: ClassTreeNode): boolean => {
    // If attribute selected, only show its domain class
    if (selectedElement?.type === 'attribute') {
      const attr = ontology.attributes?.find(a => a.uri === selectedElement.uri)
      return attr ? node.class.uri === attr.domain_class : false
    }
    
    // If relationship selected, only show connected classes
    if (selectedElement?.type === 'relationship') {
      const rel = ontology.relationships?.find(r => r.uri === selectedElement.uri)
      return rel ? 
        (node.class.uri === rel.domain_class || node.class.uri === rel.range_class) : 
        false
    }
    
    return true
  }

  // Auto-expand ancestors when filtering or navigating
  useEffect(() => {
    const toExpand = new Set<string>()
    
    // Only auto-expand for search or attribute/relationship selection
    // NOT for class selection (that's handled in the separate useEffect below)
    const shouldAutoExpand = searchQuery || (selectedElement && selectedElement.type !== 'class')
    
    if (!shouldAutoExpand) return
    
    // Helper to collect all URIs in tree
    const collectMatchingNodes = (node: ClassTreeNode): void => {
      let shouldExpand = false
      
      // Check if node matches search
      if (searchQuery && nodeMatchesFilter(node, searchQuery)) {
        shouldExpand = true
      }
      
      // Check if node matches semantic filter (only for attribute/relationship)
      if (selectedElement && selectedElement.type !== 'class' && nodeMatchesSemanticFilter(node)) {
        shouldExpand = true
      }
      
      // If this node should be visible, expand all its ancestors
      if (shouldExpand) {
        const ancestors = getAncestorChain(node.class.uri)
        ancestors.forEach(uri => toExpand.add(uri))
      }
      
      // Recursively check children
      node.children.forEach(child => collectMatchingNodes(child))
    }
    
    // Collect all nodes that should cause expansion
    classHierarchy.forEach(root => collectMatchingNodes(root))
    
    // Merge with existing expanded state
    if (toExpand.size > 0) {
      setExpandedClasses(prev => new Set([...prev, ...toExpand]))
    }
  }, [searchQuery, selectedElement, classHierarchy])

  // Auto-expand and scroll when navigating to a class
  useEffect(() => {
    if (selectedElement?.type === 'class') {
      // Expand ancestor chain
      const ancestors = getAncestorChain(selectedElement.uri)
      if (ancestors.size > 0) {
        setExpandedClasses(prev => new Set([...prev, ...ancestors]))
      }
      
      // Scroll after a brief delay to allow expansion
      setTimeout(() => {
        const key = `class-${selectedElement.uri}`
        const rowElement = selectedRowRefs.current[key]
        
        if (rowElement) {
          rowElement.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'center',
            inline: 'nearest'
          })
        }
      }, 100)
    }
  }, [selectedElement])

  // Scroll to selected attribute/relationship
  useEffect(() => {
    if (selectedElement && selectedElement.type !== 'class') {
      const key = `${selectedElement.type}-${selectedElement.uri}`
      const rowElement = selectedRowRefs.current[key]
      
      if (rowElement) {
        rowElement.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'center',
          inline: 'nearest'
        })
      }
    }
  }, [selectedElement])

  // Flatten tree for rendering, respecting collapse state
  const flattenTree = (nodes: ClassTreeNode[], parentCollapsed: boolean = false): OntologyClassModel[] => {
    const result: OntologyClassModel[] = []
    
    nodes.forEach(node => {
      // Check if node should be visible based on filters
      const matchesSearch = !searchQuery || nodeMatchesFilter(node, searchQuery)
      const matchesSemantic = !selectedElement || selectedElement.type === 'class' || nodeMatchesSemanticFilter(node)
      
      if (matchesSearch && matchesSemantic && !parentCollapsed) {
        result.push(node.class)
        
        // Add children if expanded (or if searching/filtering)
        const isExpanded = expandedClasses.has(node.class.uri)
        const shouldAutoExpand = searchQuery || (selectedElement && selectedElement.type !== 'class')
        
        if (node.children.length > 0 && (isExpanded || shouldAutoExpand)) {
          result.push(...flattenTree(node.children, false))
        } else if (node.children.length > 0 && !isExpanded) {
          // Children exist but are collapsed
          result.push(...flattenTree(node.children, true))
        }
      } else if (!matchesSearch || !matchesSemantic) {
        // Node doesn't match, but check children
        result.push(...flattenTree(node.children, parentCollapsed))
      }
    })
    
    return result
  }

  // Helper to get node by URI
  const getNodeByUri = (uri: string, nodes: ClassTreeNode[] = classHierarchy): ClassTreeNode | null => {
    for (const node of nodes) {
      if (node.class.uri === uri) return node
      const found = getNodeByUri(uri, node.children)
      if (found) return found
    }
    return null
  }

  // Helper to count children
  const countChildren = (node: ClassTreeNode): number => {
    let count = node.children.length
    node.children.forEach(child => {
      count += countChildren(child)
    })
    return count
  }

  // Get filtered classes with hierarchy
  const filteredClasses = useMemo(() => {
    let classes = flattenTree(classHierarchy)
    
    // Apply filter mode if filteredElements is available
    if (filteredElements) {
      classes = classes.filter(cls => filteredElements.visibleClasses.has(cls.uri))
    }
    
    return classes
  }, [classHierarchy, expandedClasses, searchQuery, selectedElement, filteredElements])

  // Filter attributes based on selection
  const filteredAttributes = useMemo(() => {
    if (!ontology.attributes) return []
    
    let attrs = ontology.attributes

    // Apply filter mode if filteredElements is available
    if (filteredElements) {
      attrs = attrs.filter(attr => filteredElements.visibleAttributes.has(attr.uri))
    }

    // Filter by selected class
    if (selectedElement?.type === 'class') {
      attrs = attrs.filter(attr => attr.domain_class === selectedElement.uri)
    }
    
    // Filter by selected attribute (only show itself)
    if (selectedElement?.type === 'attribute') {
      attrs = attrs.filter(attr => attr.uri === selectedElement.uri)
    }

    // Filter by selected relationship (no attributes)
    if (selectedElement?.type === 'relationship') {
      return []
    }

    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      attrs = attrs.filter(attr =>
        attr.label.toLowerCase().includes(query) ||
        attr.uri.toLowerCase().includes(query) ||
        (attr.description && attr.description.toLowerCase().includes(query)) ||
        (attr.definition && attr.definition.toLowerCase().includes(query))
      )
    }

    return attrs
  }, [ontology.attributes, selectedElement, searchQuery, filteredElements])

  // Filter relationships based on selection
  const filteredRelationships = useMemo(() => {
    if (!ontology.relationships) return []
    
    let rels = ontology.relationships

    // Apply filter mode if filteredElements is available
    if (filteredElements) {
      rels = rels.filter(rel => filteredElements.visibleRelationships.has(rel.uri))
    }

    // Filter by selected class
    if (selectedElement?.type === 'class') {
      rels = rels.filter(rel => 
        rel.domain_class === selectedElement.uri || 
        rel.range_class === selectedElement.uri
      )
    }

    // Filter by selected attribute (no relationships)
    if (selectedElement?.type === 'attribute') {
      return []
    }

    // Filter by selected relationship (only show itself)
    if (selectedElement?.type === 'relationship') {
      rels = rels.filter(rel => rel.uri === selectedElement.uri)
    }

    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase()
      rels = rels.filter(rel =>
        rel.label.toLowerCase().includes(query) ||
        rel.uri.toLowerCase().includes(query) ||
        (rel.description && rel.description.toLowerCase().includes(query)) ||
        (rel.definition && rel.definition.toLowerCase().includes(query))
      )
    }

    return rels
  }, [ontology.relationships, selectedElement, searchQuery, filteredElements])

  const renderClassRow = (cls: OntologyClassModel) => {
    const isSelected = selectedElement?.type === 'class' && selectedElement.uri === cls.uri
    const rowKey = `class-${cls.uri}`
    const node = getNodeByUri(cls.uri)
    const hasChildren = node && node.children.length > 0
    const isExpanded = expandedClasses.has(cls.uri)
    const level = node?.level || 0
    const childCount = node ? countChildren(node) : 0
    const changeType = getChangeType('class', cls.uri)
    const changeClasses = getChangeClasses(changeType)
    const changeBadge = getChangeBadge(changeType)
    
    // Get display type (changed/required/connected)
    const displayType = filteredElements ? getClassDisplayType(cls.uri, filteredElements) : 'normal'
    
    return (
      <tr 
        key={cls.uri}
        ref={(el) => { selectedRowRefs.current[rowKey] = el }}
        className={`cursor-pointer transition-colors ${
          isSelected 
            ? 'bg-blue-100 hover:bg-blue-200' 
            : changeClasses || 'hover:bg-gray-50'
        }`}
        onClick={() => handleSelect({ type: 'class', uri: cls.uri })}
      >
        <td className="px-3 py-2">
          <div className="flex items-start gap-1" style={{ paddingLeft: `${level * 16}px` }}>
            {/* Expand/collapse icon */}
            {hasChildren ? (
              <button
                className="flex-shrink-0 w-4 h-4 flex items-center justify-center text-gray-500 hover:text-gray-700 focus:outline-none mt-0.5"
                onClick={(e) => toggleExpand(cls.uri, e)}
                aria-label={isExpanded ? 'Collapse' : 'Expand'}
              >
                {isExpanded ? '▼' : '▶'}
              </button>
            ) : (
              <span className="w-4 flex-shrink-0"></span>
            )}
            
            {/* Class info */}
            <div className="flex-1 min-w-0">
              <div className="font-medium text-sm text-gray-900 flex items-center gap-2">
                <span>{cls.label}</span>
                {changeBadge}
                {displayType === 'required' && (
                  <span className="text-xs bg-purple-100 text-purple-700 px-1.5 py-0.5 rounded font-medium" title="Required as endpoint">
                    endpoint
                  </span>
                )}
                {displayType === 'connected' && (
                  <span className="text-xs bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded font-medium" title="Connected to changed elements">
                    connected
                  </span>
                )}
                {hasChildren && !isExpanded && (
                  <span className="text-xs bg-gray-200 text-gray-600 px-1.5 py-0.5 rounded">
                    {childCount}
                  </span>
                )}
              </div>
              {level === 0 && cls.parent_classes && cls.parent_classes.length > 0 && (
                <div className="text-xs text-gray-500 mt-0.5">
                  ↑ {cls.parent_classes.map((uri, idx) => {
                    const parent = ontology.classes?.find(c => c.uri === uri)
                    const label = parent?.label || uri.split('/').pop() || uri
                    return (
                      <span key={uri}>
                        {idx > 0 && ', '}
                        <button
                          className="text-blue-600 hover:text-blue-800 hover:underline focus:outline-none focus:underline"
                          onClick={(e) => {
                            e.stopPropagation()
                            handleSelect({ type: 'class', uri })
                          }}
                        >
                          {label}
                        </button>
                      </span>
                    )
                  })}
                </div>
              )}
            </div>
          </div>
        </td>
        <td className="px-3 py-2">
          <div className="text-sm space-y-1">
            {cls.definition && (
              <div className="text-gray-900 italic" title="Formal definition">
                {cls.definition}
              </div>
            )}
            {cls.description && (
              <div className="text-gray-700" title="Additional context">
                {cls.description}
              </div>
            )}
            {!cls.definition && !cls.description && (
              <span className="text-gray-400 italic">No definition or description</span>
            )}
          </div>
        </td>
      </tr>
    )
  }

  const renderAttributeRow = (attr: OntologyAttributeModel) => {
    const isSelected = selectedElement?.type === 'attribute' && selectedElement.uri === attr.uri
    const domainClass = ontology.classes?.find(c => c.uri === attr.domain_class)
    const rowKey = `attribute-${attr.uri}`
    const changeType = getChangeType('attribute', attr.uri)
    const changeClasses = getChangeClasses(changeType)
    const changeBadge = getChangeBadge(changeType)
    
    return (
      <tr 
        key={attr.uri}
        ref={(el) => { selectedRowRefs.current[rowKey] = el }}
        className={`cursor-pointer transition-colors ${
          isSelected 
            ? 'bg-green-100 hover:bg-green-200' 
            : changeClasses || 'hover:bg-gray-50'
        }`}
        onClick={() => handleSelect({ type: 'attribute', uri: attr.uri })}
      >
        <td className="px-3 py-2">
          <div className="font-medium text-sm text-gray-900 flex items-center gap-2">
            {attr.label}
            {changeBadge}
          </div>
          <div className="text-xs text-gray-500 mt-0.5">
            <span className="font-medium">Domain:</span>{' '}
            <button
              className="text-blue-600 hover:text-blue-800 hover:underline focus:outline-none focus:underline"
              onClick={(e) => {
                e.stopPropagation()
                handleSelect({ type: 'class', uri: attr.domain_class })
              }}
            >
              {domainClass?.label || attr.domain_class}
            </button>
            <span className="ml-3 font-medium">Range:</span> {attr.range_type}
          </div>
        </td>
        <td className="px-3 py-2">
          <div className="text-sm space-y-1">
            {attr.definition && (
              <div className="text-gray-900 italic" title="Formal definition">
                {attr.definition}
              </div>
            )}
            {attr.description && (
              <div className="text-gray-700" title="Additional context">
                {attr.description}
              </div>
            )}
            {!attr.definition && !attr.description && (
              <span className="text-gray-400 italic">No definition or description</span>
            )}
          </div>
        </td>
      </tr>
    )
  }

  const renderRelationshipRow = (rel: OntologyRelationshipModel) => {
    const isSelected = selectedElement?.type === 'relationship' && selectedElement.uri === rel.uri
    const domainClass = ontology.classes?.find(c => c.uri === rel.domain_class)
    const rangeClass = ontology.classes?.find(c => c.uri === rel.range_class)
    const rowKey = `relationship-${rel.uri}`
    const changeType = getChangeType('relationship', rel.uri)
    const changeClasses = getChangeClasses(changeType)
    const changeBadge = getChangeBadge(changeType)
    
    return (
      <tr 
        key={rel.uri}
        ref={(el) => { selectedRowRefs.current[rowKey] = el }}
        className={`cursor-pointer transition-colors ${
          isSelected 
            ? 'bg-purple-100 hover:bg-purple-200' 
            : changeClasses || 'hover:bg-gray-50'
        }`}
        onClick={() => handleSelect({ type: 'relationship', uri: rel.uri })}
      >
        <td className="px-3 py-2">
          <div className="font-medium text-sm text-gray-900 flex items-center gap-2">
            {rel.label}
            {changeBadge}
          </div>
          <div className="text-xs text-gray-500 mt-0.5">
            <button
              className="text-blue-600 hover:text-blue-800 hover:underline focus:outline-none focus:underline"
              onClick={(e) => {
                e.stopPropagation()
                handleSelect({ type: 'class', uri: rel.domain_class })
              }}
            >
              {domainClass?.label || rel.domain_class}
            </button>
            {' → '}
            <button
              className="text-blue-600 hover:text-blue-800 hover:underline focus:outline-none focus:underline"
              onClick={(e) => {
                e.stopPropagation()
                handleSelect({ type: 'class', uri: rel.range_class })
              }}
            >
              {rangeClass?.label || rel.range_class}
            </button>
          </div>
        </td>
        <td className="px-3 py-2">
          <div className="text-sm space-y-1">
            {rel.definition && (
              <div className="text-gray-900 italic" title="Formal definition">
                {rel.definition}
              </div>
            )}
            {rel.description && (
              <div className="text-gray-700" title="Additional context">
                {rel.description}
              </div>
            )}
            {!rel.definition && !rel.description && (
              <span className="text-gray-400 italic">No definition or description</span>
            )}
          </div>
        </td>
      </tr>
    )
  }

  const renderPanel = (
    title: string,
    color: string,
    items: any[],
    renderRow: (item: any) => JSX.Element,
    emptyMessage: string
  ) => (
    <div className="bg-white border rounded-card overflow-hidden">
      <div className={`px-3 py-2 ${color} border-b`}>
        <h3 className="font-semibold text-sm flex items-center justify-between">
          <span>{title}</span>
          <span className="text-xs font-normal opacity-75">
            {items.length} {items.length === 1 ? 'item' : 'items'}
          </span>
        </h3>
      </div>
      <div className="overflow-auto" style={{ maxHeight: '400px' }}>
        {items.length > 0 ? (
          <table className="w-full">
            <thead className="bg-gray-50 border-b sticky top-0">
              <tr>
                <th className="px-3 py-2 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                  Name
                </th>
                <th className="px-3 py-2 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                  Description
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {items.map(renderRow)}
            </tbody>
          </table>
        ) : (
          <div className="p-8 text-center text-gray-500 text-sm">
            {emptyMessage}
          </div>
        )}
      </div>
    </div>
  )

  return (
    <div className="space-y-4">
      {/* Selection indicator */}
      {selectedElement && (
        <div className="bg-blue-50 border border-blue-200 rounded-card px-4 py-2 flex items-center justify-between">
          <div className="text-sm">
            <span className="font-medium">Selected:</span>{' '}
            <span className="capitalize">{selectedElement.type}</span>{' '}
            <span className="font-semibold">
              {selectedElement.type === 'class' 
                ? ontology.classes?.find(c => c.uri === selectedElement.uri)?.label
                : selectedElement.type === 'attribute'
                ? ontology.attributes?.find(a => a.uri === selectedElement.uri)?.label
                : ontology.relationships?.find(r => r.uri === selectedElement.uri)?.label
              }
            </span>
          </div>
          <button 
            className="text-xs px-2 py-1 bg-white border rounded hover:bg-gray-50"
            onClick={() => handleSelect(null)}
          >
            Clear Selection
          </button>
        </div>
      )}

      <div className="grid grid-cols-3 gap-4">
        {/* Classes Panel with Tree Controls */}
        <div className="bg-white border rounded-card overflow-hidden">
          <div className="px-3 py-2 bg-blue-50 text-blue-900 border-b">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-semibold text-sm">🧩 Classes</h3>
              <span className="text-xs font-normal opacity-75">
                {filteredClasses.length} {filteredClasses.length === 1 ? 'item' : 'items'}
              </span>
            </div>
            <div className="flex gap-2">
              <button
                onClick={expandAll}
                className="text-xs px-2 py-1 bg-white border border-blue-300 rounded hover:bg-blue-100 transition-colors"
              >
                Expand All
              </button>
              <button
                onClick={collapseAll}
                className="text-xs px-2 py-1 bg-white border border-blue-300 rounded hover:bg-blue-100 transition-colors"
              >
                Collapse All
              </button>
            </div>
          </div>
          <div className="overflow-auto" style={{ maxHeight: '400px' }}>
            {filteredClasses.length > 0 ? (
              <table className="w-full">
                <thead className="bg-gray-50 border-b sticky top-0">
                  <tr>
                    <th className="px-3 py-2 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                      Name
                    </th>
                    <th className="px-3 py-2 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                      Description
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {filteredClasses.map(renderClassRow)}
                </tbody>
              </table>
            ) : (
              <div className="p-8 text-center text-gray-500 text-sm">
                {selectedElement?.type === 'attribute'
                  ? 'Showing owning class for selected attribute'
                  : selectedElement?.type === 'relationship'
                    ? 'Showing classes connected by selected relationship'
                    : searchQuery 
                      ? 'No classes match your search'
                      : 'No classes in this ontology'}
              </div>
            )}
          </div>
        </div>

        {/* Attributes Panel */}
        {renderPanel(
          '🔤 Attributes',
          'bg-green-50 text-green-900',
          filteredAttributes,
          renderAttributeRow,
          selectedElement?.type === 'relationship'
            ? 'No attributes for selected relationship'
            : searchQuery 
              ? 'No attributes match your search'
              : selectedElement?.type === 'class'
                ? 'No attributes for selected class'
                : 'No attributes in this ontology'
        )}

        {/* Relationships Panel */}
        {renderPanel(
          '🔗 Relationships',
          'bg-purple-50 text-purple-900',
          filteredRelationships,
          renderRelationshipRow,
          selectedElement?.type === 'attribute'
            ? 'No relationships for selected attribute'
            : searchQuery
              ? 'No relationships match your search'
              : selectedElement?.type === 'class'
                ? 'No relationships for selected class'
                : 'No relationships in this ontology'
        )}
      </div>
    </div>
  )
}
