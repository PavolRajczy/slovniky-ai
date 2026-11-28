/**
 * Typed fetch wrapper used by every API module.
 *
 * The backend lives at `import.meta.env.VITE_API_BASE_URL` (defaults to
 * `http://localhost:8000`). Set it to `same-origin` or an empty string when
 * the UI is served behind a reverse proxy that forwards `/api` next to the UI,
 * i.e. `<UI base path>/api`. All requests use `${base}/api/...` so callers pass
 * just the route, e.g. `apiFetch('/projects')`.
 */

import { APP_BASE_PATH } from '@/basePath'
import type { ApiErrorBody } from './types'

const DEFAULT_BASE_URL = 'http://localhost:8000'

function getApiBaseUrl(): string {
  const fromEnv = import.meta.env.VITE_API_BASE_URL
  if (fromEnv === undefined || fromEnv === null) {
    return DEFAULT_BASE_URL
  }
  const trimmed = String(fromEnv).replace(/\/+$/, '')
  if (trimmed === '' || trimmed === 'same-origin') {
    return APP_BASE_PATH
  }
  return trimmed
}

/** Absolute URL of a backend route given as `/api/...`. */
export function apiUrl(apiPath: string): URL {
  return new URL(`${getApiBaseUrl()}${apiPath}`, window.location.origin)
}

export class ApiError extends Error {
  readonly status: number
  readonly body: ApiErrorBody | string | null

  constructor(status: number, message: string, body: ApiErrorBody | string | null) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.body = body
  }
}

export type ApiFetchOptions = {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  body?: unknown
  signal?: AbortSignal
  query?: Record<string, string | number | boolean | undefined>
}

function buildUrl(path: string, query?: ApiFetchOptions['query']): string {
  const normalized = path.startsWith('/') ? path : `/${path}`
  const url = apiUrl(`/api${normalized}`)
  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value === undefined) {
        continue
      }
      url.searchParams.set(key, String(value))
    }
  }
  return url.toString()
}

export async function apiFetch<T>(path: string, options: ApiFetchOptions = {}): Promise<T> {
  const { method = 'GET', body, signal, query } = options
  const init: RequestInit = {
    method,
    signal,
    headers: {
      Accept: 'application/json',
    },
  }
  if (body !== undefined) {
    init.body = JSON.stringify(body)
    init.headers = { ...init.headers, 'Content-Type': 'application/json' }
  }

  const response = await fetch(buildUrl(path, query), init)

  if (response.status === 204) {
    return undefined as T
  }

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
        ? String((parsed as ApiErrorBody).message)
        : response.statusText || `Request failed with status ${response.status}`
    throw new ApiError(response.status, message, parsed as ApiErrorBody | string | null)
  }

  return parsed as T
}
