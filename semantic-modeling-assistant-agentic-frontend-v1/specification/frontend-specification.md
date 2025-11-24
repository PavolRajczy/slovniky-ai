# Frontend Specification – Consolidated Complete (vFinal)

**API Version**: This specification reflects **API v2.1** (updated January 2025).

The **Hybrid AI Modeling Assistant** is a web application for designing and evolving ontology‑based data specifications with **AI assistance** and **human‑in‑the‑loop control**. The UI orchestrates planning (roadmap), detailed modeling (editing & execution), and evidence‑based validation (coverage vs. documents) in a single, consistent shell.

This consolidated specification merges all design decisions from our threads into a single source of truth. It focuses on **clarity for developers** while preserving UX rationale and states.

---

## 0. API Version History

### API v2.1 (Current - January 2025)

**Breaking Changes:**
1. **Iteration Status Values** - Changed to better reflect workflow semantics:
   - `'planned'` → `'suggested'` (iteration exists but no tasks planned yet)
   - `'in_progress'` → `'planned'` (tasks have been planned)
   - Status `'prepared'` remains unchanged
   - `'completed'` (renamed from `'finished'` for consistency)

2. **Task Status Values** - Updated to match AI generation terminology:
   - `'planned'` remains unchanged
   - `'in_progress'` → `'generating'` (AI is generating/executing the task)
   - `'completed'` (renamed from `'finished'` for consistency)

3. **API Endpoints** - Iteration-specific operations now require iteration ID:
   - `/iterations/current/apply` → `/iterations/{iterationId}/apply`
   - New endpoint: `/iterations/{iterationId}/cancel` (cancels prepared iteration)
   - Operations parameter in apply endpoint is now optional (server-side persistence)

4. **Ontology Element Definition Field** - Backend now properly returns the `definition` field:
   - All ontology elements (classes, attributes, relationships) now include optional `definition` field
   - Corresponds to `skos:definition` in RDF (formal definition)
   - Distinct from `description` field which corresponds to `rdfs:comment` (contextual notes)
   - Frontend updated to display both fields with visual distinction
   - Search functionality updated to search both definition and description

**Migration Impact:**
- Frontend updated to use new status literals throughout UI components
- Status badge colors and labels updated to match new semantics
- API client methods updated to use new endpoint patterns
- OntologyGrid component updated to display and search definition field
- All changes are backward-incompatible; requires coordinated backend deployment

---

## 0.1. Product Goals & UX Principles

**Goals**
1) Make planning and execution of ontology changes **visible and controllable**.  
2) Let AI do the heavy lifting (suggest/reidentify/plan/prepare) while users **approve before apply**.  
3) Maintain **traceability** from knowledge documents → domain areas → iterations → ontology operations → final ontology.

**Core UX principles**
- **One mental model**: *Document → Area → Iteration → Tasks → Operations → Ontology*. Breadcrumbs, mode transitions, and context persistence enforce this.
- **AI transparency**: Input prompt, preview results, explicit confirm; AI reasoning tab shows the "why".
- **Consistency**: Same chips, colors, icons, and terms across all screens; same interactions for lists/trees/cards.
- **Progressive disclosure**: Summaries first (cards/lanes), details on demand (tabs/forms/drawers).
- **Accessibility by default**: Keyboard navigation, ARIA roles, high‑contrast coverage markers.

---

## 0.2. Key Concepts

**Project KB vs Global KB**  
- Documents exist globally; **projects attach/detach references** (remove from project ≠ delete document).  
- **Key Document** for reidentification **must be one of the project's Legal/Expert docs** (not a special document).

**Project and Ontology Association**
- Each project is associated with exactly one ontology selected during project creation.
- Ontology selection uses a dropdown populated from all loaded ontologies (via `GET /ontologies`).
- Ontology cannot be changed after project creation; only project metadata (name, domain) can be edited.
- The dropdown displays ontologies in format: "{label} ({uri})" for easy identification.

**Iterations & Areas**
- Iterations belong to a **project** and are **scoped to a single domain area**.
- Storyboard groups iterations by area.
- Iteration detail shows its owning area.

**Goals**
1) Make planning and execution of ontology changes **visible and controllable**.  
2) Let AI do the heavy lifting (suggest/reidentify/plan/prepare) while users **approve before apply**.  
3) Maintain **traceability** from knowledge documents → domain areas → iterations → ontology operations → final ontology.

**Core UX principles**
- **One mental model**: *Document → Area → Iteration → Tasks → Operations → Ontology*. Breadcrumbs, mode transitions, and context persistence enforce this.
- **AI transparency**: Input prompt, preview results, explicit confirm; AI reasoning tab shows the “why”.
- **Consistency**: Same chips, colors, icons, and terms across all screens; same interactions for lists/trees/cards.
- **Progressive disclosure**: Summaries first (cards/lanes), details on demand (tabs/forms/drawers).
- **Accessibility by default**: Keyboard navigation, ARIA roles, high‑contrast coverage markers.

---

## 1. Application Frame (Persistent Shell)

```
┌──────────────────────────────────────────────────────────────┐
│ Top Bar – Project & Ontology context | Global Search | AI ✨ │
├───────────────┬───────────────────────────────┬──────────────┤
│ Left Nav      │ Central Workspace (by mode)   │ Right Panel  │
├───────────────┴───────────────────────────────┴──────────────┤
│ Bottom Drawer – Prepared Operations | Long‑running statuses  │
└──────────────────────────────────────────────────────────────┘
```

