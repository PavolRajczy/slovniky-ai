import { useProjectStore } from '@/store/projectStore'
import { useSelectedElementStore } from '@/store/selectedElementStore'
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { useMemo } from 'react'

type OntologyElementReference = {
  uri: string
  label: string
  element_type: 'class' | 'attribute' | 'relationship'
}

type ElementCoverage = {
  defined_ontology_elements: OntologyElementReference[]
  specified_ontology_elements: OntologyElementReference[]
  referenced_ontology_elements: OntologyElementReference[]
  has_coverage: boolean
}

export type CoverageCounts = {
  classes: number
  attributes: number
  relationships: number
  total: number
}

// Hook to get aggregated coverage counts for any element (including children/descendants)
export function useCoverageCounts(projectId: string | null, elementIdOrContent: string | { id: string; content?: string; child_elements?: any[] }) {
  const ontologyQ = useQuery({
    enabled: !!projectId,
    queryKey: ['projectOntology', projectId],
    queryFn: () => api.getProjectOntology(projectId!),
  })

  const elementCoverageMap = useMemo(() => {
    if (!ontologyQ.data || typeof ontologyQ.data === 'string') return new Map<string, ElementCoverage>()

    const ontology = ontologyQ.data
    const map = new Map<string, ElementCoverage>()
    
    const addToCoverage = (refId: string, element: OntologyElementReference, type: 'defined' | 'specified' | 'referenced') => {
      if (!map.has(refId)) {
        map.set(refId, {
          defined_ontology_elements: [],
          specified_ontology_elements: [],
          referenced_ontology_elements: [],
          has_coverage: false,
        })
      }
      const coverage = map.get(refId)!
      if (type === 'defined') {
        coverage.defined_ontology_elements.push(element)
      } else if (type === 'specified') {
        coverage.specified_ontology_elements.push(element)
      } else {
        coverage.referenced_ontology_elements.push(element)
      }
      coverage.has_coverage = true
    }

    // Process all ontology elements
    for (const cls of ontology.classes || []) {
      const ref: OntologyElementReference = { uri: cls.uri, label: cls.label, element_type: 'class' }
      for (const refId of cls.definition_references || []) addToCoverage(refId, ref, 'defined')
      for (const refId of cls.specification_references || []) addToCoverage(refId, ref, 'specified')
      for (const refId of cls.references || []) addToCoverage(refId, ref, 'referenced')
    }
    for (const attr of ontology.attributes || []) {
      const ref: OntologyElementReference = { uri: attr.uri, label: attr.label, element_type: 'attribute' }
      for (const refId of attr.definition_references || []) addToCoverage(refId, ref, 'defined')
      for (const refId of attr.specification_references || []) addToCoverage(refId, ref, 'specified')
      for (const refId of attr.references || []) addToCoverage(refId, ref, 'referenced')
    }
    for (const rel of ontology.relationships || []) {
      const ref: OntologyElementReference = { uri: rel.uri, label: rel.label, element_type: 'relationship' }
      for (const refId of rel.definition_references || []) addToCoverage(refId, ref, 'defined')
      for (const refId of rel.specification_references || []) addToCoverage(refId, ref, 'specified')
      for (const refId of rel.references || []) addToCoverage(refId, ref, 'referenced')
    }

    return map
  }, [ontologyQ.data])

  return useMemo(() => {
    if (typeof elementIdOrContent === 'string') return { classes: 0, attributes: 0, relationships: 0, total: 0 }
    
    const element = elementIdOrContent
    const seenUris = new Set<string>()
    let classCount = 0, attrCount = 0, relCount = 0
    
    const countElement = (coverage: ElementCoverage) => {
      const allElements = [
        ...coverage.defined_ontology_elements,
        ...coverage.specified_ontology_elements,
        ...coverage.referenced_ontology_elements
      ]
      for (const el of allElements) {
        if (!seenUris.has(el.uri)) {
          seenUris.add(el.uri)
          if (el.element_type === 'class') classCount++
          else if (el.element_type === 'attribute') attrCount++
          else if (el.element_type === 'relationship') relCount++
        }
      }
    }
    
    // Direct match
    const directCoverage = elementCoverageMap.get(element.id)
    if (directCoverage) countElement(directCoverage)
    
    // Fragments from content
    if (element.content && typeof element.content === 'string') {
      const parser = new DOMParser()
      const xmlDoc = parser.parseFromString(element.content, 'text/xml')
      const fragments = xmlDoc.querySelectorAll('f[id]')
      fragments.forEach(frag => {
        const id = frag.getAttribute('id')
        if (id) {
          const coverage = elementCoverageMap.get(id)
          if (coverage) countElement(coverage)
        }
      })
    }
    
    // Children/descendants
    if (element.child_elements && element.child_elements.length > 0) {
      const prefix = element.id + '/'
      for (const [key, coverage] of elementCoverageMap.entries()) {
        if (key.startsWith(prefix)) {
          countElement(coverage)
        }
      }
    }
    
    return {
      classes: classCount,
      attributes: attrCount,
      relationships: relCount,
      total: classCount + attrCount + relCount
    }
  }, [elementIdOrContent, elementCoverageMap])
}

