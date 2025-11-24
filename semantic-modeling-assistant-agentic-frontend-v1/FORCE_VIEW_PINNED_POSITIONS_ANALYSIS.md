# Force View Pinned Positions Persistence Analysis

## Problem Statement

Currently, when users pin nodes in the Force View by dragging them, these positions are lost when:
- Switching to another view (Grid/Graph)
- Switching to another tab (Workbench, Compare, etc.)
- Filtering nodes (changing filter mode)
- Applying iteration operations
- Refreshing the page

Users need these pinned positions to persist across actions within a session, and ideally across browser sessions.

## Current Implementation

### How Pinning Works Now

**File: `src/lib/OntologyCanvas.ts`**

```typescript
interface D3Node extends d3.SimulationNodeDatum {
  id: string;
  label: string;
  color: string;
  radius: number;
  pinned?: boolean;     // Boolean flag
  fx?: number | null;   // Fixed X position
  fy?: number | null;   // Fixed Y position
  changeType?: ChangeType | null;
}
```

**Pinning Process:**
1. User drags a node
2. On drag end, node is auto-pinned: `n.pinned = true; n.fx = n.x; n.fy = n.y;`
3. Right-click to unpin: `n.pinned = false; n.fx = null; n.fy = null;`

**When Positions Are Lost:**
```typescript
// In OntologyForceGraph.tsx - useEffect runs on every data change
useEffect(() => {
  canvasRef.current.loadData(nodes, edges);
  // ↑ This creates NEW D3Node objects, losing all pinned state
}, [ontology, changes, filteredElements]);
```

Every time `loadData()` is called, it creates fresh `D3Node` objects from `GraphNode[]`, discarding:
- `pinned` flags
- `fx/fy` fixed positions
- User's manual layout work

---

## Solution 1: Session Persistence (In-Memory)

### Approach: Zustand Store

Create a dedicated store to track pinned positions during the browser session.

### Implementation Design

#### 1. Create New Store: `src/store/nodePositionsStore.ts`

```typescript
import { create } from 'zustand'

export interface NodePosition {
  x: number
  y: number
  timestamp: number // For debugging/analytics
}

export interface NodePositionsState {
  // Key: `${projectId}:${nodeUri}` - scoped per project
  positions: Map<string, NodePosition>
  
  // Actions
  pinNode: (projectId: string, nodeUri: string, x: number, y: number) => void
  unpinNode: (projectId: string, nodeUri: string) => void
  getPosition: (projectId: string, nodeUri: string) => NodePosition | null
  clearProject: (projectId: string) => void
  clearAll: () => void
}

export const useNodePositionsStore = create<NodePositionsState>((set, get) => ({
  positions: new Map(),
  
  pinNode: (projectId, nodeUri, x, y) => {
    set(state => {
      const key = `${projectId}:${nodeUri}`
      const newPositions = new Map(state.positions)
      newPositions.set(key, { x, y, timestamp: Date.now() })
      return { positions: newPositions }
    })
  },
  
  unpinNode: (projectId, nodeUri) => {
    set(state => {
      const key = `${projectId}:${nodeUri}`
      const newPositions = new Map(state.positions)
      newPositions.delete(key)
      return { positions: newPositions }
    })
  },
  
  getPosition: (projectId, nodeUri) => {
    const key = `${projectId}:${nodeUri}`
    return get().positions.get(key) || null
  },
  
  clearProject: (projectId) => {
    set(state => {
      const newPositions = new Map(state.positions)
      for (const key of newPositions.keys()) {
        if (key.startsWith(`${projectId}:`)) {
          newPositions.delete(key)
        }
      }
      return { positions: newPositions }
    })
  },
  
  clearAll: () => {
    set({ positions: new Map() })
  },
}))
```

#### 2. Update `OntologyCanvas.ts`

Add callbacks to save/load positions:

