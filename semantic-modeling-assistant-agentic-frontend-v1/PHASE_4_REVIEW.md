# Phase 4 Review: Graph Visualization
**Date**: October 11, 2025  
**Status**: Ready to Implement

## Overview

Phase 4 focuses on adding interactive graph visualization to the Ontology page using React Flow. This will provide a visual, navigable representation of the ontology hierarchy alongside the existing grid view.

---

## Current State Analysis

### ✅ Completed (Phases 1-2)

**Phase 1: TypeScript Types & API Foundation**
- Complete ontology type definitions (`OntologyClassModel`, `OntologyAttributeModel`, `OntologyRelationshipModel`)
- Type-safe API client with dual-format export (JSON/RDF)
- Fully implemented

**Phase 2: Grid View with Semantic Filtering**
- Three-panel layout (Classes | Attributes | Relationships)
- Hierarchical tree view for classes with expand/collapse
- Smart auto-expand on search/filter/navigation
- Bidirectional semantic filtering
- Auto-scroll navigation
- Search across all panels
- Export functionality
- **Status**: ✅ Complete with all refinements

### 🔍 Recent Independent Changes (API v2.1)

**Breaking Changes Detected:**
1. **Iteration Status Values**:
   - `'finished'` → `'completed'`
   - These changes don't affect ontology visualization

2. **Task Status Values**:
   - `'in_progress'` → `'generating'`
   - `'finished'` → `'completed'`
   - These changes don't affect ontology visualization

3. **API Endpoints**:
   - New: `POST /iterations/{iterationId}/cancel`
   - No impact on ontology endpoints

4. **Project & Ontology Association**:
   - Projects now must select an ontology during creation
   - Ontology cannot be changed after project creation
   - Ontology displayed as read-only badge in Top Bar
   - **Impact**: This reinforces the importance of the Ontology page as a viewing tool

**Impact Assessment for Phase 4**: ✅ **No conflicts** - All changes are in Storyboard/Workbench domains, not affecting Ontology visualization.

---

## Phase 4 Specification

### Goals

1. **Visual Hierarchy**: Show ontology structure as an interactive graph
2. **Bidirectional Sync**: Keep grid and graph selections synchronized
3. **Interactive Exploration**: Support zoom, pan, drag nodes
4. **Automatic Layout**: Intelligently position nodes based on relationships
5. **Consistent UX**: Maintain same color coding and interaction patterns as grid

### Technical Requirements

#### 1. **React Flow Integration**

**Library**: `@xyflow/react` (formerly `reactflow`)
- Latest version: `^12.0.0` (as of Oct 2025)
- Includes TypeScript types
- Supports custom nodes and edges
- Built-in minimap, controls, and background options

**Installation**:
```bash
npm install @xyflow/react
```

**Dependencies**: None required beyond what's already in `package.json`

#### 2. **Data Transformation**

Transform `OntologyModel` to React Flow format:

```typescript
interface OntologyGraphData {
  nodes: Node[]
  edges: Edge[]
}

// Node types
type OntologyNode = 
  | { id: string; type: 'class'; data: OntologyClassModel; position: { x: number; y: number } }
  | { id: string; type: 'attribute'; data: OntologyAttributeModel; position: { x: number; y: number } }
  | { id: string; type: 'relationship'; data: OntologyRelationshipModel; position: { x: number; y: number } }

// Edge types
type OntologyEdge =
  | { id: string; source: string; target: string; type: 'inheritance'; label?: string } // parent_classes
  | { id: string; source: string; target: string; type: 'domain'; label?: string }      // attribute → class
  | { id: string; source: string; target: string; type: 'relationship'; label?: string } // relationship domain/range
```

**Transformation Logic**:
1. **Classes → Nodes**: Each class becomes a node
2. **Attributes → Nodes**: Each attribute becomes a node (optional, can be shown as properties)
3. **Relationships → Nodes or Edges**: Can be represented as:
   - **Option A**: Nodes with edges to domain/range classes
   - **Option B**: Direct edges between domain and range classes (simpler)
4. **parent_classes → Edges**: Inheritance relationships
5. **domain_class → Edges**: Attribute-to-class connections

#### 3. **Layout Algorithm**

**Recommended**: Dagre layout (hierarchical)
- `dagre` library for automatic node positioning
- Install: `npm install dagre @types/dagre`
- Top-down hierarchy for class inheritance
- Left-to-right or clustered for attributes/relationships