// Hook to get fragment IDs that reference a specific ontology element
export function useOntologyFragments(projectId: string | null, ontologyUri: string | null) {
  const ontologyQ = useQuery({
    enabled: !!projectId,
    queryKey: ['projectOntology', projectId],
    queryFn: () => api.getProjectOntology(projectId!),
  })

  return useMemo(() => {
    if (!ontologyUri || !ontologyQ.data || typeof ontologyQ.data === 'string') {
      return new Set<string>()
    }

    const ontology = ontologyQ.data
    const fragmentIds = new Set<string>()

    // Find the ontology element by URI and collect all its reference IDs
    for (const cls of ontology.classes || []) {
      if (cls.uri === ontologyUri) {
        for (const refId of cls.definition_references || []) fragmentIds.add(refId)
        for (const refId of cls.specification_references || []) fragmentIds.add(refId)
        for (const refId of cls.references || []) fragmentIds.add(refId)
        break
      }
    }
    for (const attr of ontology.attributes || []) {
      if (attr.uri === ontologyUri) {
        for (const refId of attr.definition_references || []) fragmentIds.add(refId)
        for (const refId of attr.specification_references || []) fragmentIds.add(refId)
        for (const refId of attr.references || []) fragmentIds.add(refId)
        break
      }
    }
    for (const rel of ontology.relationships || []) {
      if (rel.uri === ontologyUri) {
        for (const refId of rel.definition_references || []) fragmentIds.add(refId)
        for (const refId of rel.specification_references || []) fragmentIds.add(refId)
        for (const refId of rel.references || []) fragmentIds.add(refId)
        break
      }
    }

    return fragmentIds
  }, [ontologyUri, ontologyQ.data])
}

