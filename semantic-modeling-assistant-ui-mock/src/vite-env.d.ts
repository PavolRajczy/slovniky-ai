/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Backend origin. Empty or `same-origin` = same origin (Docker behind nginx). */
  readonly VITE_API_BASE_URL?: string
  /** Dataspecer UI origin. Defaults to the same origin behind the gateway, else http://localhost:3000. */
  readonly VITE_DATASPECER_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
