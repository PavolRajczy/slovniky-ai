# Ontology Graph Component - Data Model

## Overview

The ontology graph visualization uses a **two-layer data model**:
1. **Backend/API Layer** - Domain models representing the ontology (from backend API)
2. **React Flow Layer** - Graph-specific models for visualization (nodes & edges)

## 1. Backend/API Layer (Domain Models)

These models come from the backend API and represent the semantic ontology structure.

### 1.1 OntologyModel
The root model containing all ontology data.

```typescript
export type OntologyModel = {
  uri: string;                              // Unique identifier (IRI)
  label: string;                            // Human-readable name
  description: string;                      // Description of the ontology
  classes?: OntologyClassModel[];           // Array of classes
  attributes?: OntologyAttributeModel[];    // Array of attributes
  relationships?: OntologyRelationshipModel[]; // Array of relationships
}
```

**Example:**
```json
{
  "uri": "https://data.gov.cz/slovniky/podminky-provozu/.../2025-10-11/",
  "label": "Ontologie silničních vozidel v2025-10-11",
  "description": "Ontologie silničních vozidel ve verzi v2025-10-11",
  "classes": [...],
  "attributes": [...],
  "relationships": [...]
}
```

### 1.2 OntologyClassModel
Represents a class (concept) in the ontology.

```typescript
export type OntologyClassModel = {
  uri: string;                    // Unique identifier (IRI)
  label: string;                  // Human-readable name
  description?: string | null;    // Description of the class
  parent_classes?: string[];      // Array of parent class URIs (inheritance)
}
```

**Example:**
```json
{
  "uri": "https://data.gov.cz/.../SilnicniVozidlo",
  "label": "Silniční vozidlo",
  "description": "Třída Silniční vozidlo zahrnuje vozidla...",
  "parent_classes": [
    "https://data.gov.cz/.../Vozidlo"
  ]
}
```

**Key Concept - Inheritance:**
- `parent_classes` array defines the class hierarchy
- Used to create **inheritance edges** (gray, dashed arrows in the graph)
- Multiple parents allowed (multiple inheritance)

### 1.3 OntologyAttributeModel
Represents an attribute (property with primitive type) of a class.

```typescript
export type OntologyAttributeModel = {
  uri: string;                    // Unique identifier (IRI)
  label: string;                  // Human-readable name
  description?: string | null;    // Description of the attribute
  domain_class: string;           // URI of the class that owns this attribute
  range_type: string;             // Data type (e.g., "string", "boolean")
}
```

**Example:**
```json
{
  "uri": "https://data.gov.cz/.../ucelPouzitiSilnicnihoVozidla",
  "label": "účel použití silničního vozidla",
  "description": "Určuje hlavní účel...",
  "domain_class": "https://data.gov.cz/.../SilnicniVozidlo",
  "range_type": "string"
}
```

**Key Concept - Attributes vs Relationships:**
- **Attributes** point to primitive types (string, boolean, number, date)
- Displayed **inside the class box** in UML style
- NOT shown as edges/arrows in the graph

### 1.4 OntologyRelationshipModel
Represents a relationship (association) between two classes.

```typescript
export type OntologyRelationshipModel = {
  uri: string;                    // Unique identifier (IRI)
  label: string;                  // Human-readable name
  description?: string | null;    // Description of the relationship
  domain_class: string;           // URI of the source class
  range_class: string;            // URI of the target class
}
```

**Example:**
```json
{
  "uri": "https://data.gov.cz/.../maKategoriiSilnicnihoVozidla",
  "label": "má kategorii silničního vozidla",
  "description": "Umožňuje přiřadit každému silničnímu vozidlu...",
  "domain_class": "https://data.gov.cz/.../SilnicniVozidlo",
  "range_class": "https://data.gov.cz/.../KategorieVozidla"
}
```

**Key Concept - Relationships:**
- **Relationships** connect two classes (domain → range)
- Displayed as **blue arrows with labels** in the graph
- Direction: domain_class → range_class

## 2. React Flow Layer (Graph Models)