export function ElementCoveragePanel() {
  const { projectId } = useProjectStore()
  const { documentId, elementId, selectedOntologyUri, setSelectedOntologyElement } = useSelectedElementStore()

  // Fetch the document to access element structure
  const documentQ = useQuery({
    enabled: !!documentId,
    queryKey: ['document', documentId],
    queryFn: () => api.getKnowledgeDocument(documentId!),
  })

  // Fetch the ontology for the current project
  const ontologyQ = useQuery({
    enabled: !!projectId,
    queryKey: ['projectOntology', projectId],
    queryFn: () => api.getProjectOntology(projectId!),
  })

  // Build reverse index: documentElementId → coverage info
  const elementCoverageMap = useMemo(() => {
    if (!ontologyQ.data || typeof ontologyQ.data === 'string') return new Map<string, ElementCoverage>()

    const ontology = ontologyQ.data
    const map = new Map<string, ElementCoverage>()
    
    // Helper to add element to coverage map
    const addToCoverage = (refId: string, element: OntologyElementReference, type: 'defined' | 'specified' | 'referenced') => {
      if (!map.has(refId)) {
        map.set(refId, {
          defined_ontology_elements: [],
          specified_ontology_elements: [],
          referenced_ontology_elements: [],
          has_coverage: false,
        })
      }
      const coverage = map.get(refId)!
      if (type === 'defined') {
        coverage.defined_ontology_elements.push(element)
      } else if (type === 'specified') {
        coverage.specified_ontology_elements.push(element)
      } else {
        coverage.referenced_ontology_elements.push(element)
      }
      coverage.has_coverage = true
    }

    // Process classes
    for (const cls of ontology.classes || []) {
      const ref: OntologyElementReference = {
        uri: cls.uri,
        label: cls.label,
        element_type: 'class'
      }
      for (const refId of cls.definition_references || []) {
        addToCoverage(refId, ref, 'defined')
      }
      for (const refId of cls.specification_references || []) {
        addToCoverage(refId, ref, 'specified')
      }
      for (const refId of cls.references || []) {
        addToCoverage(refId, ref, 'referenced')
      }
    }

    // Process attributes
    for (const attr of ontology.attributes || []) {
      const ref: OntologyElementReference = {
        uri: attr.uri,
        label: attr.label,
        element_type: 'attribute'
      }
      for (const refId of attr.definition_references || []) {
        addToCoverage(refId, ref, 'defined')
      }
      for (const refId of attr.specification_references || []) {
        addToCoverage(refId, ref, 'specified')
      }
      for (const refId of attr.references || []) {
        addToCoverage(refId, ref, 'referenced')
      }
    }

    // Process relationships
    for (const rel of ontology.relationships || []) {
      const ref: OntologyElementReference = {
        uri: rel.uri,
        label: rel.label,
        element_type: 'relationship'
      }
      for (const refId of rel.definition_references || []) {
        addToCoverage(refId, ref, 'defined')
      }
      for (const refId of rel.specification_references || []) {
        addToCoverage(refId, ref, 'specified')
      }
      for (const refId of rel.references || []) {
        addToCoverage(refId, ref, 'referenced')
      }
    }

    return map
  }, [ontologyQ.data])

  // Helper to extract fragment IDs from XML content
  const extractFragmentIds = (xmlString: string): string[] => {
    const parser = new DOMParser()
    const xmlDoc = parser.parseFromString(xmlString, 'text/xml')
    
    const parserError = xmlDoc.querySelector('parsererror')
    if (parserError) return []
    
    const fragmentIds: string[] = []
    const fragments = xmlDoc.querySelectorAll('f[id]')
    fragments.forEach(frag => {
      const id = frag.getAttribute('id')
      if (id) fragmentIds.push(id)
    })
    
    return fragmentIds
  }

  // Helper to find element in document tree
  const findElement = (elements: any[], targetId: string): any => {
    for (const el of elements || []) {
      if (el.id === targetId) return el
      if (el.child_elements) {
        const found = findElement(el.child_elements, targetId)
        if (found) return found
      }
    }
    return null
  }

  const selectedElementCoverage = useMemo(() => {
    if (!elementId || !documentQ.data) return null
    
    // Find the selected element in the document tree
    const element = findElement([documentQ.data], elementId)
    if (!element) return null
    
    // Aggregate coverage from:
    // 1. Direct element ID match
    // 2. Fragment IDs within the element's content
    const aggregated: ElementCoverage = {
      defined_ontology_elements: [],
      specified_ontology_elements: [],
      referenced_ontology_elements: [],
      has_coverage: false
    }
    
    const seenUris = {
      defined: new Set<string>(),
      specified: new Set<string>(),
      referenced: new Set<string>()
    }
    
    const addCoverage = (coverage: ElementCoverage) => {
      for (const el of coverage.defined_ontology_elements) {
        if (!seenUris.defined.has(el.uri)) {
          seenUris.defined.add(el.uri)
          aggregated.defined_ontology_elements.push(el)
        }
      }
      for (const el of coverage.specified_ontology_elements) {
        if (!seenUris.specified.has(el.uri)) {
          seenUris.specified.add(el.uri)
          aggregated.specified_ontology_elements.push(el)
        }
      }
      for (const el of coverage.referenced_ontology_elements) {
        if (!seenUris.referenced.has(el.uri)) {
          seenUris.referenced.add(el.uri)
          aggregated.referenced_ontology_elements.push(el)
        }
      }
      aggregated.has_coverage = true
    }
    
    // Check direct element ID
    const directCoverage = elementCoverageMap.get(elementId)
    if (directCoverage) {
      addCoverage(directCoverage)
    }
    
    // Check fragments in content
    if (element.content && typeof element.content === 'string') {
      const fragmentIds = extractFragmentIds(element.content)
      for (const fragId of fragmentIds) {
        const coverage = elementCoverageMap.get(fragId)
        if (coverage) {
          addCoverage(coverage)
        }
      }
    }
    
    return aggregated.has_coverage ? aggregated : null
  }, [elementId, elementCoverageMap, documentQ.data])

  if (!elementId) {
    return (
      <div className="space-y-3">
        <h3 className="font-semibold text-sm">Ontology Coverage</h3>
        <div className="text-xs text-gray-500">
          Click on a document element to see which ontology elements are referenced.
        </div>
      </div>
    )
  }

  if (ontologyQ.isLoading) {
    return (
      <div className="space-y-3">
        <h3 className="font-semibold text-sm">Ontology Coverage</h3>
        <div className="text-xs text-gray-500">Loading coverage data...</div>
      </div>
    )
  }

  if (!selectedElementCoverage || !selectedElementCoverage.has_coverage) {
    return (
      <div className="space-y-3">
        <h3 className="font-semibold text-sm">Ontology Coverage</h3>
        <div className="text-xs text-gray-500">
          No ontology elements reference this document element.
        </div>
      </div>
    )
  }

  const ElementList = ({ 
    title, 
    elements, 
    icon 
  }: { 
    title: string
    elements?: OntologyElementReference[]
    icon: string 
  }) => {
    if (!elements || elements.length === 0) return null

    return (
      <div className="mb-3">
        <div className="text-xs font-semibold text-gray-700 mb-1 flex items-center gap-1">
          <span>{icon}</span>
          <span>{title}</span>
          <span className="text-gray-400">({elements.length})</span>
        </div>
        <ul className="space-y-1">
          {elements.map((el) => {
            const isSelected = selectedOntologyUri === el.uri
            return (
              <li 
                key={el.uri}
                className={`text-xs rounded p-1.5 cursor-pointer transition-colors ${
                  isSelected 
                    ? 'bg-blue-200 border border-blue-400' 
                    : 'bg-gray-50 hover:bg-gray-100'
                }`}
                title={el.uri}
                onClick={() => setSelectedOntologyElement(isSelected ? null : el.uri)}
              >
                <div className="flex items-center gap-1">
                  <span className="text-gray-400 text-[10px] uppercase">
                    {el.element_type}
                  </span>
                  <span className="font-medium text-gray-900">{el.label}</span>
                </div>
              </li>
            )
          })}
        </ul>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <h3 className="font-semibold text-sm">Ontology Coverage</h3>
      
      <ElementList 
        title="Definitions" 
        elements={selectedElementCoverage.defined_ontology_elements}
        icon="📝"
      />
      
      <ElementList 
        title="Specifications" 
        elements={selectedElementCoverage.specified_ontology_elements}
        icon="📋"
      />
      
      <ElementList 
        title="References" 
        elements={selectedElementCoverage.referenced_ontology_elements}
        icon="🔗"
      />
    </div>
  )
}
