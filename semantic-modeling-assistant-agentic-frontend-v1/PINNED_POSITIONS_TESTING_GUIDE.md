# Testing Guide - Pinned Node Positions

## Quick Test Procedure

### Test 1: Basic Pin/Unpin (30 seconds)
1. Open Force View
2. Drag a node to a new position → Release
3. ✅ Verify: Node has blue halo
4. Right-click the node
5. ✅ Verify: Blue halo disappears, node moves freely

**Expected Console Logs:**
```
📌 Pinned node: http://...class/Person at { x: 425.67, y: 318.92 }
📍 Unpinned node: http://...class/Person
```

---

### Test 2: View Switch Persistence (1 minute)
1. Pin 2-3 nodes in Force View (note their positions)
2. Switch to Grid View → then back to Force View
3. ✅ Verify: Pinned nodes are in same positions with halos
4. Switch to Graph View → then back to Force View
5. ✅ Verify: Pinned nodes still in same positions

**Expected Console Logs:**
```
📍 Restoring 3 pinned positions for project project-123
```

---

### Test 3: Tab Switch Persistence (1 minute)
1. Pin 2-3 nodes in Force View (Ontology tab)
2. Switch to Workbench tab
3. Switch to Compare tab
4. Switch back to Ontology tab → Force View
5. ✅ Verify: Pinned nodes preserved

---

### Test 4: Filter Mode Persistence (1 minute)
1. Pin 2-3 nodes
2. Change filter from "All" → "Changed Only"
3. ✅ Verify: Visible pinned nodes still pinned
4. Change filter back to "All"
5. ✅ Verify: All pinned nodes restored

---

### Test 5: Page Refresh Persistence (1 minute) ⭐ **CRITICAL**
1. Pin 2-3 nodes in distinct positions
2. Press F5 or Ctrl+R to refresh page
3. Navigate back to Ontology → Force View
4. ✅ Verify: Pinned nodes restored to same positions!

**Expected Console Logs:**
```
📍 Restoring 3 pinned positions for project project-123
```

---

### Test 6: Browser Restart Persistence (2 minutes) ⭐ **CRITICAL**
1. Pin 2-3 nodes
2. Note the positions and node names
3. Close browser completely
4. Reopen browser
5. Navigate to Force View
6. ✅ Verify: Pinned nodes restored!

---

### Test 7: Multi-Node Pinning (1 minute)
1. Pin 5-10 nodes in different positions
2. ✅ Verify: All show blue halos
3. Refresh page
4. ✅ Verify: All positions restored

---

### Test 8: Partial Unpinning (1 minute)
1. Pin 5 nodes
2. Unpin 2 of them (right-click)
3. ✅ Verify: 3 remain pinned, 2 move freely
4. Refresh page
5. ✅ Verify: Still 3 pinned, 2 unpinned

---

### Test 9: Project Switching (2 minutes)
**Prerequisites:** Need 2+ projects

1. In Project A: Pin 3 nodes in specific pattern
2. Switch to Project B
3. ✅ Verify: Nodes are unpinned (different project)
4. In Project B: Pin 2 nodes in different pattern
5. Switch back to Project A
6. ✅ Verify: Original 3 nodes pinned in original positions
7. Switch back to Project B
8. ✅ Verify: 2 nodes pinned as expected

---

### Test 10: Iteration Application (2 minutes)
**Prerequisites:** Project with pending operations

1. Pin 3 nodes
2. Apply iteration operations
3. ✅ Verify: Pinned nodes remain pinned (if classes still exist)
4. Refresh page
5. ✅ Verify: Positions still restored

---

### Test 11: Zoom/Pan Independence (30 seconds)
1. Pin a node at specific position
2. Zoom in 2x
3. ✅ Verify: Node stays at same graph position
4. Pan to different area
5. ✅ Verify: Node still at same graph position when scrolled back
6. Reset zoom
7. ✅ Verify: Node at original position

---

### Test 12: localStorage Verification (1 minute)
1. Pin 2-3 nodes
2. Open DevTools (F12) → Console
3. Run: `localStorage.getItem('ontology-node-positions')`
4. ✅ Verify: See JSON with position data
5. Run: `JSON.parse(localStorage.getItem('ontology-node-positions'))`
6. ✅ Verify: Can see position arrays with x, y, timestamp

**Expected Output:**
```javascript
{
  "state": {
    "positions": [
      ["project-123:http://...class/Person", {"x": 425, "y": 318, "timestamp": 1729180800000}],
      ...
    ]
  },
  "version": 1
}
```

---

### Test 13: Auto-Cleanup on Startup (1 minute)
1. Open DevTools Console before loading app
2. Load/refresh the app
3. ✅ Verify: Look for cleanup message
4. ✅ Expected: `🧹 Pruned N old node positions` (if any old positions exist)

---

### Test 14: Performance Test (2 minutes)
1. Pin 20-30 nodes
2. Measure time for page refresh → positions restored
3. ✅ Verify: Restoration happens in < 500ms
4. Check browser console for performance warnings
5. ✅ Verify: No warnings or errors

---

### Test 15: Edge Case - Pin at Origin (30 seconds)
1. Manually drag a node to coordinates near (0, 0)
2. ✅ Verify: Node pins correctly
3. Refresh page
4. ✅ Verify: Position restored at origin