```typescript
export class OntologyCanvas {
  private onNodePin?: (nodeId: string, x: number, y: number) => void;
  private onNodeUnpin?: (nodeId: string) => void;

  constructor(
    container: HTMLElement,
    width: number,
    height: number,
    onNodeClick?: (nodeId: string) => void,
    onNodePin?: (nodeId: string, x: number, y: number) => void,
    onNodeUnpin?: (nodeId: string) => void
  ) {
    // ... existing code ...
    this.onNodePin = onNodePin;
    this.onNodeUnpin = onNodeUnpin;
  }

  loadData(nodes: GraphNode[], edges: GraphEdge[], pinnedPositions?: Map<string, {x: number, y: number}>) {
    this.nodes = nodes.map(n => {
      const pinned = pinnedPositions?.get(n.id);
      return {
        id: n.id,
        label: n.data.label,
        color: '#3b82f6',
        radius: 30,
        changeType: n.data.changeType,
        // Restore pinned state
        pinned: pinned !== undefined,
        fx: pinned?.x ?? null,
        fy: pinned?.y ?? null,
      };
    });
    
    // ... rest of loadData ...
  }

  private initDrag() {
    // ... existing drag code ...
    
    .on('end', (event) => {
      const n = event.subject;
      if (!n) return;
      this.canvas.style.cursor = 'grab';
      
      n.pinned = true;
      n.fx = n.x;
      n.fy = n.y;
      
      // Notify store
      if (this.onNodePin && n.fx !== undefined && n.fy !== undefined) {
        this.onNodePin(n.id, n.fx, n.fy);
      }
      
      if (!event.active) this.simulation.alphaTarget(0);
      this.render();
    });
  }

  private initDoubleClickPin() {
    this.canvas.addEventListener('contextmenu', (e) => {
      // ... existing code ...
      
      if (n.pinned) {
        n.pinned = false;
        n.fx = null;
        n.fy = null;
        
        // Notify store
        if (this.onNodeUnpin) {
          this.onNodeUnpin(n.id);
        }
        
        this.simulation.alpha(0.4).restart();
        this.render();
      }
    });
  }
}
```

#### 3. Update `OntologyForceGraph.tsx`

```typescript
import { useNodePositionsStore } from '@/store/nodePositionsStore';
import { useProjectStore } from '@/store/projectStore';

export const OntologyForceGraph: React.FC<OntologyForceGraphProps> = ({
  ontology,
  selectedElement,
  onSelectClass,
  changes,
  filteredElements,
}) => {
  const { projectId } = useProjectStore();
  const { pinNode, unpinNode, getPosition } = useNodePositionsStore();
  
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<OntologyCanvas | null>(null);
  
  // Initialize canvas with pin callbacks
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const rect = container.getBoundingClientRect();
    const canvas = new OntologyCanvas(
      container, 
      rect.width, 
      rect.height, 
      onSelectClass,
      // onNodePin callback
      (nodeUri, x, y) => {
        if (projectId) {
          pinNode(projectId, nodeUri, x, y);
        }
      },
      // onNodeUnpin callback
      (nodeUri) => {
        if (projectId) {
          unpinNode(projectId, nodeUri);
        }
      }
    );
    
    canvasRef.current = canvas;
    return () => {
      canvas.destroy();
      canvasRef.current = null;
    };
  }, [projectId, onSelectClass, pinNode, unpinNode]);

  // Load data with pinned positions
  useEffect(() => {
    if (!canvasRef.current || !ontology || !projectId) return;

    let { nodes, edges } = buildGraphData(ontology);
    
    // Apply filtering...
    // Add change information...
    
    // Collect pinned positions for visible nodes
    const pinnedPositions = new Map<string, {x: number, y: number}>();
    nodes.forEach(node => {
      const pos = getPosition(projectId, node.id);
      if (pos) {
        pinnedPositions.set(node.id, { x: pos.x, y: pos.y });
      }
    });
    
    canvasRef.current.loadData(nodes, edges, pinnedPositions);
  }, [ontology, changes, filteredElements, projectId, getPosition]);
}
```

### Pros of Session Persistence (In-Memory)
✅ **Simple to implement** - No async operations, no backend changes
✅ **Fast** - Instant save/restore, no network latency
✅ **Privacy-friendly** - No data leaves the browser
✅ **Works offline** - No server dependency
✅ **Automatic cleanup** - Positions cleared on page refresh

### Cons of Session Persistence
❌ **Lost on refresh** - User must re-pin after browser refresh
❌ **Not shared** - Different browser tabs have separate states
❌ **Lost on crash** - No recovery if browser crashes
❌ **Device-specific** - Can't access from different computer

---

## Solution 2: Cross-Session Persistence (localStorage)

### Approach: Browser localStorage

Store pinned positions in `localStorage` for persistence across sessions.

### Implementation Design

#### Enhanced Store with localStorage Sync

