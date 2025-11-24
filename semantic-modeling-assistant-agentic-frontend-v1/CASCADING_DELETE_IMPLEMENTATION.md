# Cascading Delete Implementation for Operations

## Overview

This document describes the implementation of cascading delete functionality for operations in the Workbench. When a user attempts to delete a CREATE operation that has dependent operations, the system now identifies all dependencies and requires the user to approve deletion of the entire chain.

## Problem Statement

When users delete a CREATE operation (class, attribute, or relationship), subsequent operations that depend on the created entity become invalid:

- **Deleting a CREATE Class**: Breaks attributes with that domain, relationships using that class, subclasses inheriting from it, and any update/delete operations on that class
- **Deleting a CREATE Attribute**: Breaks any update/delete operations on that attribute
- **Deleting a CREATE Relationship**: Breaks any update/delete operations on that relationship

## Implementation

### 1. Dependency Analysis Function

**Function**: `findDependentOperations(operation, allOperations)`

This function analyzes the operation list and identifies all operations that depend on the given CREATE operation:

#### For CREATE Class operations:
- **Attributes**: Checks `owning_class_uri` matching the class URI
- **Relationships**: Checks `source_class_uri` or `target_class_uri` matching the class URI
- **Subclasses**: Checks if `generalization_uris[]` includes the class URI
- **Updates/Deletes**: Checks if operation URI matches and type is update or delete

#### For CREATE Attribute operations:
- **Updates/Deletes**: Operations targeting the same attribute URI

#### For CREATE Relationship operations:
- **Updates/Deletes**: Operations targeting the same relationship URI

The function only considers operations that appear **after** the CREATE operation in the list, as order matters.

### 2. Delete Handler

**Function**: `handleDeleteOperation(op)`

When user clicks Delete:
1. **For CREATE operations**:
   - Runs dependency analysis
   - If dependencies found: Shows confirmation modal
   - If no dependencies: Simple confirmation dialog and delete
2. **For UPDATE/DELETE operations**:
   - Simple confirmation dialog and delete (no cascading needed)

### 3. Cascading Delete Mutation

**Mutation**: `deleteCascadeMut`

Deletes multiple operations sequentially:
- Processes operations in **reverse order** (dependents first)
- Ensures no orphaned references during deletion
- Refreshes operation list on success

### 4. Confirmation Modal

**Component**: Delete Confirmation Modal with Dependencies

Features:
- ⚠️ Warning banner explaining the cascade
- Shows the operation to be deleted (highlighted in red)
- Lists all dependent operations with:
  - Operation type badges (Create/Update/Delete)
  - Target type (Class/Attribute/Relationship)
  - **Dependency reason** badge explaining why it depends
  - URI and label information
- Total count of operations to be deleted
- Cancel and "Delete All" buttons

#### Dependency Reason Labels:
- "Attribute's domain class"
- "Relationship's source class"
- "Relationship's target class"
- "Parent class in generalization"
- "Updates this class/attribute/relationship"
- "Deletes this class/attribute/relationship"

## User Flow

1. User clicks **Delete** on a CREATE operation
2. System analyzes dependencies
3. **If dependencies exist**:
   - Modal appears showing the operation and all dependents
   - User sees clear warning and dependency reasons
   - User must click "Delete All" to proceed
   - System deletes all operations in cascade
4. **If no dependencies**:
   - Simple confirmation dialog
   - Single operation deleted

## Technical Details

### State Management

```typescript
const [deleteConfirmation, setDeleteConfirmation] = useState<{
  operation: any
  dependentOps: any[]
} | null>(null)
```

### Dependency Check Logic

The function checks these fields for URI references:
- `owning_class_uri` (for attributes)
- `source_class_uri` (for relationships)
- `target_class_uri` (for relationships)
- `generalization_uris[]` (for class inheritance)
- `uri` (for update/delete operations)

### Order Preservation

Operations are processed in order, and only later operations are checked for dependencies. This ensures that the temporal/sequential nature of operations is respected.

## Benefits

1. **Data Integrity**: Prevents orphaned references and broken operation chains
2. **User Awareness**: Users see exactly what will be deleted and why
3. **Safety**: Requires explicit confirmation for cascading deletes
4. **Transparency**: Dependency reasons are clearly labeled
5. **Flexibility**: Non-CREATE operations can still be deleted simply

## Future Enhancements

Potential improvements:
1. Visual dependency graph showing operation relationships
2. Ability to select which dependents to keep/modify
3. Suggest alternative fixes (e.g., updating URIs instead of deleting)
4. Undo/redo for cascading deletes
5. Export dependency report before deletion