These models are used by React Flow to render the visual graph.

### 2.1 GraphNode
Represents a visual node (class box) in the graph.

```typescript
export interface GraphNode extends Node {
  id: string;                     // Must match class URI
  type: 'classNode';              // Custom node type
  data: {
    label: string;                // Display name
    classModel: OntologyClassModel;  // Reference to original class
    attributes: OntologyAttributeModel[]; // Attributes for this class
    childCount: number;           // Number of direct subclasses
    attributeCount: number;       // Number of attributes
    relationshipCount: number;    // Number of outgoing relationships
  };
  position: { x: number; y: number };  // Position set by Dagre layout
}
```

**Example:**
```javascript
{
  id: "https://data.gov.cz/.../SilnicniVozidlo",
  type: "classNode",
  data: {
    label: "Silniční vozidlo",
    classModel: { uri: "...", label: "...", ... },
    attributes: [
      { uri: "...", label: "účel použití", range_type: "string" },
      { uri: "...", label: "povaha pohonu", range_type: "string" },
      ...
    ],
    childCount: 1,
    attributeCount: 3,
    relationshipCount: 1
  },
  position: { x: 450, y: 200 }
}
```

### 2.2 GraphEdge
Represents a visual edge (arrow) in the graph.

```typescript
export interface GraphEdge extends Edge {
  id: string;                     // Unique edge identifier
  source: string;                 // Source node ID (class URI)
  target: string;                 // Target node ID (class URI)
  label?: string;                 // Edge label (for relationships)
  type?: 'default' | 'smoothstep' | 'straight';  // Visual style
  data?: {
    relationship?: OntologyRelationshipModel;  // For relationship edges
    isInheritance?: boolean;                   // For inheritance edges
  };
}
```

**Example - Inheritance Edge:**
```javascript
{
  id: "inheritance-https://data.gov.cz/.../SilnicniVozidlo-...Vozidlo",
  source: "https://data.gov.cz/.../Vozidlo",
  target: "https://data.gov.cz/.../SilnicniVozidlo",
  type: "smoothstep",
  data: { isInheritance: true },
  style: { stroke: "#94a3b8", strokeWidth: 3, strokeDasharray: "5,5" },
  markerEnd: { type: "arrowclosed", color: "#94a3b8" }
}
```

**Example - Relationship Edge:**
```javascript
{
  id: "rel-0",
  source: "https://data.gov.cz/.../SilnicniVozidlo",
  target: "https://data.gov.cz/.../KategorieVozidla",
  label: "má kategorii silničního vozidla",
  type: "smoothstep",
  data: { 
    relationship: { uri: "...", label: "...", ... }
  },
  style: { stroke: "#3b82f6", strokeWidth: 3 },
  markerEnd: { type: "arrowclosed", color: "#3b82f6" }
}
```

## 3. Data Flow & Transformation

### Step 1: Fetch from API
```typescript
// In OntologyPage.tsx
const { data: ontology } = useQuery<OntologyModel>({
  queryKey: ['project', projectId, 'ontology'],
  queryFn: () => getProjectOntology(projectId, 'json'),
});
```

### Step 2: Build Graph Data
```typescript
// In ontologyGraphLayout.ts - buildGraphData()
function buildGraphData(ontology: OntologyModel): { 
  nodes: GraphNode[]; 
  edges: GraphEdge[] 
}
```

**Process:**
1. **Create nodes** - One node per class
   - Extract attributes for each class (filter by `domain_class`)
   - Calculate child count (count classes where `parent_classes` contains this class URI)
   - Calculate relationship count (count relationships where `domain_class` matches)

2. **Create inheritance edges** - From `parent_classes` array
   - For each class, iterate through `parent_classes`
   - Create edge: parent → child
   - Style: Gray, dashed

3. **Create relationship edges** - From `relationships` array
   - For each relationship
   - Create edge: domain_class → range_class
   - Add label from relationship
   - Style: Blue, solid

