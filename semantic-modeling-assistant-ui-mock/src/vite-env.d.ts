/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Backend origin. Empty or `same-origin` = same origin (Docker behind nginx). */
  readonly VITE_API_BASE_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