---

## Comprehensive Test Matrix

| Test Case | Action | Expected Result | Status |
|-----------|--------|-----------------|--------|
| Basic pin | Drag node | Blue halo appears, console log | ⬜ |
| Basic unpin | Right-click node | Halo disappears, console log | ⬜ |
| Grid switch | Force→Grid→Force | Positions preserved | ⬜ |
| Graph switch | Force→Graph→Force | Positions preserved | ⬜ |
| Tab switch | Ontology→Workbench→Ontology | Positions preserved | ⬜ |
| Filter "Changed" | Change filter mode | Positions preserved | ⬜ |
| Filter "Connected" | Change filter mode | Positions preserved | ⬜ |
| Page refresh | F5 | Positions restored | ⬜ |
| Browser restart | Close/reopen browser | Positions restored | ⬜ |
| Multi-pin | Pin 10 nodes | All preserved | ⬜ |
| Partial unpin | Unpin some nodes | Only selected unpinned | ⬜ |
| Project A → B | Switch projects | Separate positions | ⬜ |
| Project B → A | Switch back | Original positions | ⬜ |
| Iteration apply | Apply operations | Positions preserved | ⬜ |
| Zoom/pan | Transform viewport | Positions stable | ⬜ |
| localStorage check | Inspect storage | Data present | ⬜ |
| Auto-cleanup | App startup | Old positions pruned | ⬜ |
| 30-node performance | Pin many nodes | Fast restore | ⬜ |
| Origin position | Pin at (0,0) | Works correctly | ⬜ |

---

## Automated Testing Commands

### Check localStorage Size
```javascript
// In browser console
const data = localStorage.getItem('ontology-node-positions')
console.log('Storage size:', data?.length || 0, 'bytes')
console.log('Storage size:', ((data?.length || 0) / 1024).toFixed(2), 'KB')
```

### Count Pinned Positions
```javascript
const store = useNodePositionsStore.getState()
console.log('Total pinned positions:', store.positions.size)
```

### List All Positions
```javascript
const store = useNodePositionsStore.getState()
for (const [key, pos] of store.positions.entries()) {
  console.log(key, '→', pos)
}
```

### Clear All Positions (Manual Test)
```javascript
const store = useNodePositionsStore.getState()
store.clearAll()
// Refresh page to verify all positions cleared
```

### Clear Single Project
```javascript
const store = useNodePositionsStore.getState()
store.clearProject('project-123')
// Refresh page to verify project positions cleared
```

### Manual Prune Test
```javascript
const store = useNodePositionsStore.getState()
// Prune positions older than 1 minute (for testing)
store.pruneOldPositions(60 * 1000)
```

---

## Regression Testing

After any code changes to force view or stores:

### Minimal Regression Suite (5 minutes)
- [ ] Test 1: Basic Pin/Unpin
- [ ] Test 5: Page Refresh Persistence
- [ ] Test 7: Multi-Node Pinning
- [ ] Test 11: Zoom/Pan Independence

### Full Regression Suite (20 minutes)
- [ ] Run all 18 tests above
- [ ] Check console for unexpected errors
- [ ] Verify localStorage data structure
- [ ] Test with 3 different projects

---

## Known Limitations & Expected Behavior

### Not Bugs - Expected Behavior:
1. **Positions cleared when switching projects** - Each project has separate layout
2. **Invalid positions ignored** - If class is deleted, position is discarded
3. **localStorage disabled in incognito** - Browser limitation, use normal mode
4. **Positions lost if browser data cleared** - localStorage is browser storage
5. **Positions expire after 30 days** - Automatic cleanup feature

### Real Bugs to Watch For:
1. ❌ Positions not restored after normal refresh
2. ❌ Multiple halos on same node
3. ❌ Console errors when pinning/unpinning
4. ❌ Positions apply to wrong nodes
5. ❌ Performance degradation with many pins
6. ❌ localStorage size growing indefinitely
7. ❌ Conflict between multiple tabs

---

## Performance Benchmarks

Expected performance metrics:

| Operation | Expected Time | Acceptable Max |
|-----------|---------------|----------------|
| Pin node | < 1ms | < 5ms |
| Unpin node | < 1ms | < 5ms |
| Load 10 positions | < 5ms | < 20ms |
| Load 100 positions | < 10ms | < 50ms |
| Save to localStorage | < 5ms | < 20ms |
| Prune old positions | < 10ms | < 50ms |
| Full page load + restore | < 500ms | < 1000ms |

---

## Bug Report Template

If you find a bug, report with:

```markdown
**Environment:**
- Browser: [Chrome 130, Firefox 131, etc.]
- OS: [Windows 11, macOS 15, etc.]
- Project ID: [if relevant]

**Steps to Reproduce:**
1. 
2. 
3. 

**Expected Behavior:**


**Actual Behavior:**


**Console Errors:**
```paste console output```

**localStorage Data:**
```paste localStorage.getItem('ontology-node-positions')```

**Screenshots/Video:**
[if applicable]
```

---

## Success Criteria

✅ Implementation is successful if:
1. All 18 test cases pass
2. No console errors during normal use
3. Positions persist across page refresh
4. Performance is within acceptable limits
5. localStorage data is well-formed
6. No data loss during typical workflows
7. User feedback is positive

🎉 **Happy Testing!**