**Alternative**: ELK (Eclipse Layout Kernel)
- More sophisticated
- Supports multiple layout types
- Heavier dependency

**Initial Layout Strategy**:
- Classes arranged hierarchically (top = root classes, down = children)
- Attributes positioned around their domain classes
- Relationships as connecting edges

#### 4. **Visual Design**

**Node Styling**:
- **Class Nodes**: Blue border, white background (matches grid)
  - Shows: label (large), description (truncated)
  - Expandable: click to show attributes/relationships
- **Attribute Nodes**: Green border, light green background
  - Shows: label, domain class (small text)
- **Relationship Nodes/Edges**: Purple
  - Shows: label, domain → range

**Edge Styling**:
- **Inheritance** (parent_classes): Solid blue arrow, thicker
- **Domain** (attribute → class): Dashed green arrow
- **Relationship**: Solid purple arrow with label

**Interactive States**:
- **Selected**: Highlight node + connected edges in bright color
- **Hover**: Subtle shadow, show tooltip with full description
- **Related**: When class selected, dim unrelated nodes/edges

**Color Coding** (consistent with grid):
- Classes: Blue theme
- Attributes: Green theme
- Relationships: Purple theme

#### 5. **Interaction Features**

**Essential**:
- ✅ Click node → select in grid (sync)
- ✅ Click in grid → highlight in graph (sync)
- ✅ Zoom in/out (mouse wheel, controls)
- ✅ Pan (drag background)
- ✅ Drag nodes to reposition
- ✅ Double-click node → expand/collapse attributes/relationships

**Advanced** (Phase 5+):
- Right-click context menu (edit, delete, add relationship)
- Drag-and-drop to create relationships
- Minimap for navigation
- Search highlighting in graph
- Filter by type (show only classes, only attributes, etc.)

#### 6. **Layout & UI Structure**

**Selected Approach: Switchable Views (Tabs)**
```
┌────────────────────────────────────────────────────────┐
│ Search | Export JSON | Export RDF                      │
├────────────────────────────────────────────────────────┤
│ [Tab: Grid View ✓] [Tab: Graph View]                  │
├────────────────────────────────────────────────────────┤
│ Content area (full width)                              │
│ - Grid View: Three-panel semantic grid                │
│ - Graph View: Interactive React Flow visualization    │
└────────────────────────────────────────────────────────┘
```

**Benefits**:
- ✅ Full screen width for both views (better use of space)
- ✅ Clean, uncluttered interface
- ✅ Familiar tab pattern (low learning curve)
- ✅ Works well on typical screen sizes (1920x1080 or smaller)
- ✅ Selection state preserved when switching between views

**Interaction**:
1. User selects element in Grid View
2. User switches to Graph View tab
3. Graph View shows with same element selected/highlighted
4. Vice versa: select in Graph, switch to Grid, selection preserved

**Tab State Management**:
- Active tab stored in component state (`useState`)
- Selection state (`selectedElement`) shared between both views
- Search query applies to both views
- Export buttons work regardless of active tab

**Alternative Considered (Rejected)**:
- **Side-by-Side**: Rejected due to screen space constraints
  - Would require 50% width each
  - Grid needs ~800px minimum for three panels
  - Graph needs ~600px minimum for clarity
  - Total: 1400px minimum, too cramped on 1920px screens
- **Stacked**: Rejected due to vertical space issues
  - Would split vertical space inefficiently
  - Scrolling becomes cumbersome

---

## Implementation Plan

### Step 1: Install Dependencies

```bash
npm install @xyflow/react dagre
npm install --save-dev @types/dagre
```

### Step 2: Create Graph Components

**File Structure**:
```
src/components/
├── OntologyGraph.tsx          # Main graph component
├── OntologyGraphNode.tsx      # Custom node components
└── OntologyGraphLayout.ts     # Layout algorithms
```

**Components**:
1. **OntologyGraph.tsx**: React Flow wrapper with custom nodes/edges
2. **OntologyGraphNode.tsx**: Custom node rendering (class/attribute/relationship)
3. **OntologyGraphLayout.ts**: Dagre integration for automatic layout

### Step 3: Data Transformation

