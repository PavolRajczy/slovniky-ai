import { useProjectStore } from '@/store/projectStore'
import { useQuery } from '@tanstack/react-query'
import { api, OntologyModel } from '@/lib/api'
import { OntologyGrid, SelectedElement } from '@/components/OntologyGrid'
import { OntologyGraph } from '@/components/OntologyGraph'
import { OntologyForceGraph } from '@/components/OntologyForceGraph'
import { useOntologyChangesStore } from '@/store/ontologyChangesStore'
import { useState, useEffect } from 'react'

type ViewMode = 'grid' | 'graph' | 'force'

export function OntologyPage() {
  const { projectId } = useProjectStore()
  const [searchQuery, setSearchQuery] = useState('')
  const [viewMode, setViewMode] = useState<ViewMode>('grid')
  const [selectedElement, setSelectedElement] = useState<SelectedElement>(null)
  
  // Get changes tracking state
  const { 
    changes, 
    showChanges, 
    toggleShowChanges,
    filterMode,
    setFilterMode,
    updateFilteredElements,
    filteredElements
  } = useOntologyChangesStore()

  const ontologyQ = useQuery({
    enabled: !!projectId,
    queryKey: ['ontology', projectId],
    queryFn: () => api.getProjectOntology(projectId!, 'json'),
  })

  const ontology = ontologyQ.data as OntologyModel | undefined

  // Update filtered elements when ontology or filter mode changes
  useEffect(() => {
    if (ontology && changes) {
      updateFilteredElements(ontology)
    }
  }, [ontology, filterMode, changes, updateFilteredElements])

  const handleExport = async (format: 'json' | 'rdf') => {
    if (!projectId) return
    
    try {
      const data = await api.getProjectOntology(projectId, format)
      const blob = new Blob(
        [typeof data === 'string' ? data : JSON.stringify(data, null, 2)],
        { type: format === 'json' ? 'application/json' : 'text/turtle' }
      )
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `ontology-${projectId}.${format === 'json' ? 'json' : 'ttl'}`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Export failed:', error)
      alert('Failed to export ontology')
    }
  }

  if (!projectId) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        Select a project to see its ontology.
      </div>
    )
  }

  if (ontologyQ.isLoading) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        Loading ontology...
      </div>
    )
  }

  if (ontologyQ.isError) {
    return (
      <div className="flex items-center justify-center h-64 text-red-500">
        Failed to load ontology. Please try again.
      </div>
    )
  }

  if (!ontology) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        No ontology data available.
      </div>
    )
  }

  const totalElements = (ontology.classes?.length || 0) + 
                        (ontology.attributes?.length || 0) + 
                        (ontology.relationships?.length || 0)

  // Calculate change counts
  const changesCounts = changes ? {
    created: (changes.classes.size + changes.attributes.size + changes.relationships.size) - 
             Array.from([...changes.classes.values(), ...changes.attributes.values(), ...changes.relationships.values()])
               .filter(t => t === 'deleted').length,
    modified: Array.from([...changes.classes.values(), ...changes.attributes.values(), ...changes.relationships.values()])
               .filter(t => t === 'modified').length,
    deleted: Array.from([...changes.classes.values(), ...changes.attributes.values(), ...changes.relationships.values()])
               .filter(t => t === 'deleted').length,
  } : null

  return (
    <div className="flex flex-col h-full space-y-4">
      {/* Header with stats */}
      <div className="bg-white border rounded-card p-4 flex-shrink-0">
        <h2 className="text-lg font-semibold mb-2">{ontology.label}</h2>
        <p className="text-sm text-gray-600 mb-3">{ontology.description}</p>
        <div className="flex items-center gap-4 text-sm">
          <div className="flex items-center gap-2">
            <span className="inline-block w-3 h-3 rounded-full bg-blue-500"></span>
            <span className="text-gray-600">Classes: <strong>{ontology.classes?.length || 0}</strong></span>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-block w-3 h-3 rounded-full bg-green-500"></span>
            <span className="text-gray-600">Attributes: <strong>{ontology.attributes?.length || 0}</strong></span>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-block w-3 h-3 rounded-full bg-purple-500"></span>
            <span className="text-gray-600">Relationships: <strong>{ontology.relationships?.length || 0}</strong></span>
          </div>
          <div className="ml-auto text-gray-500">
            Total: <strong>{totalElements}</strong> elements
          </div>
        </div>
      </div>

      {/* Toolbar */}
      <div className="flex items-center gap-2 flex-shrink-0">
        <input 
          className="border rounded-card px-3 py-2 flex-1" 
          placeholder="Search by label, URI, or description..." 
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
        
        {/* Filter Mode Dropdown */}
        {changes && (
          <div className="flex items-center gap-2 border rounded-card px-3 py-2 bg-white">
            <label htmlFor="filter-mode" className="text-sm font-medium text-gray-700">
              Show:
            </label>
            <select
              id="filter-mode"
              value={filterMode}
              onChange={(e) => setFilterMode(e.target.value as 'all' | 'changed' | 'connected')}
              className="text-sm border-0 bg-transparent focus:outline-none focus:ring-0 cursor-pointer font-medium"
            >
              <option value="all">All Elements</option>
              <option value="changed">Changed Only</option>
              <option value="connected">Changed + Connected</option>
            </select>
          </div>
        )}
        
        {/* Changes Toggle */}
        {changes && (
          <div className="flex items-center gap-3 border rounded-card px-3 py-2 bg-white">
            <label
              htmlFor="show-changes-toggle"
              className="flex items-center gap-2 text-sm font-medium cursor-pointer"
            >
              <input
                id="show-changes-toggle"
                type="checkbox"
                checked={showChanges}
                onChange={toggleShowChanges}
                className="w-4 h-4 cursor-pointer"
              />
              <span className="text-gray-700">Show Changes</span>
            </label>
            {changesCounts && (
              <div className="flex items-center gap-2 text-xs border-l pl-3">
                <span className="px-2 py-1 rounded bg-green-100 text-green-700 font-medium">
                  +{changesCounts.created}
                </span>
                <span className="px-2 py-1 rounded bg-yellow-100 text-yellow-700 font-medium">
                  ~{changesCounts.modified}
                </span>
                <span className="px-2 py-1 rounded bg-red-100 text-red-700 font-medium">
                  -{changesCounts.deleted}
                </span>
              </div>
            )}
          </div>
        )}
        
        {/* View Mode Switcher */}
        <div className="flex items-center border rounded-card overflow-hidden">
          <button
            className={`px-4 py-2 text-sm font-medium transition-colors ${
              viewMode === 'grid'
                ? 'bg-blue-500 text-white'
                : 'bg-white text-gray-700 hover:bg-gray-50'
            }`}
            onClick={() => setViewMode('grid')}
          >
            📊 Grid View
          </button>
          <button
            className={`px-4 py-2 text-sm font-medium transition-colors border-l ${
              viewMode === 'graph'
                ? 'bg-blue-500 text-white'
                : 'bg-white text-gray-700 hover:bg-gray-50'
            }`}
            onClick={() => setViewMode('graph')}
          >
            🔗 Graph View
          </button>
          <button
            className={`px-4 py-2 text-sm font-medium transition-colors border-l ${
              viewMode === 'force'
                ? 'bg-blue-500 text-white'
                : 'bg-white text-gray-700 hover:bg-gray-50'
            }`}
            onClick={() => setViewMode('force')}
          >
            ⚡ Force View
          </button>
        </div>
        
        <button 
          className="px-3 py-2 border rounded-card hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          onClick={() => handleExport('json')}
          disabled={!ontology}
          title="Export as JSON"
        >
          📥 JSON
        </button>
        <button 
          className="px-3 py-2 border rounded-card hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          onClick={() => handleExport('rdf')}
          disabled={!ontology}
          title="Export as RDF/Turtle"
        >
          📥 RDF
        </button>
      </div>

      {/* View Content */}
      <div className="flex-1 min-h-0">
        {viewMode === 'grid' ? (
          <OntologyGrid 
            ontology={ontology}
            searchQuery={searchQuery}
            selectedElement={selectedElement}
            onSelectElement={setSelectedElement}
            changes={showChanges ? changes : null}
            filteredElements={filteredElements}
          />
        ) : viewMode === 'graph' ? (
          <div className="bg-white border rounded-card h-full">
            <OntologyGraph
              ontology={ontology}
              selectedElement={selectedElement}
              onSelectClass={(uri) => setSelectedElement(uri ? { type: 'class', uri } : null)}
              changes={showChanges ? changes : null}
              filteredElements={filteredElements}
            />
          </div>
        ) : (
          <div className="bg-white border rounded-card h-full">
            <OntologyForceGraph
              ontology={ontology}
              selectedElement={selectedElement}
              onSelectClass={(uri) => setSelectedElement(uri ? { type: 'class', uri } : null)}
              changes={showChanges ? changes : null}
              filteredElements={filteredElements}
            />
          </div>
        )}
      </div>
    </div>
  )
}
