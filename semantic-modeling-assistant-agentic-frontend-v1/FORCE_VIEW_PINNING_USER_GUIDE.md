# Force View - Pinned Node Positions User Guide

## Quick Start

### How to Pin a Node
1. Click and **drag** any node to your desired position
2. **Release** the mouse button
3. ✨ The node is automatically pinned!
4. You'll see a **blue halo** around pinned nodes

### How to Unpin a Node
1. **Right-click** on a pinned node
2. The node unpins and starts moving freely again
3. The blue halo disappears

## Visual Indicators

```
┌─────────────────────────────────────┐
│  Unpinned Node (moves freely)       │
│     ╭─────╮                          │
│     │ Person │  ← No halo            │
│     ╰─────╯                          │
│                                      │
│  Pinned Node (fixed position)       │
│     ╭───────────╮                    │
│    │  ╭─────╮  │                     │
│    │  │ Person │  │ ← Blue halo      │
│    │  ╰─────╯  │                     │
│     ╰───────────╯                    │
└─────────────────────────────────────┘
```

## What Persists

✅ **Pinned positions survive:**
- Switching between Grid/Graph/Force views
- Switching to other tabs (Workbench, Compare, etc.)
- Changing filter modes (All/Changed/Connected)
- Applying iteration operations
- **Page refresh** (saved in browser!)
- **Browser restart** (saved in browser!)

❌ **Pinned positions are cleared when:**
- Switching to a different project
- Clearing browser data/cookies
- After 30 days of inactivity (automatic cleanup)

## Tips & Tricks

### 📐 Create Your Perfect Layout
1. **Start with important nodes**: Pin central/hub classes first
2. **Work outward**: Pin connected nodes around them
3. **Leave some unpinned**: Let peripheral nodes flow naturally
4. **Use symmetry**: Create balanced, aesthetically pleasing layouts

### 🎯 Efficient Workflow
- **Don't pin everything**: Only pin 10-20 key nodes for structure
- **Let D3 do the work**: Unpinned nodes will find good positions automatically
- **Iterate**: Pin, observe, adjust, unpin, repeat

### 🔍 Finding the Right Position
- **Drag slowly**: Take time to find the optimal spot
- **Use relationships**: Place related classes near each other
- **Consider hierarchy**: Place parent classes above children
- **Think about flow**: Arrange nodes to minimize edge crossing

### 🚀 Power User Features
- **Quick unpin**: Right-click is faster than dragging back
- **Multi-project layouts**: Each project has its own saved layout
- **Persistent across iterations**: Your layout survives ontology updates
- **Works with filtering**: Pinned nodes stay pinned even when filtered

## Common Scenarios

### Scenario 1: Creating a Hierarchical Layout
```
Step 1: Pin root class at top
Step 2: Pin child classes below in a row
Step 3: Let grandchildren flow naturally
Result: Clear top-down hierarchy
```

### Scenario 2: Circular Layout
```
Step 1: Pin central "hub" class in center
Step 2: Pin related classes in a circle around it
Step 3: Let secondary connections flow
Result: Hub-and-spoke structure
```

### Scenario 3: Domain Separation
```
Step 1: Pin key classes from Domain A on left
Step 2: Pin key classes from Domain B on right
Step 3: Let connecting classes position between
Result: Clear domain boundaries
```

### Scenario 4: Iteration-Safe Layout
```
Step 1: Create layout in Iteration 1
Step 2: Apply operations (add/modify classes)
Step 3: Your pinned nodes stay in place!
Result: Consistent layout across iterations
```

## Troubleshooting

### My pinned nodes moved!
**Cause:** You may have switched projects
**Fix:** Each project has separate saved positions. Switch back to see your layout.

### Positions not saving after refresh
**Cause:** Browser's localStorage may be disabled
**Fix:** Check browser settings, disable "incognito mode", or check extensions blocking storage.

### Too many pinned nodes, layout feels cluttered
**Fix:** Right-click to unpin non-essential nodes. Aim for 10-20 pinned nodes max.

### Can't find a pinned node
**Fix:** It might be filtered out. Change filter to "All Elements" to see all nodes.

### Want to reset entire layout
**Fix:** Right-click each pinned node to unpin, or switch projects and back to reload.

## Keyboard Shortcuts

Currently available mouse interactions:
- **Left-click + drag**: Move and pin node
- **Right-click**: Unpin node
- **Mouse wheel**: Zoom in/out
- **Left-click background + drag**: Pan view
- **Left-click node**: Select node

## Technical Details

### Storage Information
- **Where:** Browser localStorage (`ontology-node-positions`)
- **Scope:** Per project (different projects = different layouts)
- **Size:** ~80 bytes per pinned node
- **Capacity:** ~62,500 nodes (you'll never hit this limit!)
- **Cleanup:** Positions older than 30 days auto-deleted

### Position Coordinates
- Stored in **graph coordinates** (not screen pixels)
- Zoom/pan doesn't affect positions
- Pinned nodes stay in same absolute position

### Privacy & Security
- All data stored **locally** in your browser
- Nothing sent to server
- No tracking or analytics
- Cleared when you clear browser data

## Best Practices

### ✅ Do:
- Pin important, frequently-referenced nodes
- Create layouts that minimize edge crossings
- Use symmetry for aesthetic appeal
- Save time by reusing layouts across sessions
- Experiment with different arrangements

### ❌ Don't:
- Pin every single node (defeats the purpose!)
- Create random, chaotic layouts
- Forget to unpin nodes when you change your mind
- Worry about "perfect" placement (iterative improvement is fine!)

## FAQ

**Q: How many nodes can I pin?**
A: Technically 62,500, practically 10-50 for best results.

**Q: Do teammates see my pinned layout?**
A: No, layouts are stored locally. Each user has their own.

**Q: Can I export/import layouts?**
A: Not yet, but it's a potential future enhancement!

**Q: What happens to pinned positions when I delete a class?**
A: The position is ignored (silently). If class is restored, position is restored.

**Q: Can I pin the same node in multiple projects?**
A: Yes! Each project stores separate positions for the same node URI.

**Q: Do positions work in Grid or Graph views?**
A: No, pinning is specific to Force View. Grid and Graph have their own layouts.

**Q: Is there a limit to localStorage?**
A: Yes (~5-10MB), but you'll never hit it. 10,000 pinned nodes = ~800KB.

## Getting Help

If you encounter issues:
1. Check browser console for error messages (F12)
2. Look for console logs: `📌 Pinned node:` or `📍 Restoring positions`
3. Try clearing and re-pinning a single node to test
4. Check if localStorage is enabled in your browser
5. Report bugs with browser version and reproduction steps

## Future Features (Planned)

Potential enhancements:
- 🎨 UI panel showing all pinned nodes
- 💾 Export/import layouts as JSON files
- 🔄 Reset button to clear all pins for current project
- 📊 Statistics (number of pinned nodes, storage used)
- 🎯 Snap-to-grid for precise alignment
- 👥 Share layouts with team members (requires backend)

---

**Enjoy creating beautiful, persistent ontology layouts! 🎨✨**
