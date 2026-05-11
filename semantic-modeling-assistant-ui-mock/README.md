# Semantic modeling assistant — mock UI

Static **screenshot prototype** for the production frontend described in `doc/specifikace.tex` (Frontend section).  
**No backend** — all content is placeholder data in `src/data/mockContent.ts`.

Stack: **TypeScript**, **React**, **Vite**, **TanStack Router**, **Tailwind CSS v4** (same family as the specification).

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