Create utility function:
```typescript
// src/lib/ontologyGraph.ts
export function transformOntologyToGraph(ontology: OntologyModel): { nodes: Node[], edges: Edge[] }
```

### Step 4: Update OntologyPage

1. Add tab switcher UI (Grid View | Graph View)
2. Conditionally render `<OntologyGrid>` or `<OntologyGraph>` based on active tab
3. Share selection state between both views
4. Ensure search query filters both views
5. Keep export buttons accessible regardless of active tab

**Implementation**:
```typescript
const [activeView, setActiveView] = useState<'grid' | 'graph'>('grid')
const [selectedElement, setSelectedElement] = useState<SelectedElement>(null)

// Render
{activeView === 'grid' ? (
  <OntologyGrid 
    ontology={ontology}
    searchQuery={searchQuery}
    selectedElement={selectedElement}
    onElementSelect={setSelectedElement}
  />
) : (
  <OntologyGraph 
    ontology={ontology}
    searchQuery={searchQuery}
    selectedElement={selectedElement}
    onElementSelect={setSelectedElement}
  />
)}
```

### Step 5: Styling & Polish

1. Custom node styles matching grid colors
2. Smooth transitions on selection
3. Responsive layout adjustments

### Step 6: Testing

1. Test with small ontologies (5-10 classes)
2. Test with medium ontologies (50+ classes)
3. Test selection sync in both directions
4. Test zoom/pan performance
5. Test layout quality (no overlaps, readable)

---

## Technical Decisions

### Decision 1: Representation of Attributes/Relationships

**Options**:
- **A**: Show all as separate nodes (comprehensive but cluttered)
- **B**: Show only classes as nodes, attributes/relationships as edges (cleaner)
- **C**: Show classes + collapsible attributes (hybrid)

**Recommendation**: **Option C (Hybrid)**
- Start with classes only (cleaner)
- Click class → expand to show attributes/relationships as connected nodes
- Matches hierarchical tree collapse/expand UX from grid

### Decision 2: Layout Algorithm

**Options**:
- **A**: Dagre (hierarchical, proven, lighter)
- **B**: ELK (more sophisticated, heavier)
- **C**: Force-directed (d3-force, organic but unpredictable)

**Recommendation**: **Option A (Dagre)**
- Perfect for hierarchical ontologies
- Lighter dependency
- Good balance of simplicity and quality

### Decision 3: Grid-Graph Layout

**Decision**: **Switchable Tabs (Updated from Side-by-Side)**

**Rationale**:
- Typical screens (1920x1080 or smaller) don't have enough width for side-by-side
- Grid needs ~800px minimum for readable three-panel layout
- Graph needs ~600px minimum for clarity
- Side-by-side would require ~1400px, leaving no margins

**Benefits of Tabs**:
- Full screen width for each view (better space utilization)
- No cramped panels or tiny text
- Clean, simple UI
- Familiar pattern (users understand tabs)
- Selection state preserved when switching

**Implementation**:
- State management: `useState<'grid' | 'graph'>('grid')`
- Shared selection: Both views use same `selectedElement` state
- Search applies to both views
- Export buttons always accessible

---

## Dependencies to Add

```json
{
  "dependencies": {
    "@xyflow/react": "^12.0.0",
    "dagre": "^0.8.5"
  },
  "devDependencies": {
    "@types/dagre": "^0.7.52"
  }
}
```

**Total Size**: ~200KB (minified + gzipped)
**Impact**: Minimal - modern bundlers will tree-shake unused features

---

## Compatibility Check

### ✅ No Conflicts Detected

1. **API Changes**: API v2.1 changes don't affect ontology endpoints
2. **Project Structure**: No new components conflict with existing
3. **TypeScript Types**: OntologyModel already defined, ready to use
4. **State Management**: Selection sync can use existing useState patterns
5. **Styling**: Tailwind CSS already in use, compatible with React Flow

### 🔍 Considerations

1. **Performance**: React Flow handles up to 1000+ nodes well
   - Current ontologies likely < 100 elements
   - If needed, can add virtualization later

2. **Right Panel**: Specification mentions future integration
   - Phase 4: Build graph, sync with grid
   - Phase 5: Add Right Panel details view
   - No conflict, complementary features

3. **Change Highlighting**: Phase 6 feature
   - Graph nodes can be styled to show +/~/− markers
   - Consistent with grid highlighting
   - No conflict, additive feature