**Top Bar**
- **Project Selector** (+Create, Edit). Switching projects reloads all mode content.
  - Create: Name (required), Ontology (required, dropdown selector from loaded ontologies), Domain Name (optional), Domain Description (optional)
    - Note: Projects are created with an empty knowledge base. Knowledge documents and domain areas can be added later via:
      1. Add knowledge documents (legal/expert)
      2. Set key document for reidentification
      3. Generate domain areas from documents
  - Edit: Name, Domain Name, Domain Description (ontology cannot be changed after creation)
- **Ontology Display** shows the label of the ontology associated with the currently selected project (read-only).
  - Displays as a badge/label (not a dropdown selector)
  - Shows "No project selected" when no project is active
  - The ontology is locked to the project and cannot be changed after project creation
- **Global Search** across Projects/Areas/Iterations/Tasks/Documents (client index; navigates to entity view).
- **AI Prompt**: contextual action launcher; shows a compact run/progress indicator; mirrors results in Right Panel › *AI Reasoning*.

**Left Navigation**
- Modes: **Storyboard**, **Workbench**, **Compare & Cover**, plus quick links: **Ontology**, **Knowledge Base**, **Settings**.
- Mode switch preserves selected entity context.

**Right Panel (tabs)**
- **Details** (read‑only entity data), **AI Reasoning** (inputs/outputs/summaries), **History** (recent actions). Collapsible.

**Bottom Drawer (frame‑anchored)**
- Reserved as placeholder for future features (e.g., long-running job statuses).

**Breadcrumbs**
- Shown below Top Bar: `[Project] › [Area] › [Iteration] › [Task]` (clickable; smart routing between modes).

---

## 2. Design Tokens & Visual Language

- **Spacing**: 4/8/12/16/24/32 (base = 8).  
- **Radii**: 8 (cards), 16 (drawers/modals).  
- **Elevation**: card (sm), panel (md), drawer (lg).  
- **Typography**: Title 24/32 700; Section 18/24 600; Body 14/20 400; Caption 12/16 500.  
- **Colors**: Primary Indigo; **AI** Info Blue; **Success** Green; **Warning** Amber; **Danger** Red.  
- **Status Chips**:  
  - Iteration: `suggested` (light gray), `planned` (blue), `prepared` (green), `completed` (green).  
  - Task: `planned` (white), `generating` (blue), `completed` (green).  
  - Operation target types: Class / Attribute / Relationship (distinct icons).
- **Iconography**: Project 📁, Ontology 🧩, Area 🗂️, Iteration 🔄, Task ✅, Document 📄, Diff ≋, AI ✨.
- **Motion**: subtle fade/slide for mode swaps; drawers slide from bottom; modals zoom/fade.

---

## 3. Information Architecture & Modes

- **Storyboard Mode** (plan‑first): domain area lanes → iteration cards grouped by workflow status (Suggested → Planned → Prepared → Completed); AI *Suggest Iterations*.
- **Workbench Mode** (expert edit): tabs for **Area**, **Iteration**, **Tasks**, **Ontology**; AI *Reidentify Areas*, *Plan Tasks*, *Prepare*; operations modal for review and apply.
- **Compare & Cover Mode** (validation): document navigator + viewer with **Coverage overlay**; matched ontology list; actions: *Add to Area*, *Suggest Iteration*.

**Project KB vs Global KB**  
- Documents exist globally; **projects attach/detach references** (remove from project ≠ delete document).  
- **Key Document** for reidentification **must be one of the project’s Legal/Expert docs** (not a special document).

**Iterations & Areas**  
- Iterations belong to a **project** and are **scoped to a single domain area**; Storyboard groups iterations by area; Iteration detail shows its owning area.

---

## 4. Wireframes WITH Frame Placement (where each screen lives)

