# Workbench Page Analysis & Implementation Plan

## Current State

The Workbench page currently shows:
- **Left Panel**: List of areas with "+ Add Area" button
- **Right Panel**: Three placeholder sections (Area, Iteration, Tasks)

## Expected Behavior (Based on Specification)

### Overview
The Workbench is an **expert edit mode** with a **master-detail interface**:
- **Left Tree**: Selectable list of Areas and Iterations (hierarchical)
- **Main Panel**: Context-sensitive tabs that change based on selection
- **Right Panel**: Details, AI assistance, History (mentioned in spec but not fully detailed)

### Expected User Flow

```
1. User clicks "✨ Suggest" button in tree header
   ↓
2. Modal opens with:
   - Focused Area selector (defaults to currently selected area)
   - Number of iterations (1-20, default 5)
   - Custom instructions (optional)
   - [Generate Iterations] button
   
3. User selects an Area from left tree
   ↓
4. Main panel shows "Area Detail View" (Read-only):
   - Label, Description, Parent area, Key Concepts
   - [✏️ Edit] button to enter edit mode
   - [✨ Reidentify Areas] with custom instructions
   
5. User clicks "Edit" button
   ↓
6. Main panel switches to "Area Edit Form":
   - Editable: Label, Description, Parent area selector, Key Concepts
   - [Save] [Cancel] [Delete] buttons
   
7. User selects an Iteration from left tree
   ↓
8. Main panel switches to "Iteration Tab" with:
   - Name, Status, Focused Area
   - Specification (multiline textarea)
   - [Save] [Check Coverage] [Prepare ▶] buttons
   
9. User clicks "View Tasks" on iteration
   ↓
10. Main panel switches to "Tasks Tab" with:
   - [✨ Plan Tasks] [+ Add Task] [Reorder] toolbar
   - List of tasks with edit/delete actions
```

## What Should Be Implemented

### 1. Left Tree Panel (Enhanced)

**Current:**
```tsx
<div className="bg-white border rounded-card p-3">
  <div className="font-semibold">Areas</div>
  <ul>
    {areasQ.data?.map((a) => (
      <li>{a.label}</li>
    ))}
  </ul>
</div>
```

**Should Be:**
```tsx
<div className="bg-white border rounded-card p-3">
  {/* Header with Add buttons */}
  <div className="flex gap-2 mb-3">
    <button>[+ Add Area]</button>
    <button>[+ Iteration]</button>
  </div>
  
  {/* Hierarchical tree */}
  {areasQ.data?.map((area) => (
    <div>
      {/* Area item - clickable */}
      <div 
        onClick={() => selectArea(area.id)}
        className={selected ? 'bg-blue-100' : ''}
      >
        ▼ {area.label}
      </div>
      
      {/* Nested iterations for this area */}
      {iterationsForArea(area.id).map((iteration) => (
        <div 
          onClick={() => selectIteration(iteration.id)}
          className="pl-4"
        >
          • {iteration.name}
        </div>
      ))}
    </div>
  ))}
</div>
```

### 2. Main Panel (Tab System)

**Should switch between 3 modes based on selection:**

#### Mode 1: Area Tab (when area is selected)
```tsx
<div className="bg-white border rounded-card p-4">
  <h2>Edit Area</h2>
  
  <label>Label</label>
  <input value={area.label} />
  
  <label>Description</label>
  <textarea value={area.description} />
  
  <label>Parent Area</label>
  <select>
    <option>None</option>
    {/* Other areas except current */}
  </select>
  
  <label>Key Concepts</label>
  <TagInput value={area.key_concepts} />
  
  <div className="flex gap-2">
    <button>Save</button>
    <button>Delete</button>
    <button className="bg-ai">Reidentify ✨</button>
  </div>
</div>
```

#### Mode 2: Iteration Tab (when iteration is selected)
```tsx
<div className="bg-white border rounded-card p-4">
  <div className="flex justify-between">
    <h2>{iteration.name} ✏️</h2>
    <span className="chip">{iteration.status}</span>
  </div>
  
  <div>Focused Area: <a href="#">{areaName}</a></div>
  
  <label>Specification</label>
  <textarea value={iteration.specification} rows={6} />
  
  <div className="flex gap-2">
    <button>Save</button>
    <button>Check Coverage</button>
    <button className="bg-primary">Prepare ▶</button>
  </div>
</div>
```

#### Mode 3: Tasks Tab (when iteration selected + tasks view)
```tsx
<div className="bg-white border rounded-card p-4">
  <div className="toolbar flex gap-2 mb-4">
    <button className="bg-ai">✨ Plan Tasks</button>
    <button>+ Add Task</button>
    <button>Reorder</button>
  </div>
  
  <ul>
    {tasks.map((task) => (
      <li className="flex justify-between border-b py-2">
        <div>
          <span className="font-medium">{task.name}</span>
          {task.aiGenerated && <span className="badge">AI</span>}
          <p className="text-sm text-gray-600">{task.specification}</p>
        </div>
        <div className="flex gap-2">
          <button>Edit</button>
          <button>Delete</button>
        </div>
      </li>
    ))}
  </ul>
</div>
```

