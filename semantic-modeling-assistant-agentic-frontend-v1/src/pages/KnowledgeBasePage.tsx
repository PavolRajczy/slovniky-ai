import { useProjectStore } from '@/store/projectStore'
import { useSelectedElementStore } from '@/store/selectedElementStore'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { useState } from 'react'
import { useCoverageCounts, useOntologyFragments } from '@/components/ElementCoveragePanel'

// Type for knowledge document elements (recursive)
type KnowledgeDocumentElement = {
  id: string
  title: string
  content: string
  content_summary: string
  element_type: string
  child_elements?: KnowledgeDocumentElement[]
}

type KnowledgeDocument = {
  id: string
  title: string
  content: string
  content_summary: string
  element_type: string
  child_elements?: KnowledgeDocumentElement[]
}

export function KnowledgeBasePage() {
  const { projectId } = useProjectStore()
  const { setSelectedElement, selectedOntologyUri } = useSelectedElementStore()
  const qc = useQueryClient()
  const [selectedDocumentId, setSelectedDocumentId] = useState<string | null>(null)
  
  // Store expanded/collapsed state for all elements (persists across re-renders)
  const [expandedElements, setExpandedElements] = useState<Set<string>>(new Set())
  const [visibleContent, setVisibleContent] = useState<Set<string>>(new Set())
  
  // Get fragment IDs to highlight based on selected ontology element
  const highlightedFragments = useOntologyFragments(projectId, selectedOntologyUri)
  
  const projectQ = useQuery({
    enabled: !!projectId,
    queryKey: ['project', projectId],
    queryFn: () => api.getProject(projectId!),
  })
  const kbQ = useQuery({
    enabled: !!projectId,
    queryKey: ['kb', projectId],
    queryFn: () => api.getProjectKnowledgeBase(projectId!),
  })
  const legalQ = useQuery({ queryKey: ['legalDocs'], queryFn: () => api.listLegalDocuments() })
  const expertQ = useQuery({ queryKey: ['expertDocs'], queryFn: () => api.listExpertDocuments() })

  const setKeyDoc = useMutation({
    mutationFn: (docId: string) => api.setKeyDocument(projectId!, docId),
    onSuccess: async () => {
      // Invalidate both project and knowledge base queries to refresh the UI
      await qc.invalidateQueries({ queryKey: ['project', projectId] })
      await qc.invalidateQueries({ queryKey: ['kb', projectId] })
    },
    onError: (error) => {
      console.error('Failed to set key document:', error)
    },
  })
  const addLegal = useMutation({
    mutationFn: (id: string) => api.addLegalDocuments(projectId!, [id]),
    onSuccess: async () => qc.invalidateQueries({ queryKey: ['kb', projectId] }),
  })
  const addExpert = useMutation({
    mutationFn: (id: string) => api.addExpertDocuments(projectId!, [id]),
    onSuccess: async () => qc.invalidateQueries({ queryKey: ['kb', projectId] }),
  })
  const removeLegal = useMutation({
    mutationFn: (id: string) => api.removeLegalDocument(projectId!, id),
    onSuccess: async () => qc.invalidateQueries({ queryKey: ['kb', projectId] }),
  })
  const removeExpert = useMutation({
    mutationFn: (id: string) => api.removeExpertDocument(projectId!, id),
    onSuccess: async () => qc.invalidateQueries({ queryKey: ['kb', projectId] }),
  })

  // Query for full document content (only when a document is selected)
  const documentQ = useQuery({
    enabled: !!selectedDocumentId,
    queryKey: ['knowledgeDocument', selectedDocumentId],
    queryFn: () => api.getKnowledgeDocument(selectedDocumentId!),
  })
  
  if (!projectId) return <div>Select a project to manage its knowledge base.</div>
  
  const keyDocumentId = projectQ.data?.key_knowledge_document_id
  
  // Debug: log project data to see what's being returned
  if (projectQ.data) {
    console.log('Project data:', projectQ.data)
    console.log('Key document ID:', keyDocumentId)
  }
  
  // Filter out documents that are already in the project
  const projectLegalIds = new Set(kbQ.data?.legal_documents?.map((d: any) => d.id) || [])
  const projectExpertIds = new Set(kbQ.data?.expert_documents?.map((d: any) => d.id) || [])
  
  const availableLegalDocs = legalQ.data?.filter((d: any) => !projectLegalIds.has(d.id)) || []
  const availableExpertDocs = expertQ.data?.filter((d: any) => !projectExpertIds.has(d.id)) || []

  // Helper function to parse XML content and extract fragments
  const parseXMLContent = (xmlString: string) => {
    const parser = new DOMParser()
    const xmlDoc = parser.parseFromString(xmlString, 'text/xml')
    
    // Check for parsing errors
    const parserError = xmlDoc.querySelector('parsererror')
    if (parserError) {
      return { error: true, text: xmlString }
    }
    
    return { error: false, doc: xmlDoc }
  }

  // Component to render XML fragments hierarchically
  const XMLFragment = ({ node, level = 0 }: { node: Element; level?: number }) => {
    const fragmentId = node.getAttribute('id')
    const isHighlighted = fragmentId && highlightedFragments.has(fragmentId)
    const children = Array.from(node.children).filter(child => child.tagName === 'f')
    const textContent = Array.from(node.childNodes)
      .filter(child => child.nodeType === Node.TEXT_NODE || (child.nodeType === Node.ELEMENT_NODE && (child as Element).tagName !== 'f'))
      .map(child => child.textContent)
      .join('')
      .trim()

    return (
      <div 
        id={fragmentId || undefined}
        data-fragment-id={fragmentId || undefined}
        className={`mb-2 transition-colors ${isHighlighted ? 'bg-yellow-200 border-l-4 border-yellow-500 pl-2 py-1 rounded' : ''}`}
        style={{ marginLeft: `${level * 1}rem` }}
      >
        {textContent && (
          <div className={`text-sm leading-relaxed ${isHighlighted ? 'text-gray-900 font-medium' : 'text-gray-700'}`}>
            {textContent}
          </div>
        )}
        {children.length > 0 && (
          <div className="mt-1">
            {children.map((child, idx) => (
              <XMLFragment key={child.getAttribute('id') || idx} node={child} level={level + 1} />
            ))}
          </div>
        )}
      </div>
    )
  }

  // Component to render content (either plain text or XML)
  const ContentDisplay = ({ content }: { content: string }) => {
    const parsed = parseXMLContent(content)
    
    if (parsed.error || !parsed.doc) {
      // Fallback to plain text if XML parsing fails
      return (
        <div className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
          {content}
        </div>
      )
    }
    
    // Render XML fragments hierarchically
    const rootFragments = Array.from(parsed.doc.documentElement.children).filter(
      child => child.tagName === 'f'
    )
    
    if (rootFragments.length === 0) {
      // No fragments, just render text content
      return (
        <div className="text-sm text-gray-700 leading-relaxed">
          {parsed.doc.documentElement.textContent?.trim()}
        </div>
      )
    }
    
    return (
      <div>
        {rootFragments.map((fragment, idx) => (
          <XMLFragment key={fragment.getAttribute('id') || idx} node={fragment as Element} level={0} />
        ))}
      </div>
    )
  }

  // Recursive component to render document element hierarchy with fold/unfold
  const DocumentElement = ({ element, level = 0 }: { element: KnowledgeDocumentElement; level?: number }) => {
    const isExpanded = expandedElements.has(element.id)
    const showContent = visibleContent.has(element.id)
    const indent = level * 1.5 // rem units
    const hasChildren = element.child_elements && element.child_elements.length > 0
    const hasContent = !!element.content
    
    // Get coverage counts for this element
    const counts = useCoverageCounts(projectId, element)
    
    // Check if this element is selected
    const { documentId: selectedDocId, elementId: selectedElemId } = useSelectedElementStore()
    const isSelected = selectedDocId === selectedDocumentId && selectedElemId === element.id
    
    const toggleExpanded = () => {
      const newSet = new Set(expandedElements)
      if (isExpanded) {
        newSet.delete(element.id)
      } else {
        newSet.add(element.id)
      }
      setExpandedElements(newSet)
    }
    
    const toggleContent = () => {
      const newSet = new Set(visibleContent)
      if (showContent) {
        newSet.delete(element.id)
      } else {
        newSet.add(element.id)
      }
      setVisibleContent(newSet)
    }
    
    const handleElementClick = (e: React.MouseEvent) => {
      e.stopPropagation() // Prevent parent elements from also handling the click
      if (selectedDocumentId) {
        setSelectedElement(selectedDocumentId, element.id)
      }
    }
    
    return (
      <div style={{ marginLeft: `${indent}rem` }} className="mb-3">
        <div 
          className={`p-2 rounded border cursor-pointer transition-colors ${
            isSelected 
              ? 'border-blue-500 bg-blue-100 shadow-sm' 
              : 'border-transparent hover:border-blue-200 hover:bg-blue-50'
          }`}
          onClick={handleElementClick}
          title="Click to see ontology references"
        >
          <div className="flex items-start gap-2">
            {hasChildren && (
              <button
                onClick={(e) => { e.stopPropagation(); toggleExpanded(); }}
                className="flex-shrink-0 w-5 h-5 flex items-center justify-center hover:bg-gray-100 rounded text-gray-600"
                title={isExpanded ? 'Collapse' : 'Expand'}
              >
                {isExpanded ? '▼' : '▶'}
              </button>
            )}
            {!hasChildren && <div className="w-5 flex-shrink-0" />}
            <div className="flex-1 min-w-0">
              <div className="flex items-baseline gap-2 flex-wrap mb-1">
                <div className="text-sm font-semibold text-gray-800">
                  {element.title}
                </div>
                {counts.total > 0 && (
                  <div className="flex gap-2 text-xs">
                    {counts.classes > 0 && (
                      <span className="px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded" title="Classes">
                        📝 {counts.classes}
                      </span>
                    )}
                    {counts.attributes > 0 && (
                      <span className="px-1.5 py-0.5 bg-green-100 text-green-700 rounded" title="Attributes">
                        📋 {counts.attributes}
                      </span>
                    )}
                    {counts.relationships > 0 && (
                      <span className="px-1.5 py-0.5 bg-purple-100 text-purple-700 rounded" title="Relationships">
                        🔗 {counts.relationships}
                      </span>
                    )}
                  </div>
                )}
              </div>
              {element.content_summary && (
                <div className="text-sm text-gray-600 mb-2 leading-relaxed">
                  {element.content_summary}
                </div>
              )}
              {hasContent && (
                <div className="mb-2">
                  <button
                    onClick={(e) => { e.stopPropagation(); toggleContent(); }}
                    className="text-xs px-2 py-1 border rounded hover:bg-gray-50 text-blue-600"
                  >
                    {showContent ? 'Hide Content' : 'Show Content'}
                  </button>
                  {showContent && (
                    <div className="mt-2 border-l-2 border-blue-200 pl-3">
                      <ContentDisplay content={element.content} />
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
        {hasChildren && isExpanded && (
          <div 
            className="border-l-2 border-gray-200 pl-3 mt-2 ml-2.5"
            onClick={(e) => e.stopPropagation()}
          >
            {element.child_elements!.map((child) => (
              <DocumentElement key={child.id} element={child} level={level + 1} />
            ))}
          </div>
        )}
      </div>
    )
  }
  
  return (
    <div className="flex h-full gap-4">
      {/* Left Sidebar - Document List */}
      <div className="w-64 flex-shrink-0 space-y-4 overflow-y-auto">
        {/* Key Document Tip */}
        {!keyDocumentId && (kbQ.data?.legal_documents?.length > 0 || kbQ.data?.expert_documents?.length > 0) && (
          <div className="bg-amber-50 border border-amber-200 rounded-card p-2 text-xs">
            <strong>💡 Tip:</strong> Set a key document for domain area generation.
          </div>
        )}

        {/* Project Legal Documents */}
        <div className="bg-white border rounded-card p-3">
          <div className="font-semibold text-sm mb-2">Legal Documents</div>
          <ul className="space-y-1">
            {kbQ.data?.legal_documents?.map((d: any) => (
              <li 
                key={d.id} 
                className={`text-sm p-2 rounded cursor-pointer hover:bg-gray-100 ${
                  selectedDocumentId === d.id ? 'bg-blue-50 border border-blue-200' : ''
                }`}
                onClick={() => setSelectedDocumentId(d.id)}
              >
                <div className="flex items-start gap-1">
                  {keyDocumentId === d.id && (
                    <span className="text-amber-500 text-xs flex-shrink-0 mt-0.5" title="Key Document">🔑</span>
                  )}
                  <span className="flex-1 break-words">{d.title || '(Untitled)'}</span>
                </div>
                <div className="flex gap-1 mt-1">
                  {keyDocumentId !== d.id && (
                    <button 
                      className="text-xs px-1 py-0.5 border rounded hover:bg-white" 
                      onClick={(e) => { e.stopPropagation(); setKeyDoc.mutate(d.id); }}
                      disabled={setKeyDoc.isPending}
                    >
                      Set Key
                    </button>
                  )}
                  <button 
                    className="text-xs px-1 py-0.5 border rounded hover:bg-white text-red-600" 
                    onClick={(e) => { e.stopPropagation(); removeLegal.mutate(d.id); }}
                  >
                    Remove
                  </button>
                </div>
              </li>
            ))}
          </ul>
          
          <div className="h-px bg-gray-200 my-2" />
          <div className="text-xs font-semibold mb-1 text-gray-600">Available Legal</div>
          <ul className="space-y-1 max-h-32 overflow-auto">
            {availableLegalDocs.map((d: any) => (
              <li key={d.id} className="text-xs flex items-start justify-between gap-1">
                <span className="break-words flex-1">{d.title || '(Untitled)'}</span>
                <button 
                  className="text-xs px-1 py-0.5 border rounded flex-shrink-0" 
                  onClick={() => addLegal.mutate(d.id)}
                >
                  Add
                </button>
              </li>
            ))}
          </ul>
        </div>

        {/* Project Expert Documents */}
        <div className="bg-white border rounded-card p-3">
          <div className="font-semibold text-sm mb-2">Expert Documents</div>
          <ul className="space-y-1">
            {kbQ.data?.expert_documents?.map((d: any) => (
              <li 
                key={d.id} 
                className={`text-sm p-2 rounded cursor-pointer hover:bg-gray-100 ${
                  selectedDocumentId === d.id ? 'bg-blue-50 border border-blue-200' : ''
                }`}
                onClick={() => setSelectedDocumentId(d.id)}
              >
                <div className="flex items-start gap-1">
                  {keyDocumentId === d.id && (
                    <span className="text-amber-500 text-xs flex-shrink-0 mt-0.5" title="Key Document">🔑</span>
                  )}
                  <span className="flex-1 break-words">{d.title || '(Untitled)'}</span>
                </div>
                <div className="flex gap-1 mt-1">
                  {keyDocumentId !== d.id && (
                    <button 
                      className="text-xs px-1 py-0.5 border rounded hover:bg-white" 
                      onClick={(e) => { e.stopPropagation(); setKeyDoc.mutate(d.id); }}
                      disabled={setKeyDoc.isPending}
                    >
                      Set Key
                    </button>
                  )}
                  <button 
                    className="text-xs px-1 py-0.5 border rounded hover:bg-white text-red-600" 
                    onClick={(e) => { e.stopPropagation(); removeExpert.mutate(d.id); }}
                  >
                    Remove
                  </button>
                </div>
              </li>
            ))}
          </ul>
          
          <div className="h-px bg-gray-200 my-2" />
          <div className="text-xs font-semibold mb-1 text-gray-600">Available Expert</div>
          <ul className="space-y-1 max-h-32 overflow-auto">
            {availableExpertDocs.map((d: any) => (
              <li key={d.id} className="text-xs flex items-start justify-between gap-1">
                <span className="break-words flex-1">{d.title || '(Untitled)'}</span>
                <button 
                  className="text-xs px-1 py-0.5 border rounded flex-shrink-0" 
                  onClick={() => addExpert.mutate(d.id)}
                >
                  Add
                </button>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Right Panel - Document Detail */}
      <div className="flex-1 bg-white border rounded-card overflow-hidden flex flex-col">
        {!selectedDocumentId && (
          <div className="flex items-center justify-center h-full text-gray-400">
            <div className="text-center">
              <div className="text-4xl mb-2">📄</div>
              <div>Select a document to view its content</div>
            </div>
          </div>
        )}
        
        {selectedDocumentId && documentQ.isLoading && (
          <div className="flex items-center justify-center h-full">
            <div className="text-gray-500">Loading document...</div>
          </div>
        )}
        
        {selectedDocumentId && documentQ.error && (
          <div className="flex items-center justify-center h-full">
            <div className="text-red-500">
              Failed to load document: {(documentQ.error as Error).message}
            </div>
          </div>
        )}
        
        {selectedDocumentId && documentQ.data && (
          <div className="flex flex-col h-full">
            {/* Document Header */}
            <div className="border-b p-4 bg-gray-50">
              <h2 className="text-xl font-semibold text-gray-800">
                {documentQ.data.title}
              </h2>
              {documentQ.data.content_summary && (
                <p className="text-sm text-gray-600 mt-2 leading-relaxed">
                  {documentQ.data.content_summary}
                </p>
              )}
            </div>
            
            {/* Document Content */}
            <div className="flex-1 overflow-y-auto p-4">
              {documentQ.data.child_elements && documentQ.data.child_elements.length > 0 ? (
                documentQ.data.child_elements.map((element: KnowledgeDocumentElement) => (
                  <DocumentElement key={element.id} element={element} level={0} />
                ))
              ) : (
                <div className="text-gray-500 text-sm">
                  No hierarchical content available for this document.
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