```typescript
import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'

export interface NodePosition {
  x: number
  y: number
  timestamp: number
}

export interface NodePositionsState {
  positions: Map<string, NodePosition>
  
  pinNode: (projectId: string, nodeUri: string, x: number, y: number) => void
  unpinNode: (projectId: string, nodeUri: string) => void
  getPosition: (projectId: string, nodeUri: string) => NodePosition | null
  clearProject: (projectId: string) => void
  clearAll: () => void
  pruneOldPositions: (maxAgeMs: number) => void
}

export const useNodePositionsStore = create<NodePositionsState>()(
  persist(
    (set, get) => ({
      positions: new Map(),
      
      pinNode: (projectId, nodeUri, x, y) => {
        set(state => {
          const key = `${projectId}:${nodeUri}`
          const newPositions = new Map(state.positions)
          newPositions.set(key, { x, y, timestamp: Date.now() })
          return { positions: newPositions }
        })
      },
      
      unpinNode: (projectId, nodeUri) => {
        set(state => {
          const key = `${projectId}:${nodeUri}`
          const newPositions = new Map(state.positions)
          newPositions.delete(key)
          return { positions: newPositions }
        })
      },
      
      getPosition: (projectId, nodeUri) => {
        const key = `${projectId}:${nodeUri}`
        return get().positions.get(key) || null
      },
      
      clearProject: (projectId) => {
        set(state => {
          const newPositions = new Map(state.positions)
          for (const key of newPositions.keys()) {
            if (key.startsWith(`${projectId}:`)) {
              newPositions.delete(key)
            }
          }
          return { positions: newPositions }
        })
      },
      
      clearAll: () => {
        set({ positions: new Map() })
      },
      
      pruneOldPositions: (maxAgeMs) => {
        set(state => {
          const now = Date.now()
          const newPositions = new Map(state.positions)
          for (const [key, pos] of newPositions.entries()) {
            if (now - pos.timestamp > maxAgeMs) {
              newPositions.delete(key)
            }
          }
          return { positions: newPositions }
        })
      },
    }),
    {
      name: 'ontology-node-positions',
      storage: createJSONStorage(() => localStorage),
      // Custom serialization for Map
      serialize: (state) => {
        return JSON.stringify({
          ...state,
          state: {
            ...state.state,
            positions: Array.from(state.state.positions.entries()),
          },
        })
      },
      deserialize: (str) => {
        const parsed = JSON.parse(str)
        return {
          ...parsed,
          state: {
            ...parsed.state,
            positions: new Map(parsed.state.positions),
          },
        }
      },
    }
  )
)
```

#### Automatic Cleanup on App Load

```typescript
// In main.tsx or App component
useEffect(() => {
  // Prune positions older than 30 days on app load
  const store = useNodePositionsStore.getState();
  store.pruneOldPositions(30 * 24 * 60 * 60 * 1000);
}, []);
```

### Pros of localStorage Persistence
✅ **Survives refresh** - Positions persist across page reloads
✅ **Long-term storage** - Positions persist for days/weeks
✅ **Simple implementation** - Browser built-in feature
✅ **No backend changes** - Client-side only
✅ **Fast access** - Synchronous localStorage API

### Cons of localStorage Persistence
⚠️ **localStorage size limit** - ~5-10MB per domain
⚠️ **Device-specific** - Not synced across devices
⚠️ **Privacy concerns** - Stored in plain text locally
⚠️ **No conflict resolution** - Multiple tabs can conflict
⚠️ **Stale data risk** - Positions may be invalid after ontology changes

### localStorage Size Estimation

**Per pinned node:** ~80 bytes
```json
{
  "project-123:http://onto.fel.cvut.cz/ontologies/class/Person": {
    "x": 425.67,
    "y": 318.92,
    "timestamp": 1729180800000
  }
}
```

**Capacity:** 5MB / 80 bytes = ~62,500 pinned nodes
**Realistic usage:** 10-50 pinned nodes per project, 10 projects = 100-500 nodes total

**Conclusion:** localStorage size is not a concern for this use case.

---

## Solution 3: Server-Side Persistence (Backend API)

### Approach: Store positions on the server

This would provide true cross-device, multi-user persistence.

### Implementation Design

#### Backend API Endpoints (Hypothetical)

```typescript
// GET /api/projects/:projectId/node-positions
{
  "positions": [
    {
      "nodeUri": "http://onto.fel.cvut.cz/ontologies/class/Person",
      "x": 425.67,
      "y": 318.92,
      "lastModified": "2025-10-18T10:30:00Z"
    }
  ]
}

// POST /api/projects/:projectId/node-positions
{
  "nodeUri": "http://onto.fel.cvut.cz/ontologies/class/Person",
  "x": 425.67,
  "y": 318.92
}

// DELETE /api/projects/:projectId/node-positions/:nodeUri
```

