# Semantic modeling assistant — mock UI

Production-track frontend for the assistant described in `doc/specifikace.tex` (Frontend section). The app is being wired to the FastAPI backend in [`semantic-modeling-assistant-agentic-backend`](../semantic-modeling-assistant-agentic-backend) screen-by-screen; remaining static placeholders live in `src/data/mockContent.ts` and are removed as each commit lands.

Stack: **TypeScript**, **React**, **Vite**, **TanStack Router**, **TanStack Query**, **Tailwind CSS v4** (same family as the specification).

## Backend connection

The UI talks to the backend via `VITE_API_BASE_URL` (defaults to `http://localhost:8000`). Copy `.env.example` to `.env.local` and adjust if your backend runs elsewhere. The sidebar header shows a live "Backend OK / Backend down" pill.

## Run locally

```bash
cd semantic-modeling-assistant-ui-mock
npm install
npm run dev
```

Open the printed local URL (typically `http://localhost:5173`).

## Routes (for screenshots)

| Path | Spec view |
|------|-----------|
| `/` | Redirects to `/project` |
| `/project` | Project & knowledge base setup |
| `/domain-areas` | Domain areas |
| `/iterations` | Iterations (subarea + goal) |
| `/operations` | Operations review + preview panel |
| `/tasks` | Task list and task detail flow |
| `/guidance` | Project guidance (Type B HITL) |
| `/export-result` | Export result / output overview |

## Build

```bash
npm run build
npm run preview
```

## Relation to `semantic-modeling-assistant-agentic-frontend-v2`

The debug frontend `v2` is **not** this app. This package is a separate visual baseline for documentation and thesis figures.