---

## Success Criteria

### Minimum Viable (Phase 4 Complete)

- ✅ Tab switcher between Grid View and Graph View
- ✅ Graph displays ontology classes with inheritance hierarchy
- ✅ Nodes styled with consistent colors (blue for classes)
- ✅ Selection state preserved when switching between tabs
- ✅ Click node in graph → switches to grid with node selected (optional UX)
- ✅ Click class in grid → switches to graph with class highlighted (optional UX)
- ✅ **OR** Selection syncs silently: select in one view, switch tabs, see it selected in other
- ✅ Zoom in/out works smoothly
- ✅ Pan by dragging background
- ✅ Automatic layout with no overlapping nodes
- ✅ Search filters both grid and graph views
- ✅ Export functionality works from both tabs

### Nice-to-Have (Future Phases)

- Minimap for large ontologies
- Expand/collapse to show attributes/relationships
- Filter graph by element type
- Search highlighting in graph
- Drag nodes to save custom layouts (localStorage)

---

## Estimated Effort

**Development Time**: 2-3 days
- Day 1: Install deps, create components, basic rendering
- Day 2: Layout algorithm, data transformation, custom styling
- Day 3: Selection sync, polish, testing

**Complexity**: Medium
- React Flow is well-documented
- Dagre integration is straightforward
- Main challenge: Balancing layout quality vs. performance

---

## Recommendation

**✅ Proceed with Phase 4 Implementation**

**Why Now**:
1. No conflicts with recent API v2.1 changes
2. Grid view is stable and complete (Phase 2)
3. Natural progression: Table view → Tree view → Graph view
4. Users benefit from visual exploration alongside tabular data

**Implementation Order**:
1. Install dependencies
2. Build basic graph component (classes only, hierarchical layout)
3. Add tab switcher to OntologyPage
4. Implement selection state sharing between views
5. Refine styling and interactions
6. Test with real ontology data
7. Polish and optimize

**Tab Switching Behavior Options**:
- **Option A**: Selection syncs silently (select in grid, switch tab, see it in graph)
- **Option B**: Selecting switches tab automatically (select in grid → jumps to graph view)
- **Recommendation**: Start with **Option A** (silent sync), less jarring for users

**Next Steps After Phase 4**:
- Phase 5: Right Panel integration (click → show full details)
- Phase 6: Change highlighting (post-Apply visualization)
- Phase 7: Performance optimization and accessibility

---

## Open Questions

1. **Tab Switch on Selection**: Should selecting an element automatically switch tabs?
   - **Option A**: Silent sync (select in grid, stay in grid, switch tab manually to see in graph)
   - **Option B**: Auto-switch (select in grid → automatically jumps to graph view)
   - **Recommendation**: **Option A (Silent sync)** - Less jarring, users control when they switch

2. **Default Tab**: Which view should be active by default?
   - **Recommendation**: **Grid View** - Users are already familiar with it from Phase 2

3. **Layout Persistence**: Should we save user's custom node positions?
   - **Recommendation**: Start without, add in Phase 7 if requested

4. **Attributes/Relationships Display**: Show as nodes or edges?
   - **Recommendation**: Start with edges only (cleaner), add expandable nodes in Phase 5

5. **Graph Size Limits**: What's the expected maximum ontology size?
   - **Recommendation**: Optimize for < 100 elements, add virtualization if needed

6. **Export Graph**: Should graph layout be exportable (PNG/SVG)?
   - **Recommendation**: Add in Phase 7 (polish phase)

7. **Tab Persistence**: Remember user's last active tab across page reloads?
   - **Recommendation**: Start without, can add localStorage persistence later if needed

---

## Conclusion

Phase 4 is **ready for implementation** with no blockers from recent changes. The specification is clear, dependencies are minimal, and the feature aligns well with the completed Phase 2 grid view.

**Final Approach**: Implement **Switchable Tabs (Grid View / Graph View)** with **Dagre hierarchical layout** and **hybrid attribute/relationship representation** (collapsed by default, edges only initially).

**Key Benefits**:
- ✅ Works perfectly on typical screen sizes (1920x1080 and smaller)
- ✅ Full width for each view = better readability
- ✅ Clean, familiar tab interface
- ✅ Selection state preserved between views
- ✅ Search and export work across both tabs

**Ready to start implementation!**
