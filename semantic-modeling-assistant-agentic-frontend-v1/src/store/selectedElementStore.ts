import { create } from 'zustand'

type SelectedElementState = {
  documentId: string | null
  elementId: string | null
  selectedOntologyUri: string | null // URI of the selected ontology element for highlighting
  setSelectedElement: (documentId: string | null, elementId: string | null) => void
  setSelectedOntologyElement: (uri: string | null) => void
  clearSelection: () => void
}

export const useSelectedElementStore = create<SelectedElementState>((set) => ({
  documentId: null,
  elementId: null,
  selectedOntologyUri: null,
  setSelectedElement: (documentId, elementId) => set({ documentId, elementId, selectedOntologyUri: null }),
  setSelectedOntologyElement: (uri) => set({ selectedOntologyUri: uri }),
  clearSelection: () => set({ documentId: null, elementId: null, selectedOntologyUri: null }),
}))
