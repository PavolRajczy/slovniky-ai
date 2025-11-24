import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { useProjectStore } from '@/store/projectStore'
import { useState } from 'react'
import { Modal } from './Modal'

export function ProjectSelector() {
  const { data, isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: () => api.listProjects(),
  })
  const ontologiesQuery = useQuery({
    queryKey: ['ontologies'],
    queryFn: () => api.listOntologies(),
  })
  const { projectId, setProjectId } = useProjectStore()
  const qc = useQueryClient()
  const [openCreate, setOpenCreate] = useState(false)
  const [openEdit, setOpenEdit] = useState(false)
  const [showOntologyForm, setShowOntologyForm] = useState(false)
  
  const createOntologyMut = useMutation({
    mutationFn: (req: { ontology_uri: string; ontology_label: string; ontology_description: string }) =>
      api.createOntology(req),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ['ontologies'] })
      setShowOntologyForm(false)
    },
  })
  
  const createMut = useMutation({
    mutationFn: (req: { 
      name: string
      ontology_uri: string
      knowledge_domain_name?: string | null
      knowledge_domain_description?: string | null
    }) =>
      api.createProject(req),
    onSuccess: async (p) => {
      await qc.invalidateQueries({ queryKey: ['projects'] })
      setProjectId(p.id)
      setOpenCreate(false)
      setShowOntologyForm(false)
    },
  })
  const updateMut = useMutation({
    mutationFn: (req: { name?: string; knowledge_domain_name?: string; knowledge_domain_description?: string }) =>
      api.updateProject(projectId!, req),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ['projects'] })
      setOpenEdit(false)
    },
  })

  return (
    <div className="flex items-center gap-2">
      <span className="font-semibold">Project</span>
      <select
        className="border rounded-card px-2 py-1"
        value={projectId ?? ''}
        onChange={(e) => setProjectId(e.target.value || null)}
      >
        <option value="">Select…</option>
        {data?.map((p) => (
          <option key={p.id} value={p.id}>
            {p.name}
          </option>
        ))}
      </select>
  <button className="text-sm px-2 py-1 border rounded-card" disabled={!projectId} onClick={() => setOpenEdit(true)}>Edit</button>
  <button className="text-sm px-2 py-1 border rounded-card" onClick={() => setOpenCreate(true)}>+ Create</button>
      {openCreate && (
        <Modal title="Create Project" onClose={() => { setOpenCreate(false); setShowOntologyForm(false); }}>
          <form
            className="space-y-2"
            onSubmit={(e) => {
              e.preventDefault()
              const fd = new FormData(e.currentTarget as HTMLFormElement)
              const domainName = fd.get('domain') ? String(fd.get('domain')) : null
              const domainDesc = fd.get('description') ? String(fd.get('description')) : null
              createMut.mutate({
                name: String(fd.get('name') || ''),
                ontology_uri: String(fd.get('ontology_uri') || ''),
                knowledge_domain_name: domainName,
                knowledge_domain_description: domainDesc,
              })
            }}
          >
            <label className="block text-sm">Name</label>
            <input name="name" className="border rounded-card px-2 py-1 w-full" required />
            
            <label className="block text-sm">Ontology</label>
            {!showOntologyForm ? (
              <>
                <select name="ontology_uri" className="border rounded-card px-2 py-1 w-full" required>
                  <option value="">Select an ontology...</option>
                  {ontologiesQuery.data?.map((ont) => (
                    <option key={ont.uri} value={ont.uri}>
                      {ont.label} ({ont.uri})
                    </option>
                  ))}
                </select>
                <button
                  type="button"
                  className="text-sm text-blue-600 hover:text-blue-800"
                  onClick={() => setShowOntologyForm(true)}
                >
                  + Create new ontology
                </button>
              </>
            ) : (
              <div className="border rounded-card p-3 bg-gray-50 space-y-2">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-semibold">New Ontology</span>
                  <button
                    type="button"
                    className="text-xs text-gray-600 hover:text-gray-800"
                    onClick={() => setShowOntologyForm(false)}
                  >
                    ✕ Cancel
                  </button>
                </div>
                <label className="block text-xs">URI</label>
                <input
                  name="new_ontology_uri"
                  className="border rounded-card px-2 py-1 w-full text-sm"
                  placeholder="e.g., https://example.org/ontology"
                  required={showOntologyForm}
                />
                <label className="block text-xs">Label</label>
                <input
                  name="new_ontology_label"
                  className="border rounded-card px-2 py-1 w-full text-sm"
                  placeholder="e.g., My Ontology"
                  required={showOntologyForm}
                />
                <label className="block text-xs">Description</label>
                <textarea
                  name="new_ontology_description"
                  className="border rounded-card px-2 py-1 w-full text-sm"
                  placeholder="Describe the ontology..."
                  rows={2}
                  required={showOntologyForm}
                />
                <button
                  type="button"
                  className="w-full px-3 py-1 bg-blue-600 text-white rounded-card text-sm"
                  onClick={(e) => {
                    const form = e.currentTarget.closest('form')!
                    const fd = new FormData(form)
                    createOntologyMut.mutate({
                      ontology_uri: String(fd.get('new_ontology_uri') || ''),
                      ontology_label: String(fd.get('new_ontology_label') || ''),
                      ontology_description: String(fd.get('new_ontology_description') || ''),
                    })
                  }}
                  disabled={createOntologyMut.isPending}
                >
                  {createOntologyMut.isPending ? 'Creating...' : 'Create Ontology'}
                </button>
                {createOntologyMut.isSuccess && (
                  <p className="text-xs text-green-600">
                    ✓ Ontology created! Select it from the dropdown above.
                  </p>
                )}
              </div>
            )}
            
            <label className="block text-sm">Domain Name <span className="text-gray-500">(optional)</span></label>
            <input name="domain" className="border rounded-card px-2 py-1 w-full" />
            <label className="block text-sm">Domain Description <span className="text-gray-500">(optional)</span></label>
            <textarea name="description" className="border rounded-card px-2 py-1 w-full" />
            <p className="text-sm text-gray-600">Note: Knowledge documents and domain areas can be added later.</p>
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" className="px-3 py-1" onClick={() => { setOpenCreate(false); setShowOntologyForm(false); }}>
                Cancel
              </button>
              <button type="submit" className="px-3 py-1 bg-primary-600 text-white rounded-card" disabled={showOntologyForm}>
                Create
              </button>
            </div>
          </form>
        </Modal>
      )}
      {openEdit && (
        <Modal title="Edit Project" onClose={() => setOpenEdit(false)}>
          <form
            className="space-y-2"
            onSubmit={(e) => {
              e.preventDefault()
              const fd = new FormData(e.currentTarget as HTMLFormElement)
              updateMut.mutate({
                name: String(fd.get('name') || ''),
                knowledge_domain_name: String(fd.get('domain') || ''),
                knowledge_domain_description: String(fd.get('description') || ''),
              })
            }}
          >
            <label className="block text-sm">Name</label>
            <input name="name" className="border rounded-card px-2 py-1 w-full" defaultValue={data?.find((p) => p.id === projectId)?.name} />
            <label className="block text-sm">Domain Name</label>
            <input name="domain" className="border rounded-card px-2 py-1 w-full" defaultValue={data?.find((p) => p.id === projectId)?.knowledge_domain_name} />
            <label className="block text-sm">Domain Description</label>
            <textarea name="description" className="border rounded-card px-2 py-1 w-full" />
            <div className="flex justify-end gap-2 pt-2">
              <button type="button" className="px-3 py-1" onClick={() => setOpenEdit(false)}>
                Cancel
              </button>
              <button type="submit" className="px-3 py-1 bg-primary-600 text-white rounded-card">
                Save
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  )
}
