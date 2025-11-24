# Force View - Quick Reference

## User Guide

### What is Force View?

Force View is a **physics-based interactive graph** that shows your ontology as a living network where:
- **Nodes** (circles) = Classes
- **Blue solid arrows** = Relationships between classes
- **Gray dashed arrows** = Inheritance (parent → child)

The layout is computed using physics simulation - nodes attract/repel each other to find natural positions.

### Controls

| Action | How To | What It Does |
|--------|--------|--------------|
| **Select a class** | Click on a node | Highlights the node with blue halo |
| **Move a node** | Click and drag | Repositions the node temporarily |
| **Pin a node** | Double-click | Fixes the node in place (orange halo) |
| **Unpin a node** | Double-click again | Lets physics move it again |
| **Zoom in/out** | Mouse wheel | Zoom 0.1x to 4x |
| **Pan the view** | Drag background | Move the entire graph |

### Visual Guide

```
    ┌─────────┐
    │  Node   │  ← Class name
    └─────────┘
         │
         ↓ Gray dashed = Inheritance
    ┌─────────┐
    │ SubClass│
    └─────────┘
         │
         ↓ Blue solid = Relationship
    ┌─────────┐
    │ Related │
    └─────────┘
```

**Node States:**
- Normal: Gray outline
- Selected: **Blue halo** (thick)
- Pinned: **Orange dashed halo**
- Selected + Pinned: Both halos visible

### Tips & Tricks

1. **Organize your layout**
   - Drag important classes to corners
   - Double-click to pin them in place
   - Let physics arrange the rest

2. **Find relationships**
   - Follow the arrows to see connections
   - Blue = "has relationship with"
   - Gray = "is a kind of"

3. **Zoom for detail**
   - Zoom out: See overall structure
   - Zoom in: Read edge labels

4. **Navigate large ontologies**
   - Click to select a class
   - It syncs with Grid View for details
   - Switch tabs to see attributes

## Developer Guide

### Quick Start

```tsx
import { OntologyForceGraph } from '@/components/OntologyForceGraph';

<OntologyForceGraph
  ontology={ontologyData}
  selectedElement={selectedElement}
  onSelectClass={(uri) => setSelectedElement({ type: 'class', uri })}
/>
```

### Data Requirements

**Input:**
- `ontology: OntologyModel` - Standard ontology data from API
- `selectedElement: SelectedElement` - Current selection state
- `onSelectClass: (uri: string) => void` - Selection callback

**Data is automatically transformed** via `buildGraphData()`:
```typescript
const { nodes, edges } = buildGraphData(ontology);
// Nodes: GraphNode[] with id, data.label, position
// Edges: GraphEdge[] with source, target, label, data.isInheritance
```

### Customization

**Change colors** (edit `src/lib/OntologyCanvas.ts`):
```typescript
const REL_STYLE = {
  association: {
    stroke: '#3b82f6',  // ← Your color
    // ...
  },
  inheritance: {
    stroke: '#94a3b8',  // ← Your color
    dash: [6, 3],       // ← Dash pattern
  },
};
```

**Adjust physics** (edit constructor):
```typescript
.force('charge', d3.forceManyBody().strength(-300))  // ← Repulsion
.force('link', d3.forceLink().distance(150))         // ← Link length
```

**Change node size**:
```typescript
radius: 18,  // ← Node radius in pixels
```

### API Reference

**OntologyCanvas class:**

```typescript
class OntologyCanvas {
  // Create canvas and initialize simulation
  constructor(
    container: HTMLElement,
    width: number,
    height: number,
    onNodeClick?: (nodeId: string) => void
  )

  // Load ontology data
  loadData(nodes: GraphNode[], edges: GraphEdge[]): void

  // Update selection (external control)
  setSelectedNode(nodeId: string | null): void

  // Cleanup
  destroy(): void
}
```

**Private methods** (internal):
- `render()` - Draws canvas frame
- `computeControlPoint()` - Calculates curved edge paths
- `drawArrowhead()` - Renders arrow markers
- `findNodeAt()` - Hit-test for clicks
- `invertToGraphCoords()` - Screen to graph coordinates

### Lifecycle

```typescript
// Mount
useEffect(() => {
  const canvas = new OntologyCanvas(container, width, height, onNodeClick);
  canvasRef.current = canvas;
  
  return () => canvas.destroy(); // Cleanup
}, []);

// Load data
useEffect(() => {
  if (canvas && ontology) {
    const { nodes, edges } = buildGraphData(ontology);
    canvas.loadData(nodes, edges);
  }
}, [ontology]);

// Update selection
useEffect(() => {
  if (canvas && selectedElement?.type === 'class') {
    canvas.setSelectedNode(selectedElement.uri);
  }
}, [selectedElement]);
```

