# Edge Rendering Troubleshooting - Phase 4

## Current Status

### ✅ What's Working
- **23 nodes** created correctly
- **24 edges** created correctly (16 inheritance + 8 relationships)
- **UML-style class boxes** with attributes displayed
- **Data structure** is correct (verified via console)

### ❌ What's NOT Working
- **Edges are not visually rendering** in the graph

## Changes Made (Latest Iteration)

### 1. Edge Type Changed
- From: `type: 'straight'` and `type: 'default'`
- To: `type: 'smoothstep'` for both inheritance and relationships
- Reason: `smoothstep` is more commonly used and has better rendering support

### 2. Edge Styling Enhanced
**Inheritance edges (gray, dashed):**
- Stroke width: `3px` (was 2px)
- Stroke dash: `'5,5'` (dashed line)
- Color: `#94a3b8` (gray)

**Relationship edges (blue, solid):**
- Stroke width: `3px` (was 2px)  
- Color: `#3b82f6` (blue)
- Label style: Darker blue, larger font (12px, weight 600)

### 3. Additional Debugging
Added check for edges with missing source/target nodes:
```javascript
const nodeIds = new Set(nodes.map(n => n.id));
const edgeIssues = edges.filter(e => !nodeIds.has(e.source) || !nodeIds.has(e.target));
```

### 4. React Flow Props
- Added `defaultEdgeOptions: { type: 'smoothstep' }`
- This ensures all edges use smoothstep rendering

## Next Steps for Testing

### 1. Refresh Browser
Hard refresh (Ctrl+Shift+R or Ctrl+F5) to ensure latest code is loaded

### 2. Check Console Output
Look for new debug information:
```
📊 OntologyGraph rendering: {
  nodesCount: 23,
  edgesCount: 24,
  edgesWithMissingNodes: ?, // Should be 0
  sampleMissingEdges: []     // Should be empty
}
```

### 3. Visual Inspection
- **Inheritance edges**: Should be **gray dashed lines** with arrows
- **Relationship edges**: Should be **solid blue lines** with labels
- Try zooming out to see if edges are outside viewport

### 4. Try These Actions in the Graph
1. Click "Fit View" button (bottom-left controls)
2. Zoom out using mouse wheel
3. Pan around the graph to look for edges
4. Check MiniMap (bottom-right) for edge indicators

## Possible Remaining Issues

### Issue 1: React Flow Version Compatibility
The `@xyflow/react` v12.8.6 might have specific requirements.

**Test**: Check if edges render with a simple example:
```tsx
const testEdge = {
  id: 'test-edge',
  source: nodes[0]?.id,
  target: nodes[1]?.id,
  type: 'smoothstep',
};
```

### Issue 2: CSS/Styling Override
Tailwind or global CSS might be hiding edges.

**Test**: Inspect browser DevTools, look for `.react-flow__edge` elements in the DOM.
- If elements exist but not visible → CSS issue
- If elements don't exist → React Flow not rendering them

### Issue 3: Graph Layout
Dagre might be positioning nodes such that edges are clipped or outside the viewport.

**Test**: 
1. Console log node positions after Dagre layout
2. Check if all nodes have valid x,y coordinates
3. Verify edges connect to nodes at valid positions

### Issue 4: Node Handle Points
React Flow requires nodes to have handle points for edge connections. Custom nodes might need explicit handles.

**Potential Fix**: Add handle points to ClassNode component:
```tsx
import { Handle, Position } from '@xyflow/react';

// In ClassNode component:
<Handle type="target" position={Position.Top} />
<Handle type="source" position={Position.Bottom} />
```

## Diagnostic Commands

### Check React Flow is imported correctly:
```bash
npm list @xyflow/react
```

### Check for CSS conflicts:
Open DevTools → Elements → Find `.react-flow__edge` → Check computed styles

### Verify edge data structure:
Console should show edges like:
```javascript
{
  id: "rel-0",
  source: "https://data.gov.cz/.../SilnicniVozidlo",
  target: "https://data.gov.cz/.../KategorieVozidla",
  label: "má kategorii silničního vozidla",
  type: "smoothstep",
  style: { stroke: "#3b82f6", strokeWidth: 3 },
  markerEnd: { type: "arrowclosed", color: "#3b82f6" }
}
```

## Most Likely Cause

Based on the symptoms (nodes render, edges don't), the most likely issue is **#4: Missing Handle Points**.

React Flow requires nodes to explicitly define connection points (handles) for edges to attach to. Without handles, edges won't render even if the data is correct.

## Immediate Next Action

Add Handle components to the ClassNode:

```tsx
import { Handle, Position, NodeProps } from '@xyflow/react';

const ClassNode: React.FC<NodeProps> = ({ data, selected }) => {
  // ... existing code ...
  
  return (
    <div className="...">
      {/* Add handles */}
      <Handle 
        type="target" 
        position={Position.Top} 
        style={{ background: '#555' }}
      />
      
      {/* Existing node content */}
      <div className="px-4 py-2 bg-gray-50...">
        {label}
      </div>
      {/* ... */}
      
      <Handle 
        type="source" 
        position={Position.Bottom} 
        style={{ background: '#555' }}
      />
    </div>
  );
};
```

This will add visible connection points at the top (for incoming edges) and bottom (for outgoing edges) of each node.
