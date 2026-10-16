/**
 * Public URL path the UI is mounted under, without a trailing slash
 * (`''` at the site root, `'/slovniky-ai'` under a sub-path).
 *
 * Derived from Vite's `base`. The Docker image builds with a placeholder base
 * that its entrypoint replaces with the `BASE_PATH` env variable, so the same
 * image can be served under any path.
 */
export const APP_BASE_PATH = import.meta.env.BASE_URL.replace(/\/+$/, '')