#### Frontend Store with API Integration

```typescript
export const useNodePositionsStore = create<NodePositionsState>((set, get) => ({
  positions: new Map(),
  isLoading: false,
  
  // Load positions from server
  loadProjectPositions: async (projectId: string) => {
    set({ isLoading: true });
    try {
      const response = await api.getNodePositions(projectId);
      const positions = new Map(
        response.positions.map(p => [`${projectId}:${p.nodeUri}`, p])
      );
      set({ positions, isLoading: false });
    } catch (error) {
      console.error('Failed to load node positions:', error);
      set({ isLoading: false });
    }
  },
  
  // Save position to server (debounced)
  pinNode: async (projectId: string, nodeUri: string, x: number, y: number) => {
    // Update local state immediately (optimistic update)
    const key = `${projectId}:${nodeUri}`;
    set(state => {
      const newPositions = new Map(state.positions);
      newPositions.set(key, { x, y, timestamp: Date.now() });
      return { positions: newPositions };
    });
    
    // Debounced save to server
    debouncedSavePosition(projectId, nodeUri, x, y);
  },
  
  // ... other methods
}));

// Debounce to avoid excessive API calls during dragging
const debouncedSavePosition = debounce(async (projectId, nodeUri, x, y) => {
  try {
    await api.saveNodePosition(projectId, nodeUri, x, y);
  } catch (error) {
    console.error('Failed to save node position:', error);
    // Could implement retry logic here
  }
}, 1000);
```

### Pros of Server-Side Persistence
✅ **Cross-device sync** - Access from any device
✅ **Multi-user support** - Team collaboration possible
✅ **Backup & recovery** - Data stored on server
✅ **Unlimited storage** - No browser limits
✅ **Version control** - Can track position history
✅ **Conflict resolution** - Server can handle concurrent updates

### Cons of Server-Side Persistence
❌ **Backend implementation required** - Significant dev effort
❌ **API latency** - Network delay on save/load
❌ **Server load** - Additional database operations
❌ **Requires authentication** - User/project security
❌ **Offline mode complexity** - Sync conflicts
❌ **Backend API changes** - May not be possible to implement

---

## Recommended Implementation Plan

### Phase 1: Session Persistence (Immediate) ⭐ **RECOMMENDED**

**Effort:** Low (4-6 hours)
**Complexity:** Low
**Risk:** Minimal

**Steps:**
1. Create `src/store/nodePositionsStore.ts` (in-memory Map)
2. Update `OntologyCanvas.ts` to accept pin/unpin callbacks
3. Update `OntologyForceGraph.tsx` to use store
4. Test across view switches, filter changes, iteration operations

**Benefits:**
- Solves 90% of the user pain points
- No dependency on backend team
- Can be implemented and deployed immediately
- Low risk of bugs or performance issues

### Phase 2: localStorage Persistence (Short-term Enhancement)

**Effort:** Low (2-3 hours additional)
**Complexity:** Low-Medium
**Risk:** Low

**Steps:**
1. Add zustand `persist` middleware to store
2. Implement Map serialization/deserialization
3. Add cleanup logic for stale positions
4. Test localStorage size limits

**Benefits:**
- Positions survive page refresh
- Minimal additional code
- No backend changes needed

### Phase 3: Server-Side Persistence (Long-term Vision)

**Effort:** High (2-3 days + backend work)
**Complexity:** High
**Risk:** Medium-High

**Prerequisites:**
- Backend API endpoints implemented
- Authentication/authorization in place
- Database schema defined
- Conflict resolution strategy agreed

**Considerations:**
- Only implement if multi-device/team collaboration is required
- Consider using localStorage as fallback for offline mode
- Implement optimistic updates for better UX

---

## Implementation Recommendation

### Start with Phase 1 (Session Persistence)

**Rationale:**
1. **Immediate value** - Solves the problem for 90% of use cases
2. **Low risk** - No external dependencies, easy to rollback
3. **Fast implementation** - Can be done in a day
4. **Foundation for future** - Store interface can be extended later

**Phase 1 Success Criteria:**
- ✅ Pinned positions persist when switching views
- ✅ Pinned positions persist when filtering
- ✅ Pinned positions persist when applying iterations
- ✅ Positions cleared on page refresh (expected behavior)
- ✅ No performance degradation

