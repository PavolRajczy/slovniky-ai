import { ApiError, apiFetch, apiUrl } from './client'
import type {
  AddKnowledgeDocumentsRequest,
  DeleteResponse,
  DocumentProcessingJob,
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

export function uploadExpertDocument(
  projectId: string,
  file: File,
): Promise<SuccessResponse> {
  return postFile<SuccessResponse>(`/api/projects/${projectId}/knowledge-base/expert/upload`, file)
}

/** Starts loading, summarizing and indexing a legal act; poll the job with getDocumentProcessingJob. */
export function startLegalDocumentJob(
  projectId: string,
  documentId: string,
): Promise<DocumentProcessingJob> {
  return apiFetch<DocumentProcessingJob>(`/projects/${projectId}/knowledge-base/legal/jobs`, {
    method: 'POST',
    body: { document_ids: [documentId] },
  })
}

/** Uploads a PDF or DOCX and starts processing it; poll the job with getDocumentProcessingJob. */
export function startExpertUploadJob(
  projectId: string,
  file: File,
): Promise<DocumentProcessingJob> {
  return postFile<DocumentProcessingJob>(
    `/api/projects/${projectId}/knowledge-base/expert/upload/jobs`,
    file,
  )
}

export function getDocumentProcessingJob(
  projectId: string,
  jobId: string,
  signal?: AbortSignal,
): Promise<DocumentProcessingJob> {
  return apiFetch<DocumentProcessingJob>(`/projects/${projectId}/knowledge-base/jobs/${jobId}`, {
    signal,
  })
}

async function postFile<T>(apiPath: string, file: File): Promise<T> {
  const body = new FormData()
  body.append('file', file)
  const url = apiUrl(apiPath)
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
  return parsed as T
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
