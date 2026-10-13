import { ApiError, apiFetch, getApiBaseUrl } from './client'
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

export async function uploadExpertDocument(
  projectId: string,
  file: File,
): Promise<SuccessResponse> {
  const body = new FormData()
  body.append('file', file)
  const base = getApiBaseUrl()
  const path = `/api/projects/${projectId}/knowledge-base/expert/upload`
  const url = base.length > 0 ? `${base}${path}` : path
  const response = await fetch(url, {
    method: 'POST',
    body,
    headers: { Accept: 'application/json' },
  })
  const text = await response.text()
  let parsed: unknown = null
  if (text.length > 0) {
    try {
      parsed = JSON.parse(text)
    } catch {
      parsed = text
    }
  }
  if (!response.ok) {
    const message =
      typeof parsed === 'object' && parsed !== null && 'message' in parsed
        ? String((parsed as { message: unknown }).message)
        : response.statusText || 'Upload failed.'
    throw new ApiError(response.status, message, parsed as never)
  }
  return parsed as SuccessResponse
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