### Then Add Phase 2 (localStorage) if needed

**Triggers for Phase 2:**
- User feedback requests persistence across sessions
- Users frequently lose work due to accidental refreshes
- Competition offers this feature
- Development time available

**Phase 2 Success Criteria:**
- ✅ All Phase 1 criteria met
- ✅ Positions survive page refresh
- ✅ Positions auto-expire after 30 days
- ✅ localStorage size stays under 100KB
- ✅ No conflicts between multiple tabs

### Consider Phase 3 (Server) only if absolutely necessary

**Triggers for Phase 3:**
- Multi-user collaboration requirement
- Cross-device access requirement
- Enterprise customer demand
- Backend team has capacity

---

## Edge Cases to Handle

### 1. Node URI Changes
**Problem:** If ontology is modified and class URI changes, pinned position becomes invalid.

**Solution:**
```typescript
// In loadData(), check if pinned node still exists
const pinnedPositions = new Map();
nodes.forEach(node => {
  const pos = getPosition(projectId, node.id);
  if (pos) {
    pinnedPositions.set(node.id, pos);
  }
});

// Optionally: Clean up orphaned positions
const validNodeUris = new Set(nodes.map(n => n.id));
for (const key of store.positions.keys()) {
  const [pid, uri] = key.split(':');
  if (pid === projectId && !validNodeUris.has(uri)) {
    store.unpinNode(pid, uri);
  }
}
```

### 2. Filtered Nodes
**Problem:** When filter hides a pinned node, what happens when filter changes back?

**Solution:**
- Keep pinned positions in store even when node is filtered out
- When node becomes visible again, restore its position
- This is already handled by current design

### 3. Viewport Transformation
**Problem:** Pinned positions are in graph coordinates, but viewport may zoom/pan.

**Solution:**
- Store positions in graph coordinates (not canvas/screen coordinates)
- D3 simulation handles coordinate transformation automatically
- Current implementation is correct

### 4. Multiple Ontology Versions
**Problem:** Applying iteration creates new ontology version with potentially different structure.

**Solution (Session persistence):**
- Clear positions when new iteration is applied (optional)
- Or keep positions and let invalid ones be ignored (current behavior)

**Solution (localStorage persistence):**
- Namespace by iteration ID: `${projectId}:${iterationId}:${nodeUri}`
- Each iteration has its own position cache
- Prevents confusion between different ontology versions

### 5. Performance with Many Pinned Nodes
**Problem:** Large Map lookups on every render?

**Solution:**
- Map lookups are O(1), no performance issue
- Only lookup happens once per `loadData()` call
- No impact on render performance

---

## Testing Checklist

### Session Persistence Tests
- [ ] Pin a node, switch to Grid view, switch back → position preserved
- [ ] Pin a node, switch to Graph view, switch back → position preserved
- [ ] Pin a node, change filter to "Changed Only", change back → position preserved
- [ ] Pin multiple nodes, unpin one → only unpinned node moves
- [ ] Pin a node, apply iteration → position cleared (expected)
- [ ] Pin a node, refresh page → position lost (expected)

### localStorage Persistence Tests
- [ ] Pin a node, refresh page → position restored
- [ ] Pin a node, close browser, reopen → position restored
- [ ] Pin 100 nodes → no performance issues
- [ ] Clear browser data → positions cleared (expected)
- [ ] Open two tabs → positions sync (may conflict)

### Edge Case Tests
- [ ] Pin a node, delete that class, reload → no errors
- [ ] Pin a node, modify class URI → old position ignored
- [ ] Pin a node at coordinates (0, 0) → still pinned correctly
- [ ] Pin a node, zoom in/out → position scales correctly

---

## Conclusion

**✅ Both session and cross-session persistence are implementable.**

**Recommended path:**
1. **Start with Phase 1 (Session/In-Memory)** - Solves 90% of user needs, low risk, fast implementation
2. **Add Phase 2 (localStorage)** - If user feedback demands it, easy enhancement
3. **Consider Phase 3 (Server)** - Only if multi-device/collaboration is critical

**Next steps:**
1. Review this analysis with the team
2. Get stakeholder approval for Phase 1
3. Implement Phase 1 in ~1 day
4. Deploy and collect user feedback
5. Decide on Phase 2 based on feedback

**Estimated total effort:**
- Phase 1: 4-6 hours
- Phase 2: +2-3 hours
- Phase 3: +16-24 hours + backend work

**Risk level: Low** - All solutions are well-understood patterns with proven implementations.
