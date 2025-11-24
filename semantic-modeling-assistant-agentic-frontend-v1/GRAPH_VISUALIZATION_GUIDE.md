# Ontology Graph Visualization Guide

## What is Displayed

### Nodes (Classes)
Each class in the ontology is shown as a **rounded box node** containing:
- **Class name** (label) - displayed prominently at the top
- **Statistics** showing counts for:
  - **attr** - Number of attributes with this class as domain
  - **rel** - Number of relationships with this class as domain  
  - **sub** - Number of direct subclasses (children in hierarchy)

Example:
```
┌─────────────────────┐
│ Silniční vozidlo    │
│ 3 attr  1 rel  1 sub│
└─────────────────────┘
```

### Edges (Connections)

There are **two types of edges** in the graph:

#### 1. Inheritance Edges (Gray)
- **Color**: Gray (#94a3b8)
- **Style**: Solid line with arrow
- **Meaning**: Represents `parent_classes` relationships (class hierarchy)
- **Direction**: From parent → child
- **Example**: `Vozidlo → Silniční vozidlo` (Silniční vozidlo is a subclass of Vozidlo)

#### 2. Relationship Edges (Blue)
- **Color**: Blue (#3b82f6)
- **Style**: Solid line with arrow and label
- **Meaning**: Represents semantic relationships between classes
- **Label**: Shows the relationship name (e.g., "má kategorii silničního vozidla")
- **Direction**: From domain class → range class
- **Example**: `Silniční vozidlo → Kategorie vozidla` with label "má kategorii silničního vozidla"

### What About Attributes?

Attributes are **not shown as separate nodes or edges** in the graph. Instead:
- The **count** of attributes for each class is displayed inside the class node
- Clicking on a class in the graph will show its attributes in the **Grid View** when you switch tabs
- Attributes typically point to primitive types (string, boolean, etc.) rather than other classes, so they don't create interesting graph connections

## Layout Algorithm

The graph uses the **Dagre hierarchical layout algorithm**:
- **Direction**: Top to bottom (TB)
- **Node spacing**: 100px horizontal, 100px vertical
- **Rank separation**: 150px between hierarchy levels
- **Purpose**: Automatically positions nodes to minimize edge crossings and show hierarchy clearly

## Interaction

- **Click a node** - Selects the class (highlighted with blue border)
- **Zoom** - Use mouse wheel or controls
- **Pan** - Click and drag the background
- **MiniMap** - Shows overview of entire graph (bottom-right)
- **Controls** - Zoom in/out, fit view, etc. (bottom-left)

## Selection Sync

- Selecting a class in the **Graph View** updates the selection in the **Grid View**
- Selecting a class in the **Grid View** updates the selection in the **Graph View**
- The graph does **not** automatically switch tabs - selection is "silent"

## Example from Your Ontology

Looking at your attached ontology (`ontology-8b0b727e-80bd-4a19-b76b-ede8478c0698.ttl`):

### Nodes Created: 23 classes
- Vozidlo
- Silniční vozidlo (child of Vozidlo)
- Zvláštní vozidlo (child of Vozidlo)
- Přípojné vozidlo (child of Vozidlo)
- Kategorie vozidla
- Kategorie vozidla - kód
- Kategorie L, M, N, O, T, C, R, S, Z (all children of Kategorie vozidla)
- Technický prvek vozidla
- Systém vozidla (child of Technický prvek vozidla)
- Konstrukční část vozidla (child of Technický prvek vozidla)
- Samostatný technický celek (child of Technický prvek vozidla)
- Typ technického prvku
- Schválení typu
- Omezení použití

### Inheritance Edges: 16 edges (gray)
Examples:
- Vozidlo → Silniční vozidlo
- Vozidlo → Zvláštní vozidlo
- Vozidlo → Přípojné vozidlo
- Kategorie vozidla → Kategorie L
- Kategorie vozidla → Kategorie M
- (etc.)

### Relationship Edges: 8 edges (blue with labels)
1. `Silniční vozidlo → Kategorie vozidla` - "má kategorii silničního vozidla"
2. `Zvláštní vozidlo → Kategorie vozidla` - "má kategorii zvláštního vozidla"
3. `Vozidlo → Technický prvek vozidla` - "je vybaveno technickým prvkem vozidla"
4. `Typ technického prvku → Technický prvek vozidla` - "je typem"
5. `Typ technického prvku → Schválení typu` - "má schválení"
6. `Schválení typu → Omezení použití` - "má omezení použití"
7. `Omezení použití → Kategorie vozidla` - "omezuje použití pro kategorii"
8. `Technický prvek vozidla → Kategorie vozidla` - "je určen pro kategorii"

### Attributes: NOT shown as edges
- 8 attributes total (shown as counts in class nodes)
- Examples:
  - Silniční vozidlo has 3 attributes (účel použití, je určeno k provozu, povaha pohonu)
  - Zvláštní vozidlo has 2 attributes (účel použití, podmínky provozu)
  - Přípojné vozidlo has 3 attributes (je určeno k tažení, je samostatně poháněné, povaha pohonu)

## Why Relationships Might Not Have Been Visible

If you couldn't see the relationship edges in your initial view, it might be because:

1. **Zoom level** - The graph might have been zoomed out too far to see edge labels
2. **Edge overlap** - Multiple edges between same nodes might overlap
3. **Layout positioning** - Nodes might have been positioned such that edges were hard to see
4. **Color contrast** - Blue edges might blend with background at certain zoom levels

**Solution**: Use the "Fit View" control (bottom-left) to auto-zoom to show all nodes and edges clearly.
