import { apiFetch } from './client'
import type {
  AddKnowledgeDocumentsRequest,
  DeleteResponse,
  KnowledgeBaseResponse,
  SetKeyDocumentRequest,
  SuccessResponse,
} from './types'

export function getProjectKnowledgeBase(
  projectId: string,
  signal?: AbortSignal,
): Promise<KnowledgeBaseResponse> {
  return apiFetch<KnowledgeBaseResponse>(`/projects/${projectId}/knowledge-base`, { signal })
}

export function addLegalDocuments(
  projectId: string,
  body: AddKnowledgeDocumentsRequest,
): Promise<SuccessResponse> {
  return apiFetch<SuccessResponse>(`/projects/${projectId}/knowledge-base/legal`, {
    method: 'POST',
    body,
  })
}

export function removeLegalDocument(
  projectId: string,
  documentId: string,
): Promise<DeleteResponse> {
  return apiFetch<DeleteResponse>(
    `/projects/${projectId}/knowledge-base/legal/${encodeURIComponent(documentId)}`,
    { method: 'DELETE' },
  )
}

export function addExpertDocuments(
  projectId: string,
  body: AddKnowledgeDocumentsRequest,
): Promise<SuccessResponse> {
  return apiFetch<SuccessResponse>(`/projects/${projectId}/knowledge-base/expert`, {
    method: 'POST',
    body,
  })
}

export function removeExpertDocument(
  projectId: string,
  documentId: string,
): Promise<DeleteResponse> {
  return apiFetch<DeleteResponse>(
    `/projects/${projectId}/knowledge-base/expert/${encodeURIComponent(documentId)}`,
    { method: 'DELETE' },
  )
}

export function setKeyDocument(
  projectId: string,
  body: SetKeyDocumentRequest,
): Promise<SuccessResponse> {
  return apiFetch<SuccessResponse>(`/projects/${projectId}/key-document`, {
    method: 'PUT',
    body,
  })
}