### Step 3: Apply Layout
```typescript
// In ontologyGraphLayout.ts - applyDagreLayout()
function applyDagreLayout(
  nodes: GraphNode[], 
  edges: GraphEdge[], 
  direction: 'TB' | 'LR'
): GraphNode[]
```

**Process:**
- Uses Dagre algorithm to position nodes hierarchically
- Sets `position: { x, y }` for each node
- Returns nodes with updated positions

### Step 4: Render in React Flow
```typescript
// In OntologyGraph.tsx
<ReactFlow
  nodes={nodes}
  edges={edges}
  nodeTypes={{ classNode: ClassNode }}
  ...
/>
```

## 4. Key Relationships

### Node ID Matching
**CRITICAL:** Edge source/target must **exactly match** node IDs.

```
Node.id = OntologyClassModel.uri
Edge.source = OntologyRelationshipModel.domain_class  (or parent class URI)
Edge.target = OntologyRelationshipModel.range_class   (or child class URI)
```

### Attribute Assignment
Attributes are assigned to nodes based on `domain_class`:

```typescript
const classAttributes = ontology.attributes?.filter(
  (attr) => attr.domain_class === classModel.uri
) || [];
```

### Hierarchy Building
Class hierarchy is derived from `parent_classes`:

```typescript
classModel.parent_classes?.forEach((parentIri) => {
  edges.push({
    source: parentIri,      // Parent
    target: classModel.uri, // Child
    // ...
  });
});
```

## 5. Visual Representation Mapping

| Domain Concept | Visual Representation | Graph Element |
|----------------|----------------------|---------------|
| Class | UML-style box with 3 sections | GraphNode (custom ClassNode component) |
| Attribute | Listed inside class box | Text inside node |
| Inheritance (parent_classes) | Gray dashed arrow | GraphEdge (type: inheritance) |
| Relationship | Blue solid arrow with label | GraphEdge (type: relationship) |
| Class hierarchy | Vertical/horizontal layout | Dagre layout algorithm |

## 6. Example: Complete Flow

**Input (from API):**
```json
{
  "classes": [
    { "uri": "Class_A", "label": "Class A", "parent_classes": [] },
    { "uri": "Class_B", "label": "Class B", "parent_classes": ["Class_A"] }
  ],
  "attributes": [
    { "uri": "Attr_1", "label": "name", "domain_class": "Class_A", "range_type": "string" }
  ],
  "relationships": [
    { "uri": "Rel_1", "label": "has part", "domain_class": "Class_A", "range_class": "Class_B" }
  ]
}
```

**Output (Graph):**
```
Nodes: 2
  - Node { id: "Class_A", data: { label: "Class A", attributes: [Attr_1], ... } }
  - Node { id: "Class_B", data: { label: "Class B", attributes: [], ... } }

Edges: 2
  - Edge { source: "Class_A", target: "Class_B", type: "inheritance" }  // Gray dashed
  - Edge { source: "Class_A", target: "Class_B", label: "has part" }    // Blue solid
```

**Visual Result:**
```
┌─────────────┐
│   Class A   │
├─────────────┤
│ • name: str │
├─────────────┤
│ 1 rel 1 sub │
└──────┬──────┘
       │ (gray dashed - inheritance)
       ↓
┌─────────────┐
│   Class B   │
├─────────────┤
│             │
├─────────────┤
│             │
└─────────────┘
       ↑
       │ (blue solid - "has part")
       │
    (from Class A)
```

## Summary

The data model has **two layers**:

1. **Domain Layer** (API models):
   - `OntologyModel` → Contains everything
   - `OntologyClassModel` → Classes with inheritance
   - `OntologyAttributeModel` → Properties with primitive types
   - `OntologyRelationshipModel` → Associations between classes

2. **Visualization Layer** (React Flow models):
   - `GraphNode` → Visual class boxes
   - `GraphEdge` → Visual arrows (inheritance + relationships)

**The transformation** happens in `ontologyGraphLayout.ts` which:
- Maps classes → nodes
- Maps parent_classes → inheritance edges
- Maps relationships → relationship edges
- Applies Dagre layout for positioning
