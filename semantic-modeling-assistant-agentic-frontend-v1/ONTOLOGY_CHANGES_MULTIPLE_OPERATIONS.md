# Ontology Changes - Multiple Operations Handling

## Problem Statement
When an iteration contains multiple operations affecting the same ontology element, we need to determine the final change type that should be displayed. The system now correctly handles these scenarios.

## Resolution Rules

### Rule 1: Create + Edit(s) = Created
**Scenario:** Element is created and then edited one or more times.
**Result:** Display as **CREATED** (green)
**Reasoning:** From the user's perspective, the element is new. The edits are just refinements during creation.

**Example:**
```typescript
Operations:
1. CREATE class "Person" with definition "A human"
2. UPDATE class "Person" to add parent class "Agent"
3. UPDATE class "Person" to refine definition

Result: "Person" shown as CREATED ✓
```

### Rule 2: Edit(s) Only = Modified
**Scenario:** Element is only edited (one or more times).
**Result:** Display as **MODIFIED** (yellow)
**Reasoning:** Element already existed and was changed.

**Example:**
```typescript
Operations:
1. UPDATE class "Person" to add attribute "age"
2. UPDATE class "Person" to modify description

Result: "Person" shown as MODIFIED ✓
```

### Rule 3: Edit(s) + Delete = Deleted
**Scenario:** Element is edited and then deleted.
**Result:** Display as **DELETED** (red, faded)
**Reasoning:** The final state is that the element is removed, regardless of interim edits.

**Example:**
```typescript
Operations:
1. UPDATE class "Person" to add attribute
2. UPDATE class "Person" to modify definition
3. DELETE class "Person"

Result: "Person" shown as DELETED ✓
```

### Rule 4: Create + Edit(s) + Delete = No Display
**Scenario:** Element is created, optionally edited, and then deleted.
**Result:** **NOT DISPLAYED** (no net change)
**Reasoning:** Element didn't exist before and doesn't exist after. It was a temporary artifact of the iteration process.

**Example:**
```typescript
Operations:
1. CREATE class "TempHelper"
2. UPDATE class "TempHelper" 
3. DELETE class "TempHelper"

Result: "TempHelper" NOT shown (no net change) ✓
```

## Implementation Details

### Two-Pass Algorithm

**First Pass - Grouping:**
```typescript
// Group operations by element URI
const classOps = new Map<string, OntologyOperationModel[]>()
const attributeOps = new Map<string, OntologyOperationModel[]>()
const relationshipOps = new Map<string, OntologyOperationModel[]>()
```

**Second Pass - Resolution:**
```typescript
const resolveFinalChangeType = (ops: OntologyOperationModel[]): ChangeType | null => {
  const hasCreate = ops.some(op => op.operation_type === 'create')
  const hasDelete = ops.some(op => op.operation_type === 'delete')
  const hasUpdate = ops.some(op => op.operation_type === 'update')

  // Apply rules in priority order
  if (hasCreate && hasDelete) return null        // Rule 4
  if (hasDelete) return 'deleted'                // Rule 3
  if (hasCreate) return 'created'                // Rule 1
  if (hasUpdate) return 'modified'               // Rule 2
  
  return null
}
```

## Special Handling

### Inheritance Relationships
When a class has multiple operations, inheritance relationships use the change type of the class:
- If class is **created**, its inheritances are shown as **created**
- If class is **modified**, its inheritances are shown as **modified**
- If class is **deleted**, its inheritances are shown as **deleted**

We use the **last operation** that defines generalization URIs to determine which inheritance relationships to track.

### Attributes & Relationships
Follow the same resolution rules as classes. Each element type is processed independently.

## Examples by View

### Grid View
- Created: Green background with left border, "NEW" badge
- Modified: Yellow background with left border, "MODIFIED" badge
- Deleted: Red background with left border, "DELETED" badge, reduced opacity
- No net change: Element not displayed at all

### Graph View
- Created: Green border, green header background, "NEW" badge, animated edges
- Modified: Yellow border, yellow header background, "MOD" badge
- Deleted: Red border, red header background, "DEL" badge, reduced opacity
- No net change: Element not displayed at all

### Force View
- Created: Green halo around node, thickened green edges
- Modified: Yellow halo around node, thickened yellow edges
- Deleted: Red halo around node, reduced opacity
- No net change: Element not displayed at all

## Debug Logging

The system logs:
1. Each operation as it's being processed
2. Final change type determination with operation count
3. Elements that have no net change (created then deleted)
4. Summary of all tracked changes by type

## Benefits

1. **Correct Semantics**: Change indicators accurately reflect the net effect on the ontology
2. **Cleaner Display**: Temporary elements (created then deleted) don't clutter the view
3. **User Intent**: Reflects what users care about - the final outcome, not intermediate steps
4. **Consistent Logic**: Same rules apply to all element types (classes, attributes, relationships)
