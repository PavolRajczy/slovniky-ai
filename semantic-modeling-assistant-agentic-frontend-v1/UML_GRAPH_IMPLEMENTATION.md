# UML-Style Graph Visualization

## Implementation Overview

The graph visualization now displays ontology classes in **UML-style** with attributes listed inside each class box.

## Visual Design

### Class Nodes (UML-Style)

Each class is displayed as a structured box with three sections:

```
┌─────────────────────────────────┐
│      Silniční vozidlo           │ ← Header (class name)
├─────────────────────────────────┤
│ • účel použití: string          │ ← Attributes section
│ • je určeno k provozu: string   │   (max 5 shown)
│ • povaha pohonu: string          │
├─────────────────────────────────┤
│ 1 rel  1 sub                    │ ← Footer (stats)
└─────────────────────────────────┘
```

**Sections:**

1. **Header (Gray background)**
   - Class name in bold
   - Centered text

2. **Attributes Section (White background)**
   - Lists attributes belonging to this class
   - Format: `• attribute_name: type`
   - Shows max 5 attributes
   - If more than 5: "... and X more" at bottom
   - Tooltip shows full description on hover

3. **Footer (Gray background)**
   - Relationship count (outgoing relationships)
   - Subclass count (direct children)

### Edges (Arrows)

Two types of edges:

1. **Inheritance Edges (Gray)**
   - Color: `#94a3b8` (gray)
   - Stroke width: 2px
   - Represents `parent_classes` relationships
   - Direction: Parent → Child
   - Example: `Vozidlo → Silniční vozidlo`

2. **Relationship Edges (Blue with Labels)**
   - Color: `#3b82f6` (blue)
   - Stroke width: 2px
   - Has a **label** showing the relationship name
   - Direction: Domain class → Range class
   - Example: `Silniční vozidlo → Kategorie vozidla` with label "má kategorii silničního vozidla"

## Node Sizing

- **Width**: 300px (min 250px, max 350px)
- **Height**: Dynamically calculated based on number of attributes
- **Layout spacing**:
  - Node separation: 100px
  - Rank separation: 150px
  - Margins: 50px

## Expected Output for Your Ontology

Based on `ontology-8b0b727e-80bd-4a19-b76b-ede8478c0698.ttl`:

### Nodes: 23 classes

Examples:
- **Vozidlo** - 1 rel, 4 sub (no attributes)
- **Silniční vozidlo** - 3 attributes, 1 rel, 1 sub
- **Zvláštní vozidlo** - 2 attributes, 1 rel
- **Přípojné vozidlo** - 3 attributes
- **Kategorie vozidla** - 12 sub (no attributes)

### Edges: 24 total

- **16 Inheritance edges** (gray)
  - Vozidlo → Silniční vozidlo
  - Vozidlo → Zvláštní vozidlo
  - Vozidlo → Přípojné vozidlo
  - Kategorie vozidla → Kategorie L, M, N, O, T, C, R, S, Z (9 edges)
  - Technický prvek → Systém, Konstrukční část, Samostatný celek (3 edges)
  - And more...

- **8 Relationship edges** (blue with labels)
  1. Silniční vozidlo → Kategorie vozidla ("má kategorii silničního vozidla")
  2. Zvláštní vozidlo → Kategorie vozidla ("má kategorii zvláštního vozidla")
  3. Vozidlo → Technický prvek vozidla ("je vybaveno technickým prvkem vozidla")
  4. Typ technického prvku → Technický prvek ("je typem")
  5. Typ technického prvku → Schválení typu ("má schválení")
  6. Schválení typu → Omezení použití ("má omezení použití")
  7. Omezení použití → Kategorie vozidla ("omezuje použití pro kategorii")
  8. Technický prvek → Kategorie vozidla ("je určen pro kategorii")

## Debugging

The implementation includes console logging:

```javascript
console.log('🔍 Graph Data:', {
  nodeCount: nodes.length,
  edgeCount: edges.length,
  inheritanceEdges: edges.filter(e => e.type === 'inheritance').length,
  relationshipEdges: edges.filter(e => e.type === 'default').length,
  sampleEdges: edges.slice(0, 3),
});
```

Open browser DevTools (F12) → Console to see:
- Total number of nodes generated
- Total number of edges generated
- Breakdown by edge type
- Sample edge data

## Troubleshooting

### If edges are not visible:

1. **Check console** - Look for the debug output showing edge counts
2. **Use "Fit View"** - Click the fit view button in graph controls (bottom-left)
3. **Zoom out** - Edges might be outside viewport
4. **Check edge data** - Console will show sample edges with source/target URIs
5. **Verify data** - Make sure relationships have `domain_class` and `range_class` properties

### If attributes are not showing:

1. **Check console** - Should show attribute counts
2. **Verify data** - Attributes must have `domain_class` property matching class URI
3. **Check hovering** - Tooltip shows full attribute description on hover

## Differences from Previous Version

| Feature | Previous | UML-Style |
|---------|----------|-----------|
| Class display | Simple box with counts | Three-section UML box |
| Attributes | Count only (e.g., "3 attr") | Listed inside class box |
| Node size | 220×80px fixed | 300×120px+ dynamic |
| Attribute limit | N/A | Shows max 5 + "... X more" |
| Tooltips | None | Description on attribute hover |

## File Changes

1. **src/lib/ontologyGraphLayout.ts**
   - Added `attributes` array to node data
   - Increased node dimensions (300×120)
   - Added debug logging

2. **src/components/OntologyGraph.tsx**
   - Redesigned ClassNode component (UML-style)
   - Three-section layout (header/attributes/footer)
   - Attribute rendering with type hints
   - Dynamic height based on content

3. **GRAPH_VISUALIZATION_GUIDE.md**
   - Created comprehensive guide (previous version)

4. **UML_GRAPH_IMPLEMENTATION.md**
   - This document (UML-specific details)