### 4.1 Application Frame (container)
(See ASCII frame above.) Everything below inserts into **Central Workspace** unless labeled *modal*/*drawer*.

### 4.2 Storyboard – Roadmap Overview (Central Workspace)
```
Top Controls (under Top Bar): [Area ▾] [Status Chips] [✨ Suggest Iterations]
┌────────────────────────────────────────────────────────────────────┐
│ Lane: <Area>    [Manage Area] [View Coverage] [+ Iteration]        │
├───────────────┬───────────────┬───────────────┬───────────────┤
│ SUGGESTED     │ PLANNED       │ PREPARED      │ COMPLETED     │
│ [Cards…]      │ [Cards…]      │ [Cards…]      │ [Cards…]      │
└───────────────┴───────────────┴───────────────┴───────────────┘
```
- **Suggested**: Iterations without planned tasks (planned_tasks_count = 0). Button: [Plan Tasks ✨]
- **Planned**: Iterations with planned tasks (planned_tasks_count > 0). Buttons: [View Tasks] [Prepare ▶]
- **Prepared**: Current iteration with status 'prepared'. Buttons: [View Operations] [Apply Changes]
- **Completed**: Completed iterations. Button: [View Details]
- **Right Panel** shows details of the selected card.
- **Left Nav** active = Storyboard; switching modes preserves selected area/iteration.

**Card anatomy**: 
- **Title**: Clickable name (blue on hover) that expands/collapses the specification
- **Specification**: Shows 2-line clamp by default; click anywhere on title or specification to toggle full view
- **Action buttons**: Context-specific buttons (Plan Tasks, View Tasks, Prepare, etc.)
- **Status indicators**: Tasks count (for planned), completion checkmark (for completed)
- **Interactive states**: 
  - Collapsed (default): Shows title + 2-line specification snippet
  - Expanded: Shows title + full specification text
  - Only one card can be expanded at a time; clicking another card collapses the previous one

**Suggest Iterations – Modal (overlay)**
```
Focused Area [select] • Count [1..20] • Instruction [optional]
[Preview] → [Insert to Suggested] | [Insert & Open]
```

### 4.3 Workbench – Area Tab (Central Workspace with Left Tree)
```
Left Tree (Areas ▾, Iterations ▾)      Area Form (Main Panel)         Right Panel
[+ Add Area] [+ Iteration]             Label | Description | Parent    Details / AI / History
                                       Key Concepts [tags]
                                       [Save] [Delete] [Reidentify ✨]
```
**Reidentify Areas – Slide‑over (overlaying Central Workspace)**  
Key Document (from **Project KB only**) + Instruction → *Preview current vs proposed* → *Apply*.

### 4.4 Workbench – Iteration Tab (Central Workspace)
```
Header: Name [✏️]  Status [chip]  Focused Area (link)
Specification [multiline]
[Save] [Check Coverage] [Prepare ▶]
```
- **Prepare** → progress pane (inline) then caches prepared operations for later viewing.

### 4.5 Workbench – Tasks Tab (Central Workspace)
```
Toolbar: [✨ Plan Tasks] [+ Add Task] [Reorder]
List rows: ⠿ Title (AI badge?)  ⋯ Edit | Delete  (Description tooltip)
```
**Plan Tasks – Modal (overlay)**: Instruction (optional) → preview → insert tasks.

**Task Status Values** (API v2.1):
- `planned`: Task is planned but not yet started
- `generating`: Task is currently being generated/executed by AI
- `completed`: Task has been completed

### 4.6 Workbench – Ontology Tab (Central Workspace)

**Implementation Status: Phase 2 Complete (Grid View with Semantic Filtering)**

**Header Section**
```
┌─────────────────────────────────────────────────────────────────────┐
│ Statistics Cards (read-only summary)                                │
│ ┌───────────┬───────────┬───────────┐                               │
│ │ Classes   │ Attributes│Relationships                              │
│ │    42     │    156    │    89     │                               │
│ └───────────┴───────────┴───────────┘                               │
│                                                                      │
│ Controls: [Search 🔍] [Export JSON ⬇] [Export RDF ⬇]               │
└─────────────────────────────────────────────────────────────────────┘
```

**Three-Panel Semantic Grid**
```
┌──────── Classes (Hierarchical Tree) ──┬──────── Attributes ──────┬─── Relationships ───┐
│ [Expand All] [Collapse All]           │ Label      Domain  Type  │ Label   From → To   │
├────────────────────────────────────────┼──────────────────────────┼─────────────────────┤
│ ▼ Thing                                │ name       Person  text  │ knows   Person→Person
│   ▼ Person                             │ age        Person  int   │ worksAt Person→Org  │
│     ├── Employee                       │ founded    Org     date  │ ...                 │
│     └── Manager                        │ ...                      │                     │
│ ▼ Organization                         │                          │                     │
│   └── Company                          │                          │                     │
└────────────────────────────────────────┴──────────────────────────┴─────────────────────┘
         ↕ Context-aware bidirectional filtering + smart auto-expand ↕
```

**Grid View Features (Implemented)**
1. **Hierarchical Tree View for Classes** (NEW)
   - Recursive tree structure built from `parent_classes` relationships
   - Visual hierarchy with indentation (16px per level)
   - Expand/collapse controls:
     - Individual node toggle with ▶ (collapsed) / ▼ (expanded) icons
     - "Expand All" / "Collapse All" buttons in panel header
   - Child count badges shown when collapsed (e.g., "Person (5)")
   - Smart auto-expand behavior:
     - **Search**: Automatically expands ancestors of matching classes
     - **Semantic Filter**: Expands ancestors when attribute/relationship selected
     - **Navigation**: Expands ancestor chain when clicking class references
   - Preserves manual expand/collapse state across interactions
   - Cycle detection prevents infinite loops in circular hierarchies
   - Multi-parent support: classes with multiple parents shown under each parent

2. **Three-Panel Layout**: Classes, Attributes, and Relationships in separate scrollable panels
   - Each panel has independent scrolling with overflow handling
   - Color-coded headers: Classes (blue), Attributes (green), Relationships (purple)
   - Consistent row interaction patterns across all panels

3. **Semantic Filtering** (bidirectional)
   3. **Semantic Filtering** (bidirectional)
   - **Class → Attributes/Relationships**: Selecting a class filters to show only attributes/relationships that reference it
   - **Attribute → Classes**: Selecting an attribute highlights its domain class
   - **Relationship → Classes**: Selecting a relationship highlights both domain and range classes
   - Empty states with contextual messages (e.g., "No attributes for this class")

4. **Interactive Navigation**
   - All class references are **clickable** (parent classes, domain classes, range classes)
   - Clicking a class reference navigates to that class in the Classes panel
   - Selected elements are highlighted with colored backgrounds
   - **Auto-scroll**: Clicking navigation links automatically scrolls the target element into view
     - Uses smooth scrolling behavior with center alignment
     - Works across all three panels (classes, attributes, relationships)
     - For hierarchical classes: Auto-expands ancestor chain before scrolling

5. **Smart Label Display**
   - URIs are **hidden** from the grid view for cleaner UI
   - Shows human-readable labels with intelligent fallback:
     - Primary: `element.label`
     - Fallback 1: Extract last segment from URI (after final `/` or `#`)
     - Fallback 2: Show full URI if no other option
   - Parent classes, domain classes, and range classes show as clickable labels

6. **Search Integration**
   - Search box filters across all three panels simultaneously
   - Case-insensitive matching on labels and URIs
   - Results update in real-time as user types
   - Auto-expands hierarchy to reveal matching classes

7. **Export Functionality**

3. **Interactive Navigation**
   - All class references are **clickable** (parent classes, domain classes, range classes)
   - Clicking a class reference navigates to that class in the Classes panel
   - Selected elements are highlighted with colored backgrounds
   - **Auto-scroll**: Clicking navigation links automatically scrolls the target element into view
     - Uses smooth scrolling behavior with center alignment
     - Works across all three panels (classes, attributes, relationships)

4. **Smart Label Display**
   - URIs are **hidden** from the grid view for cleaner UI
   - Shows human-readable labels with intelligent fallback:
     - Primary: `element.label`
     - Fallback 1: Extract last segment from URI (after final `/` or `#`)
     - Fallback 2: Show full URI if no other option
   - Parent classes, domain classes, and range classes show as clickable labels

5. **Search Integration**
   - Search box filters across all three panels simultaneously
   - Case-insensitive matching on labels and URIs
   - Results update in real-time as user types

6. **Export Functionality**
   - **Export JSON**: Downloads ontology as JSON file (`ontology.json`)
   - **Export RDF**: Downloads ontology in RDF/Turtle format (`ontology.ttl`)
   - Uses browser download API with proper MIME types

7. **Visual States**
   - **Selection**: Highlighted rows with color-coded backgrounds
   - **Hover**: Subtle background change on row hover
   - **Empty**: Contextual messages when no data or filtered to zero results
   - **Loading**: Skeleton/spinner states during data fetch
   - **Error**: Clear error messages with retry options

**Data Flow**
- API endpoint: `GET /api/projects/{projectId}/ontology?format=json` returns `OntologyModel`
- TypeScript types: `OntologyClassModel`, `OntologyAttributeModel`, `OntologyRelationshipModel`
- State management: React useState for selection, useMemo for filtered lists, useRef for scroll targets
- TanStack Query: Handles caching, loading, error states, and refetching

**Component Structure**
- `src/pages/OntologyPage.tsx`: Main page with header, stats, controls, and grid container
- `src/components/OntologyGrid.tsx`: Three-panel grid with all interactive features
- `src/lib/api.ts`: Type definitions and API client functions

**Future Enhancements** (Not Yet Implemented)
- Graph visualization with React Flow (zoom, pan, interactive nodes)
- Right Panel integration (click element → view full details in side panel)
- Change highlighting (track and visualize post-apply ontology changes)
- Advanced filtering options (by type, by parent, by domain/range)
- Bulk operations (multi-select, batch export)

### 4.7 Tasks Modal (overlay)
```
Title: "Iteration Tasks"
┌─────────────────────────────────────────────────────────────┐
│ Summary: Planned: N | Generating: M | Completed: K          │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ [Task Name]                                             │ │
│ │ Specification text...                                   │ │
│ │ Status: planned/generating/completed                    │ │
│ └─────────────────────────────────────────────────────────┘ │
│ [Close]                                                     │
└─────────────────────────────────────────────────────────────┘
```
- Opened from Storyboard "View Tasks" button on Planned iterations
- Color-coded by status: planned (white), generating (blue bg), completed (green bg)
- Read-only view for reviewing iteration tasks

### 4.8 Operations Modal (overlay)
```
Title: "Operations"
┌─────────────────────────────────────────────────────────────┐
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ [Badge: Add/Remove/Modify Class/Attribute/Relationship] │ │
│ │ URI: <uri>                                              │ │
│ │ Label: <label>                                          │ │
│ │ Definition: <definition>                                │ │
│ │ Description: <description>                              │ │
│ │ [Target-type specific fields:]                          │ │
│ │   - Class: Generalizations                              │ │
│ │   - Attribute: Domain, Kind                             │ │
│ │   - Relationship: Source, Target                        │ │
│ │ [References: definition_refs, spec_refs, refs]          │ │
│ └─────────────────────────────────────────────────────────┘ │
│ [Apply Changes]  [Cancel]                                   │
└─────────────────────────────────────────────────────────────┘
```
- Opened from Storyboard "View Operations" button on Prepared iterations
- Badge colors: Add (green), Remove (red), Modify (blue)
- Displays all operation details including URIs, labels, definitions, and target-specific fields
- Apply Changes: executes the iteration and moves it to Completed column
- Operations are cached after Prepare and retrieved from cache when viewing

### 4.9 Compare & Cover – Document Coverage (Central Workspace)
```
Top Controls: [Project KB ▾ | Global KB] [Coverage: OFF/ON]
Left: Docs & Outline  |  Center: Document with coverage chips  |  Right: Matched Ontology + Actions
Paragraph menu: [View Matches] [Add to Area…] [✨ Suggest Iteration]
```
- **Banner** if document not attached to project: “Add to Project?”
- **Coverage legend** explains states: *Defined* / *Specified* / *Referenced* / *Uncovered*.

**Add to Area – Modal (overlay)**: pick Area + optional note → link saved to area metadata.

**Suggest Iteration from Fragment – Modal**: Prefilled area + fragment summary; K & instruction → preview → insert.

---

## 5. Detailed Behaviors & Edge Cases

**Context persistence**  
- Switching modes keeps `[project, area?, iteration?, task?]` selection.  
- Re‑opening Storyboard scrolls to the last active area lane and card.

**Iteration card expansion**
- By default, iteration cards show a 2-line clamp of the specification text for space efficiency.
- Clicking on the card's title or specification area toggles expansion to show the full specification.
- Only one card can be expanded at a time across all columns; expanding a new card automatically collapses the previously expanded one.
- Visual feedback: title shows blue hover color to indicate clickability; cursor changes to pointer on hover.
- Expansion state is ephemeral (not persisted); navigating away resets all cards to collapsed state.

**Button states and async action feedback**
- Long-running async actions (Plan Tasks, Prepare, Apply Changes) provide immediate visual feedback when initiated.
- **Plan Tasks**: Button shows "Planning..." with disabled state while AI generates tasks.
- **Prepare**: Button shows "⏳ Preparing..." with disabled state while generating operations; includes error handling with user alert on failure.
- **Apply Changes**: Button shows "Applying..." with disabled state while executing operations.
- Buttons are disabled during their respective operations to prevent duplicate submissions.
- Visual feedback includes label change, optional icon (hourglass ⏳), and reduced opacity (disabled state).
- On completion, button re-enables and UI updates to reflect new state (e.g., iteration moves to next column).

**Iteration lifecycle**  
- Suggested iterations start with no tasks (planned_tasks_count = 0); use "Plan Tasks" to add tasks and move to Planned.
- Planned iterations have tasks (planned_tasks_count > 0); use "Prepare" to generate operations and move to Prepared.
- Prepared iterations have cached operations ready to review; use "Apply Changes" to execute and move to Completed.
- Users can edit iterations freely in suggested/planned states; prepared iterations show operations in modal for review before apply.

**Operations review**  
- Operations are generated during "Prepare" and cached in the operations store by iteration ID.
- Click "View Operations" on prepared iterations to open modal showing detailed operation information.
- Each operation displays: type badge (Add/Remove/Modify), URI, label, definition, description, target-type specific fields.
- Modal includes "Apply Changes" button to execute operations and "Cancel" to close without applying.
- After successful apply, iteration moves to Completed column and operations cache is cleared.

**Ontology highlights**  
- Client snapshots just before Apply allow post‑apply highlighting (+added/~changed/−deleted markers in Grid/Graph).

**Coverage semantics**  
- *Defined*: ontology element directly models the fragment.  
- *Specified*: fragment constrains an already modeled element.  
- *Referenced*: fragment is cited/linked but not modeled.  
- *Uncovered*: no mapping yet.

**Key Document rule**  
- In Reidentify Areas, the **Key Document must be selected from Project KB** (Legal/Expert); this prevents out‑of‑scope drift.

**Global vs Project KB**  
- *Add to Project* attaches a reference; *Remove from Project* detaches without deleting the document globally.

**Reordering**  
- Iterations: reorder within the same status column in Storyboard; keyboard and drag supported.  
- Tasks: reorder within Tasks Tab; keyboard and drag supported.

**Empty states**  
- No areas: CTA “Create Area” or “✨ Reidentify Areas”.  
- No iterations in an area: inline card with `+ Create` and `✨ Suggest`.  
- No tasks: `✨ Plan Tasks` prominent.

**Errors & feedback**  
- Inline field errors (422/validation).  
- AI run progress with cancellable step list.  
- Toasts for success/failure; logs mirrored in Right Panel › History.

**Accessibility**  
- Trees/boards/lists navigable via arrows & type‑ahead; modals trap focus; coverage chips also have shapes/icons, not only colors.

**Keyboard shortcuts (examples)**  
- `G P` open Project selector, `G O` open Ontology tab, `A` focus AI Prompt, `R` toggle Reorder (in lists/boards), `Esc` close modals/drawers.

**Responsiveness**  
- Min width 1280px desktop primary; below 960px, Right Panel collapses to a drawer; Left Nav collapses to icon rail; Central Workspace priority.

**Performance**  
- Virtualized lists (docs, outlines, iterations, tasks).  
- Debounced search; optimistic reorder (reconcile on server ack).  
- Cache Project KB lists and doc outlines per project session.

---


## 6. TypeScript Type Definitions

### Ontology Element Text Fields

Each ontology element (class, attribute, relationship) has three text fields:

- **`label`** (required): Human-readable name for the element
  - Examples: "Person", "birthDate", "hasParent"
  - Used for: Display names, node labels in visualizations
  
- **`definition`** (optional): Formal definition from authoritative source
  - Corresponds to `skos:definition` in RDF
  - Used for: Formal semantic meaning, reference documentation
  - Example: "A person is a human being regarded as an individual."
  - Display: Emphasized (italic) in grid views, labeled "Definition" in detail panels
  
- **`description`** (optional): Additional context, usage notes, or informal explanation
  - Corresponds to `rdfs:comment` in RDF  
  - Used for: Implementation notes, usage guidelines, contextual information
  - Example: "This class represents natural persons. Use Organization for legal entities."
  - Display: Normal text in grid views, labeled "Description" in detail panels

**Display Guidelines**:
- In compact views (grid/table): Show both, with definition in italic and description in normal text
- In detailed views (panels/modals): Show both with clear section labels ("Definition" and "Description")
- In tooltips: Prefer definition, fallback to description, then to label
- In search: Search both definition and description fields

### Ontology Types (Implemented in `src/lib/api.ts`)

```typescript
// Individual ontology element types
export interface OntologyClassModel {
  uri: string
  label?: string
  definition?: string        // Formal definition (skos:definition)
  description?: string       // Additional context (rdfs:comment)
  parent_classes?: string[]  // URIs of parent classes
}

export interface OntologyAttributeModel {
  uri: string
  label?: string
  definition?: string        // Formal definition (skos:definition)
  description?: string       // Additional context (rdfs:comment)
  domain_class?: string      // URI of the class this attribute belongs to
  range_type?: string        // Data type (string, integer, date, etc.)
}

export interface OntologyRelationshipModel {
  uri: string
  label?: string
  definition?: string        // Formal definition (skos:definition)
  description?: string       // Additional context (rdfs:comment)
  domain_class?: string      // URI of source class
  range_class?: string       // URI of target class
}

// Complete ontology structure
```

**Type Design Rationale**
- All fields except `uri` are optional to handle incomplete ontology data gracefully
- URIs are used as primary identifiers and for cross-referencing between elements
- `parent_classes`, `domain_class`, `range_class` use URIs for relationships
- `SelectedElement` uses discriminated union for type-safe state management
- Arrays default to empty (`[]`) when undefined to simplify iteration logic

## 7. API ↔ UI Mapping (by feature)

> **Note:** Endpoint names reflect our earlier API outline; adjust to actual OpenAPI paths during implementation.

**Projects**
- List/Create/Edit: Top Bar Project selector & modal.  
  - `GET /projects`  
  - `POST /projects { name, domain, description }`  
  - `PUT /projects/{id}`

**Ontology**
- Create/Edit: Accessible during project creation via inline form, or (Future) via Settings page or dedicated Ontology Management page.
  - During project creation: "+ Create new ontology" link expands inline form within the Create Project modal
  - `POST /ontologies { ontology_uri, ontology_label, ontology_description }` (all fields required)
  - `PUT /ontologies/{id}` - for editing (future implementation)
- View/Export: Ontology Page (Left Nav > Ontology or Workbench > Ontology Tab).  
  - `GET /api/projects/{projectId}/ontology?format=json` → Returns `OntologyModel` (Implemented)
    - Response: `{ classes: [], attributes: [], relationships: [] }`
    - Used by: OntologyPage stats header, OntologyGrid component
  - `GET /api/projects/{projectId}/ontology?format=rdf` → Returns RDF/Turtle string (Implemented)
    - Response: Plain text RDF content
    - Used by: Export RDF button → downloads as `ontology.ttl`
  - Export functionality triggers browser download with proper MIME types:
    - JSON: `application/json`, filename: `ontology.json`
    - RDF: `text/turtle`, filename: `ontology.ttl`

**Knowledge Base**
- Lists & Attach/Detach in Compare & Cover.  
  - `GET /projects/{id}/knowledge-base` (legal/expert subsets)  
  - `POST /projects/{id}/knowledge-base/documents/{docId}` (attach)  
  - `DELETE /projects/{id}/knowledge-base/documents/{docId}` (detach)  
  - `GET /knowledge-base/documents/{docId}` (content)  
  - `GET /knowledge-base/documents/{docId}/outline`  
  - `GET /knowledge-base/documents/{docId}/coverage?project_id={id}`

**Domain Areas**
- CRUD & Reidentify (Workbench › Area Tab).  
  - `GET /projects/{id}/domain-areas`  
  - `POST /projects/{id}/domain-areas`  
  - `GET/PUT/DELETE /projects/{id}/domain-areas/{areaId}`  
  - `POST /projects/{id}/domain-areas/reidentify { key_document_id, instruction }`

**Iterations**
- Suggest & CRUD; reorder (Storyboard).  
  - `POST /projects/{id}/iterations/suggest { focused_area_id, count, user_instruction? }`  
  - `GET /projects/{id}/iterations?area_id=&status=`  
  - `POST /projects/{id}/iterations`  
  - `GET/PUT/DELETE /projects/{id}/iterations/{iterationId}`  
  - `PUT /projects/{id}/iterations/reorder { iteration_ids }`

**Tasks**
- Plan & CRUD; reorder (Workbench › Tasks Tab).  
  - `POST /projects/{id}/iterations/{iterationId}/tasks/plan { user_instruction? }`  
  - `GET/POST /projects/{id}/iterations/{iterationId}/tasks`  
  - `PUT/DELETE /projects/{id}/iterations/{iterationId}/tasks/{taskId}`  
  - `PUT /projects/{id}/iterations/{iterationId}/tasks/reorder { task_ids }`

**Execution (Operations)**
- Prepare/Apply workflow (Operations Modal).  
  - `POST /projects/{id}/iterations/{iterationId}/prepare` - generates operations, cached in frontend store
  - `POST /projects/{id}/iterations/{iterationId}/apply { operations[] }` - executes operations and updates ontology
  - `POST /projects/{id}/iterations/{iterationId}/cancel` - cancels prepared iteration and reverts to planned state
  - Operations displayed in modal for review before apply; no server-side filtering/rejection

**Links from Documents**
- *Add to Area…* linkage persisted in project scope (implementation choice: store as area metadata or a dedicated linkage entity).  
  - `POST /projects/{id}/areas/{areaId}/doc-links { document_id, fragment_id, note? }`

---

## 7. User Stories → Concrete UI Flows (acceptance criteria)

1) **Create a new design project**  
   - Top Bar › Project selector › **+ Create**.
   - Fill in: Name (required), select Ontology from dropdown (lists all loaded ontologies with label and URI), Domain Name (optional), Domain Description (optional).
   - Ontology dropdown shows: "{label} ({uri})" for each available ontology.
   - **Create new ontology inline**: Click "+ Create new ontology" link below the dropdown to expand an inline form.
     - Inline form requests: URI, Label, Description (all required).
     - Click "Create Ontology" to save; new ontology appears in the dropdown automatically.
     - Success message shows; user can then select the newly created ontology.
     - Click "✕ Cancel" to collapse the inline form and return to dropdown selection.
   - After create, the Top Bar displays the selected ontology name as a read-only badge.
   - Storyboard opens with empty lanes; Compare & Cover shows empty Project KB.

2) **Edit an existing design project**  
   - Project selector › **Edit**; change Name, Domain Name, or Domain Description; Save.
   - Note: Ontology cannot be changed after project creation.
   - All modes refresh to show updated names/descriptions.

3) **Load an existing project**  
   - Project selector › choose project; Storyboard/Workbench/Compare & Cover load that context.
   - Top Bar displays the project's associated ontology name as a read-only badge.

4) **Edit project knowledge base**  
   - Compare & Cover › Project KB tab.  
   - **Add** document from Global KB; **Remove** detaches.  
   - Reading content is immediate in the Document Viewer.

5) **Manually edit knowledge areas**  
   - Workbench › Area Tab.  
   - Add/Edit/Delete via form; Save updates Left Tree and Storyboard lanes.

6) **Reidentify knowledge areas with AI**  
   - Workbench › Area Tab › **Reidentify ✨** (slide‑over).  
   - Choose **Key Document** (must be in Project KB) + Instruction; Preview; Apply; lanes update.

7) **Suggest iterations for a domain area**  
   - Storyboard › **✨ Suggest Iterations**.  
   - Select area, K, instruction; Preview; Insert to **Suggested**; cards appear in Suggested column.

8) **Plan tasks for a suggested iteration**  
    - Storyboard › Suggested column › **Plan Tasks ✨** on iteration card.
    - Optional instruction; Preview; Insert; iteration moves to **Planned** column with tasks.

9) **View tasks for a planned iteration**  
    - Storyboard › Planned column › **View Tasks** on iteration card.
    - Modal opens showing all tasks (planned, generating, completed) with color-coded status.

10) **Manually edit iterations**  
    - Storyboard cards: Edit/Delete; reorder within status column; open in Workbench for full edit.

11) **Edit tasks of an iteration**  
    - Workbench › Tasks Tab: Add/Edit/Delete tasks; reorder with drag/keyboard.

12) **Prepare an iteration (generate operations)**  
    - Storyboard › Planned column › **Prepare ▶** on iteration card (or Workbench › Iteration Tab).
    - Progress indicator; operations generated and cached; iteration moves to **Prepared** column.

13) **Review prepared operations**  
    - Storyboard › Prepared column › **View Operations** on iteration card.
    - Modal opens showing detailed operation list with all fields (URI, label, definition, target-specific details).
    - Each operation shows color-coded badge: Add (green), Remove (red), Modify (blue).

14) **Execute operations (apply iteration)**  
    - Operations Modal › **Apply Changes** (or Storyboard › Prepared column › **Apply Changes** button).
    - Operations executed; iteration moves to **Completed** column; ontology updated.

15) **See ontology after executing operations**  
    - Switch to Ontology Tab; highlight new/changed elements.
    - *Implementation note: Change highlighting pending; current implementation shows complete ontology state.*

16) **See an existing ontology (any time)**  
    - Left Nav › **Ontology** (or Workbench › Ontology Tab) shows current structure and allows export.
    - **✅ IMPLEMENTED**: Full ontology browsing with:
      - Three-panel semantic grid (Classes | Attributes | Relationships)
      - Statistics header showing element counts
      - Bidirectional filtering (select class → see its attributes/relationships, or vice versa)
      - Clickable class references for navigation (parent classes, domain/range classes)
      - Auto-scroll to selected elements in long lists
      - Search across all panels simultaneously
      - Export to JSON or RDF/Turtle format
      - Smart label display (URIs hidden, human-readable labels shown)
    - **Components**: `OntologyPage.tsx`, `OntologyGrid.tsx`
    - **API**: `GET /api/projects/{projectId}/ontology?format=json|rdf`

19) **Read knowledge base document**  
    - Compare & Cover › select document in Project KB; read in viewer with outline.

20) **See coverage of documents by ontology**  
    - Coverage toggle **ON**; overlay chips; Right Panel lists matched ontology; actions available.

---

## 8. Implementation Progress & Phases

### Ontology Tab Implementation (4.6)

**Overall Approach**: Iterative development with user feedback at each phase

**Phase 1: TypeScript Types & API Foundation** ✅ COMPLETE
- Added complete ontology type definitions in `src/lib/api.ts`
- Created type-safe interfaces: `OntologyClassModel`, `OntologyAttributeModel`, `OntologyRelationshipModel`, `OntologyModel`
- Updated API client to return strongly-typed data (no `any` types)
- Implemented dual-format export (JSON and RDF/Turtle)
- Added proper type handling for `getProjectOntology` with format parameter

**Phase 2: Grid View with Semantic Filtering** ✅ COMPLETE
- Created `OntologyGrid.tsx` component with three-panel layout
- Implemented semantic filtering logic:
  - Class selection filters attributes (by domain_class) and relationships (by domain_class or range_class)
  - Attribute selection highlights owning class (domain_class)
  - Relationship selection highlights connected classes (domain_class and range_class)
- Added bidirectional navigation:
  - Clickable parent class references in Classes panel
  - Clickable domain class references in Attributes panel
  - Clickable domain/range class references in Relationships panel
- Implemented auto-scroll functionality:
  - Used `useRef` to track DOM elements for each row
  - Added `useEffect` to trigger scroll on selection change
  - Configured `scrollIntoView` with smooth behavior and center alignment
- **Hierarchical Tree View** (Phase 2b):
  - Built recursive tree structure from parent_classes relationships
  - Added expand/collapse UI with ▶/▼ icons
  - Implemented smart auto-expand:
    - Search auto-expands ancestors of matching classes
    - Semantic filter auto-expands related class ancestors
    - Navigation auto-expands and scrolls to target class
  - Added manual controls (Expand All / Collapse All buttons)
  - Visual indicators: indentation (16px/level), child count badges
  - Cycle detection for circular references
  - Multi-parent support (class shown under all parents)
- UI improvements:
  - Removed URI clutter, showing only human-readable labels
  - Smart label resolution with fallbacks (label → URI segment → full URI)
  - Color-coded panels with consistent interaction patterns
  - Contextual empty states for filtered results
- Enhanced `OntologyPage.tsx`:
  - Added statistics header with element counts
  - Integrated search functionality across all panels
  - Added export buttons with proper download handling

**Phase 3: Reserved for Future Work** ⏳ PENDING
- Advanced filtering UI (by type, by parent hierarchy, by domain/range)
- Multi-select and bulk operations
- Column customization and sorting

**Phase 4: Graph Visualization** ⏳ PENDING
- Install and integrate React Flow library
- Transform ontology data to node/edge format
- Implement interactive graph with zoom, pan, and layout
- Sync selection between grid and graph views

**Phase 5: Right Panel Integration** ⏳ PENDING
- Click element → show full details in Right Panel
- Display complete metadata (URI, label, description, all properties)
- Add inline editing capabilities
- Show element history and references

**Phase 6: Change Highlighting** ⏳ PENDING
- Snapshot ontology state before Apply operations
- Compare current state with snapshot after Apply
- Highlight added (+), modified (~), and deleted (−) elements
- Color-coded markers in grid and graph views

**Phase 7: Polish & Optimization** ⏳ PENDING
- Performance optimization for large ontologies (virtualization)
- Accessibility improvements (ARIA labels, keyboard navigation)
- Responsive design refinements
- Loading state improvements
- Error handling enhancements

### Key Design Decisions

**Architecture Clarity**
- Ontology is a **separate page** (Left Nav › Ontology), not a Workbench tab
- Maintains consistency with Storyboard and Compare & Cover as top-level modes
- Direct navigation without requiring project/iteration context

**Semantic Browsing Philosophy**
- Bidirectional relationships: classes ↔ attributes ↔ relationships
- Context-aware filtering rather than global search-only approach
- Click-through navigation for exploring ontology structure
- Visual feedback for all interactive elements

**User Experience Priorities**
1. **Discoverability**: Make relationships between elements obvious and explorable
2. **Readability**: Hide technical URIs, show human-friendly labels
3. **Navigation**: Support both top-down (class → attributes) and bottom-up (attribute → class) exploration
4. **Feedback**: Auto-scroll ensures navigation targets are always visible

**Technical Stack Choices**
- **TanStack Query**: Handles caching, loading, error states automatically
- **React hooks**: useState for selection, useMemo for filtered lists, useRef for DOM access
- **Tailwind CSS**: Utility-first styling with custom color coding
- **TypeScript**: Strict typing prevents runtime errors, improves developer experience

## 9. QA Checklists & Non‑functional

**Functional QA**
- Mode switching preserves context across all features.  
- Prepared Operations drawer always opens post‑Prepare or shows clear error.  
- Coverage overlay renders chips for **every visible** paragraph/section with legend.

**Accessibility QA**
- Keyboard traverse for trees, boards, lists; modals trap focus; tooltips/readable labels on chips.

**Performance QA**
- Virtualization verified on large data sets; optimistic reorder reconciles correctly; no blocking UI during AI jobs.

**Internationalization**
- UI strings centralised; number/date formats localised; avoid text truncation in chips/cards.

**Security & Roles (extensible)**
- Role‑aware default modes (Analyst → Compare & Cover; Designer → Workbench; Lead/PM → Storyboard).  
- All mutating actions gated behind project write permissions (future auth layer).

---

## 10. Glossary
- **Area**: Domain area (knowledge area) within a project.
- **Iteration**: Planned work unit scoped to a single Area. Workflow states:
  - **Suggested**: No tasks planned yet (planned_tasks_count = 0)
  - **Planned**: Tasks have been planned (planned_tasks_count > 0)
  - **Prepared**: Operations generated and cached, ready for review
  - **Completed**: Operations applied, iteration completed
- **Task**: Action item forming a plan inside an Iteration. States: `planned`, `generating`, `completed`.
- **Prepared Operations**: Materialized ontology edit operations cached and awaiting user review/approval.
- **Operations Modal**: Dialog showing detailed operation information with Apply/Cancel actions.
- **Project KB**: The subset of documents attached to the project (Legal/Expert).  
- **Global KB**: All available documents system‑wide.
- **Key Document**: A selected **Project KB** document used to guide AI reidentification of areas.
- **Ontology**: Formal representation of domain knowledge with classes, attributes, and relationships.
  - **Class**: A category or type of thing (e.g., Person, Organization)
  - **Attribute**: A property or characteristic of a class (e.g., name, age, founded_date)
  - **Relationship**: A connection between two classes (e.g., knows, worksAt, owns)
- **Semantic Filtering**: Context-aware filtering that shows related ontology elements based on current selection.
- **Bidirectional Navigation**: Ability to navigate from classes to attributes/relationships and vice versa.
- **Auto-scroll**: Automatic scrolling to bring selected elements into view when navigating.
- **OntologyModel**: TypeScript type representing complete ontology structure with classes, attributes, and relationships arrays.

---

**End of Consolidated Frontend Specification (vFinal)**

