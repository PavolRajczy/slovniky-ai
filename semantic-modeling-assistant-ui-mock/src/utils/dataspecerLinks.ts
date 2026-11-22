import { APP_BASE_PATH } from '@/basePath'

const LOCAL_DATASPECER_URL = 'http://localhost:3000'

/**
 * Origin of the Dataspecer UI. Behind the gateway Dataspecer is served at the site root of the
 * same origin; in local development it runs on its own port unless VITE_DATASPECER_URL says otherwise.
 */
export function dataspecerOrigin(): string {
  const configured = import.meta.env.VITE_DATASPECER_URL?.trim()
  if (configured) return configured.replace(/\/+$/, '')
  return APP_BASE_PATH ? window.location.origin : LOCAL_DATASPECER_URL
}

/** Link to the Dataspecer editor of the vocabulary the project is linked to. */
export function dataspecerEditorUrl(packageIri: string): string {
  return `${dataspecerOrigin()}/conceptual-model-editor/diagram?package-id=${encodeURIComponent(packageIri)}`
}
