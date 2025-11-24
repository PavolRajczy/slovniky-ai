# Ontology Changes Highlighting Implementation

## Overview
This implementation allows users to visually track and compare changes made to the ontology after applying iteration operations. Changes are highlighted across all three ontology views (Grid, Graph, and Force) with visual indicators distinguishing between created, modified, and deleted elements.

## Key Components

### 1. Change Tracking Store (`ontologyChangesStore.ts`)
A Zustand store that manages the state of ontology changes:
- **Types of changes tracked:**
  - Classes (created/modified/deleted)
  - Attributes (created/modified/deleted)
  - Relationships (created/modified/deleted)
  - Inheritance relationships (created/modified/deleted)

- **Key functions:**
  - `recordChanges(iterationId, operations)`: Records changes from applied operations
  - `clearChanges()`: Clears all tracked changes
  - `toggleShowChanges()`: Toggles visibility of change highlights
  - `setShowChanges(show)`: Explicitly sets change visibility

### 2. Integration Points

#### Application of Changes
When iterations are applied in:
- `WorkbenchPage.tsx` (2 locations)
- `StoryboardPage.tsx`

The operations are recorded immediately after successful application:
```typescript
await api.applyIteration(projectId, iterationId, cachedOps)
if (cachedOps && cachedOps.length > 0) {
  changesStore.recordChanges(iterationId, cachedOps)
}
await qc.invalidateQueries({ queryKey: ['ontology', projectId] })
```

#### Ontology Page UI
`OntologyPage.tsx` now includes:
- **Changes visibility toggle**: Checkbox to show/hide change highlights
  - When checked: Changes are highlighted in all views
  - When unchecked: Ontology is displayed without highlighting
  - User can toggle on/off as many times as needed
- **Change statistics**: Visual badges always visible showing count of created (+), modified (~), and deleted (-) elements
  - Displayed even when highlighting is turned off
  - Provides persistent visibility of what changed
- **Changes prop**: Passes change information to all three view components (only when highlighting is enabled)

### 3. Visual Indicators

#### Grid View (`OntologyGrid.tsx`)
- **Row highlighting**: Colored left border on changed rows
  - Green: Created elements
  - Yellow: Modified elements
  - Red: Deleted elements (with reduced opacity)
- **Badge labels**: "NEW", "MODIFIED", "DELETED" badges next to element names
- **Border colors**: Left border colored according to change type

#### Graph View (`OntologyGraph.tsx`)
- **Node styling**:
  - Colored borders on nodes (green/yellow/red)
  - Background color tint on class header
  - Badge in node header showing change type
  - Reduced opacity for deleted elements
- **Edge styling**:
  - Colored edges (green/yellow/red) for changed relationships
  - Increased thickness for visibility
  - Animation on newly created edges
  - Reduced opacity for deleted edges

#### Force View (`OntologyForceGraph.tsx` + `OntologyCanvas.ts`)
- **Node rendering**:
  - Colored halo around changed nodes (thick colored ring)
  - Reduced opacity for deleted nodes
  - Colors: green (created), yellow (modified), red (deleted)
- **Edge rendering**:
  - Colored and thickened lines for changed relationships
  - Reduced opacity for deleted relationships
  - Maintains distinction between inheritance (dashed) and relationships (solid)

### 4. Color Scheme
Consistent across all views:
- **Created**: Green (#22c55e / green-500)
- **Modified**: Yellow (#eab308 / yellow-500)
- **Deleted**: Red (#ef4444 / red-500)

### 5. Type System Updates

Extended type definitions in:
- `ontologyGraphLayout.ts`: Added `changeType` to `GraphNode.data` and `GraphEdge.data`
- `OntologyCanvas.ts`: Added `changeType` to `D3Node` and `D3Link` interfaces

## Usage Flow

1. User prepares an iteration (operations are shown in drawer)
2. User applies the iteration
3. System records the operations as changes
4. Ontology view is refreshed with new data
5. Changes are automatically highlighted in all views with a panel showing change counts
6. User can:
   - Toggle highlighting on/off using the checkbox (changes remain tracked)
   - See change counts at all times (even when highlighting is off)
   - Switch between views while maintaining change visibility state
   - Changes persist across sessions until a new iteration is applied

## Benefits

1. **Visual Feedback**: Users can immediately see what changed in the ontology
2. **Multiple Views**: Changes are consistently highlighted across all visualization modes
3. **Persistence**: Changes remain tracked until a new iteration is applied
4. **Flexible Control**: Toggle highlighting on/off without losing track of changes
5. **Always Visible Stats**: Change counts are always visible, even when highlighting is off
6. **Non-Destructive**: Cannot accidentally lose change information - it persists until new changes occur
7. **Comprehensive**: Covers all ontology element types (classes, attributes, relationships, inheritance)

## Future Enhancements

Potential improvements that could be added:
- History of multiple iterations (track multiple sets of changes)
- Diff view comparing two specific ontology versions
- Export change report
- Filter ontology to show only changed elements
- Undo/redo support with change tracking
- Manual clear button (if users request it)
