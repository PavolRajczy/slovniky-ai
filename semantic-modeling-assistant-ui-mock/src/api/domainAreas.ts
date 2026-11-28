import { apiFetch } from './client'
import type {
  CreateDomainAreaRequest,
  GenerateDomainAreasRequest,
  KnowledgeDomainAreaModel,
  ReidentifyDomainAreasRequest,
  SuccessResponse,
  UpdateDomainAreaRequest,
} from './types'

export function listDomainAreas(
  projectId: string,
  signal?: AbortSignal,
): Promise<KnowledgeDomainAreaModel[]> {
  return apiFetch<KnowledgeDomainAreaModel[]>(`/projects/${projectId}/domain-areas`, { signal })
}

export function createDomainArea(
  projectId: string,
  body: CreateDomainAreaRequest,
): Promise<KnowledgeDomainAreaModel> {
  return apiFetch<KnowledgeDomainAreaModel>(`/projects/${projectId}/domain-areas`, {
    method: 'POST',
    body,
  })
}

export function updateDomainArea(
  projectId: string,
  areaId: string,
  body: UpdateDomainAreaRequest,
): Promise<KnowledgeDomainAreaModel> {
  return apiFetch<KnowledgeDomainAreaModel>(`/projects/${projectId}/domain-areas/${areaId}`, {
    method: 'PUT',
    body,
  })
}

export function deleteDomainArea(
  projectId: string,
  areaId: string,
): Promise<SuccessResponse> {
  return apiFetch<SuccessResponse>(`/projects/${projectId}/domain-areas/${areaId}`, {
    method: 'DELETE',
  })
}

export function generateDomainAreas(
  projectId: string,
  body: GenerateDomainAreasRequest,
): Promise<KnowledgeDomainAreaModel[]> {
  return apiFetch<KnowledgeDomainAreaModel[]>(`/projects/${projectId}/domain-areas/generate`, {
    method: 'POST',
    body,
  })
}

export function reidentifyDomainAreas(
  projectId: string,
  body: ReidentifyDomainAreasRequest,
): Promise<KnowledgeDomainAreaModel[]> {
  return apiFetch<KnowledgeDomainAreaModel[]>(`/projects/${projectId}/domain-areas/reidentify`, {
    method: 'POST',
    body,
  })
}