### Performance Tips

1. **Large graphs (1000+ nodes)**
   - Reduce `forceManyBody` iterations
   - Increase `forceCollide` radius to reduce overlap checking
   - Consider throttling render to 30fps

2. **Slow interactions**
   - Lower `alphaTarget` in drag handlers
   - Use `alphaDecay` to stop simulation faster

3. **Memory optimization**
   - Call `destroy()` when unmounting
   - Clear references to avoid leaks

### Debugging

**Enable console logs:**
```typescript
// In OntologyCanvas.ts
console.log('Nodes:', this.nodes.length);
console.log('Links:', this.links.length);
console.log('Transform:', this.transform);
```

**Check canvas rendering:**
```javascript
// Browser console
const canvas = document.querySelector('canvas');
const ctx = canvas.getContext('2d');
console.log('Canvas size:', canvas.width, canvas.height);
```

**Inspect D3 simulation:**
```javascript
// In browser console (add window.simulation = this.simulation)
simulation.nodes();  // Current node positions
simulation.alpha();  // Current energy level
simulation.restart();  // Re-run simulation
```

### Common Issues

**Problem: Edges not showing**
- ✅ Check `edge.source` and `edge.target` match node IDs exactly
- ✅ Verify `buildGraphData()` returns edges
- ✅ Look for console errors

**Problem: Simulation won't stop**
- ✅ Check `alphaDecay` is not too small
- ✅ Call `simulation.stop()` on unmount
- ✅ Don't set `alphaTarget > 0` continuously

**Problem: Canvas is blank**
- ✅ Check container has width/height
- ✅ Verify `loadData()` was called
- ✅ Check browser console for errors

**Problem: Performance lag**
- ✅ Check number of nodes (>5000 is heavy)
- ✅ Reduce force iterations
- ✅ Use requestAnimationFrame throttling

### Extension Points

**Add new edge types:**
```typescript
// 1. Add to REL_STYLE
aggregation: {
  stroke: '#10b981',
  dash: [2, 2],
  // ...
}

// 2. Detect in loadData()
const kind = e.data?.isAggregation ? 'aggregation' : 'association';

// 3. Apply style in render()
const style = REL_STYLE[link._kind];
```

**Add node badges/icons:**
```typescript
// In render(), after drawing circle:
if (node.important) {
  ctx.fillStyle = '#ff0000';
  ctx.beginPath();
  ctx.arc(node.x + 12, node.y - 12, 4, 0, 2 * Math.PI);
  ctx.fill();
}
```

**Add minimap:**
```typescript
// Draw small version in corner
ctx.save();
ctx.translate(width - 200, height - 150);
ctx.scale(0.1, 0.1);
// ... draw nodes/edges again
ctx.restore();
```

## Troubleshooting

### Node positions reset on reload

**Cause**: Positions are not persisted.

**Solution**: Save positions to localStorage:
```typescript
// Save
localStorage.setItem('nodePositions', JSON.stringify(
  nodes.map(n => ({ id: n.id, x: n.x, y: n.y, pinned: n.pinned }))
));

// Load
const saved = JSON.parse(localStorage.getItem('nodePositions') || '[]');
nodes.forEach(n => {
  const pos = saved.find(s => s.id === n.id);
  if (pos) {
    n.x = pos.x;
    n.y = pos.y;
    if (pos.pinned) { n.fx = pos.x; n.fy = pos.y; n.pinned = true; }
  }
});
```

### Multi-edge curves overlap

**Cause**: Offset calculation needs tuning.

**Solution**: Adjust `base` in `computeControlPoint()`:
```typescript
const base = Math.min(100, Math.max(30, len * 0.25)); // Increase range
```

### Labels unreadable at low zoom

**Cause**: Text size doesn't scale with zoom.

**Solution**: Make font size zoom-aware:
```typescript
const fontSize = Math.max(8, Math.min(12, 10 / this.transform.k));
ctx.font = `${fontSize}px sans-serif`;
```

## Credits

Based on the WebVOWL-inspired prototype by Martin (user-tested and approved).

**Technologies:**
- D3.js - Force layout, zoom, drag
- Canvas 2D - Rendering
- TypeScript - Type safety
- React - Component wrapper

**Design principles:**
- Performance first (Canvas over SVG)
- User control (drag, pin, zoom)
- Visual clarity (curved edges, clear labels)
- Integration (shares data with Grid/Graph views)
