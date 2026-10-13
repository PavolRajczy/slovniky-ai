import { apiFetch } from './client'
import type {
  ExportOntologyToDataSpecerRequest,
  ExportOntologyToOfnRequest,
  ImportOntologyFromDataSpecerRequest,
  OfnDocument,
  OntologyMetadata,
  OntologyModel,
  SuccessResponse,
} from './types'

export function listOntologies(signal?: AbortSignal): Promise<OntologyMetadata[]> {
  return apiFetch<OntologyMetadata[]>('/ontologies', { signal })
}

export function getOntology(uri: string, signal?: AbortSignal): Promise<OntologyModel> {
  return apiFetch<OntologyModel>(`/ontologies/${encodeURIComponent(uri)}`, { signal })
}

export function importOntologyFromDataspecer(
  body: ImportOntologyFromDataSpecerRequest,
): Promise<OntologyMetadata> {
  return apiFetch<OntologyMetadata>('/ontologies/import-from-dataspecer', {
    method: 'POST',
    body,
  })
}

export function exportOntologyToDataspecer(
  body: ExportOntologyToDataSpecerRequest,
): Promise<SuccessResponse> {
  return apiFetch<SuccessResponse>('/ontologies/export-to-dataspecer', {
    method: 'POST',
    body,
  })
}

export function exportOntologyToOfn(body: ExportOntologyToOfnRequest): Promise<OfnDocument> {
  return apiFetch<OfnDocument>('/ontologies/export-to-ofn', {
    method: 'POST',
    body,
  })
}
