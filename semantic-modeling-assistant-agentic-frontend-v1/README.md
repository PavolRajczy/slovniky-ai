# Hybrid AI Conceptual Modeling Assistant – Frontend

A Vite + React + TypeScript app implementing the frontend from `specification/frontend-specification.md`, wired to the backend API in `specification/backend-openapi.json`.

## Tech stack
- Vite, React 18, TypeScript
- Tailwind CSS
- TanStack Router
- TanStack React Query
- Zustand (lightweight state for selections and operations drawer)
- Axios (API client)

## Prerequisites
- Node.js 18+ and npm
- Backend API running locally at http://localhost:8000 (proxy mapped at `/api`)

## Quick start
1) Install dependencies
```powershell
npm install
```
2) Start the dev server
```powershell
npm run dev
```
It will open on http://localhost:5173 (or the next available port). Requests to `/api/*` are proxied to `http://localhost:8000`.

## App structure
- `src/shell/AppShell.tsx` – Persistent frame: Top bar (Project/Ontology selector, search, AI), Left nav (Storyboard, Workbench, Compare & Cover, Ontology, KB, Settings), Right panel (Details/AI/History), Bottom drawer (Prepared operations)
- `src/pages/*` – Pages for each mode/tab
  - `StoryboardPage` – Area filter, status lanes, Suggest Iterations modal, Prepare flow
  - `WorkbenchPage` – Area/Iteration/Tasks tabs scaffolding
  - `CompareCoverPage` – KB vs Coverage scaffolding
  - `OntologyPage` – Ontology view scaffolding + export controls
  - `KnowledgeBasePage` – Project KB lists (legal/expert)
  - `SettingsPage` – Placeholder
- `src/components/*`
  - `ProjectSelector` – List/select projects, Create/Edit modals
  - `OntologySelector` – List/select ontologies, Create/Edit modals
  - `OperationsDrawer` – Prepared operations review with Reject + Apply/Cancel
  - `Modal` – Reusable overlay
- `src/store/*` – Zustand stores for project context and operations drawer
- `src/lib/api.ts` – Typed API client matching backend OpenAPI

## Notes on backend API contract
- All endpoints and shapes are taken from `specification/backend-openapi.json`.
- Vite proxy forwards `/api/*` to `http://localhost:8000` (configure in `vite.config.ts`).

## What’s implemented now
- Project lifecycle: list, create, edit, select
- Ontology lifecycle: list, create, edit, select (frontend-scoped)
- Storyboard: filter by area, list iterations by status, Suggest Iterations (AI), Prepare → operations drawer, Apply/Cancel
- Knowledge Base: shows project legal/expert lists
- Ontology: basic toolbar and placeholders for graph/grid
- Compare & Cover: layout scaffolding

## What’s next (small scoped follow-ups)
- Workbench: implement Area edit form and Reidentify slide-over (api.reidentifyAreas)
- Iterations: manual CRUD and reorder, inline edit menu on cards
- Tasks: Plan Tasks modal, CRUD + reorder in Workbench
- Compare & Cover: document navigator, viewer, coverage overlay (api.getProjectDocumentCoverage), actions (Add to Area, Suggest Iteration from fragment)
- Ontology: render grid and simple graph, highlight changes after Apply
- Global search, AI prompt interactions, Right Panel details/AI/History wiring
- Accessibility passes (ARIA, keyboard traversal), i18n hooks

## Troubleshooting
- If Tailwind classes don’t apply, ensure `postcss.config.js` and `tailwind.config.js` are present and that `src/index.css` is imported in `main.tsx`.
- Ensure the backend is reachable at `http://localhost:8000`; otherwise, adjust proxy in `vite.config.ts`.

## License
See repository-level license.
