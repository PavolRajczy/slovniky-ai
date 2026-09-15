import { apiFetch } from './client'
import type { OntologyModel } from './types'

export function getProjectOntology(projectId: string, signal?: AbortSignal): Promise<OntologyModel> {
  return apiFetch<OntologyModel>(`/projects/${projectId}/ontology`, { signal })
}
