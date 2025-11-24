import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { useProjectStore } from '@/store/projectStore'

export function OntologySelector() {
  const { projectId } = useProjectStore()
  
  // Get all projects to find the selected one
  const projectsQuery = useQuery({
    queryKey: ['projects'],
    queryFn: () => api.listProjects(),
  })
  
  // Get all ontologies to map URI to label
  const ontologiesQuery = useQuery({
    queryKey: ['ontologies'],
    queryFn: () => api.listOntologies(),
  })

  // Find the current project
  const currentProject = projectsQuery.data?.find((p) => p.id === projectId)
  
  // Find the ontology for the current project
  const currentOntology = currentProject
    ? ontologiesQuery.data?.find((o) => o.uri === currentProject.ontology_uri)
    : null

  return (
    <div className="flex items-center gap-2">
      <span className="font-semibold">Ontology:</span>
      {currentProject && currentOntology ? (
        <span className="text-sm px-2 py-1 bg-gray-100 rounded-card">
          {currentOntology.label}
        </span>
      ) : (
        <span className="text-sm text-gray-400 italic">
          {projectId ? 'Loading...' : 'No project selected'}
        </span>
      )}
    </div>
  )
}