### 3. State Management Requirements

The **projectStore** already has the necessary state:
- `areaId` - Currently selected area
- `iterationId` - Currently selected iteration  
- `taskId` - Currently selected task (for future use)

**Usage:**
```tsx
const { projectId, areaId, iterationId, setAreaId, setIterationId } = useProjectStore()

// Determine which tab to show
const activeTab = iterationId && tasksView ? 'tasks' 
                : iterationId ? 'iteration'
                : areaId ? 'area'
                : null
```

### 4. API Integration

**Required queries:**
```tsx
// Get selected area details
const areaQ = useQuery({
  enabled: !!projectId && !!areaId,
  queryKey: ['area', projectId, areaId],
  queryFn: () => api.getArea(projectId, areaId)
})

// Get selected iteration details
const iterationQ = useQuery({
  enabled: !!projectId && !!iterationId,
  queryKey: ['iteration', projectId, iterationId],
  queryFn: () => api.getIteration(projectId, iterationId)
})

// Get tasks for selected iteration
const tasksQ = useQuery({
  enabled: !!projectId && !!iterationId,
  queryKey: ['tasks', projectId, iterationId],
  queryFn: () => api.listTasks(projectId, iterationId)
})

// Get iterations filtered by area (for left tree)
const iterationsQ = useQuery({
  enabled: !!projectId && !!areaId,
  queryKey: ['iterations', projectId, areaId],
  queryFn: () => api.listIterations(projectId, areaId)
})
```

**Required mutations:**
```tsx
// Area operations
updateArea: PUT /api/projects/{id}/domain-areas/{area_id}
deleteArea: DELETE /api/projects/{id}/domain-areas/{area_id}
createArea: POST /api/projects/{id}/domain-areas

// Iteration operations
updateIteration: PUT /api/projects/{id}/iterations/{iteration_id}

// Task operations
createTask: POST /api/projects/{id}/iterations/{iteration_id}/tasks
updateTask: PUT /api/projects/{id}/iterations/{iteration_id}/tasks/{task_id}
deleteTask: DELETE /api/projects/{id}/iterations/{iteration_id}/tasks/{task_id}
```

## Implementation Priority

### Phase 1: Left Tree Enhancement
1. ✅ Make area items clickable (already has onClick in current code)
2. Add visual selection state (highlight selected area/iteration)
3. Fetch and display iterations nested under each area
4. Add expand/collapse for area children

### Phase 2: Area Tab
1. Load area details when `areaId` is set
2. Create form with Label, Description, Parent, Key Concepts
3. Implement Save mutation
4. Implement Delete mutation (with confirmation)
5. Add Reidentify ✨ button (already exists, just needs proper placement)

### Phase 3: Iteration Tab
1. Load iteration details when `iterationId` is set
2. Create form with Name, Status, Focused Area, Specification
3. Implement Save mutation
4. Add "Check Coverage" functionality (TBD - what does this do?)
5. Add "Prepare ▶" button (should trigger prepare mutation and open operations modal)

### Phase 4: Tasks Tab
1. Add tab/view switcher when iteration is selected
2. Load tasks list
3. Implement "Plan Tasks ✨" modal
4. Implement "Add Task" functionality
5. Implement task edit/delete
6. Add drag-drop reordering

## Key Differences from Storyboard

| Aspect | Storyboard | Workbench |
|--------|-----------|-----------|
| **Purpose** | High-level workflow visualization | Detailed editing |
| **Layout** | 4-column Kanban board | Master-detail with tabs |
| **Selection** | Click to expand cards | Click to edit in detail |
| **Area Filter** | Dropdown at top | Tree navigation on left |
| **Iteration View** | Cards grouped by status | Full form for selected item |
| **Task View** | Modal popup | Dedicated tab with full CRUD |
| **Operations** | Quick actions on cards | Full form editing |

## Summary

**Current Issue:**
The Workbench page shows static placeholder sections because:
1. No area/iteration is selected (areaId and iterationId are null)
2. No conditional rendering based on selection state
3. No queries to fetch selected item details
4. No forms to edit the selected items

**What Needs to Happen:**
1. User clicks an area in the left tree → `setAreaId(area.id)`
2. Main panel detects `areaId !== null` → shows Area editing form
3. User clicks an iteration in the left tree → `setIterationId(iteration.id)`
4. Main panel detects `iterationId !== null` → shows Iteration editing form
5. User clicks "Tasks" (or auto-show) → shows Tasks list and editing

**The placeholders are there because nothing is selected yet!**
