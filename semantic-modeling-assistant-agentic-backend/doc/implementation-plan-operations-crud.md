# Implementation Plan: CRUD Operations for Iteration Operations

## Overview
Transform iteration operations from transient value objects to managed entities with full CRUD capabilities, following the same API patterns used for tasks.

**Goal**: Users should be able to reorder, update, and delete individual operations just like they can with tasks.

## Current State vs Target State

### Current State
- Operations are frozen dataclasses without IDs
- Operations identified by list position (index-based)
- Filter endpoint is client-side only
- Operations are stored in `List[OntologyEditOperation]`

### Target State
- Operations are identifiable entities with unique IDs
- Operations support reorder/update/delete via API
- Endpoints follow task CRUD pattern
- Operations maintain immutability where appropriate

## Implementation Steps

### Phase 1: Domain Model Changes

#### 1.1 Create Operation Wrapper Entity
**File**: `src/design_project/domain.py`

Add a new dataclass to wrap operations with identity:

```python
@dataclass
class IdentifiedOperation:
    """
    Wrapper for OntologyEditOperation that adds identity for CRUD operations.
    
    This wrapper allows operations to be managed as entities during the prepare-review-apply
    workflow while keeping the underlying OntologyEditOperation immutable.
    """
    id: str                                    # Unique identifier for this operation instance
    operation: OntologyEditOperation           # The actual operation (immutable value object)
    created_from_task_id: Optional[str]        # ID of the task that generated this operation (for traceability)
```

**Rationale**: 
- Separates identity concerns from operation data
- Keeps `OntologyEditOperation` immutable (frozen dataclass)
- Allows tracking which task generated each operation

#### 1.2 Update DesignIteration
**File**: `src/design_project/domain.py`

Change the type of `plannedOperations`:

```python
@dataclass
class DesignIteration:
    # ... existing fields ...
    
    plannedOperations: Optional[List[IdentifiedOperation]]  # Changed from List[OntologyEditOperation]
    # The list of planned ontology edit operations generated during prepare phase.
    # Each operation has a unique ID for CRUD management.
    # Set to None initially, populated by prepare_planned_iteration(), cleared after apply.
```

### Phase 2: API Model Changes

#### 2.1 Add ID to OntologyOperationModel
**File**: `src/api/models.py`

Update the model to include an ID field:

```python
class OntologyOperationModel(BaseModel):
    """
    Ontology edit operation - complete representation with identity.
    """
    id: str  # NEW: Unique identifier for this operation instance
    operation_type: Literal["create", "update", "delete"]
    target_type: Literal["class", "attribute", "relationship"]
    
    # Required for all operations
    uri: str
    
    # ... rest of fields remain unchanged ...
```

#### 2.2 Add Request Models for CRUD Operations
**File**: `src/api/models.py`

Add new request models following the task pattern:

```python
class ReorderOperationsRequest(BaseModel):
    """Request to reorder operations within an iteration."""
    operation_ids: List[str]


class UpdateOperationRequest(BaseModel):
    """Request to update an operation."""
    # All fields optional - only provided fields are updated
    operation_type: Optional[Literal["create", "update", "delete"]] = None
    target_type: Optional[Literal["class", "attribute", "relationship"]] = None
    uri: Optional[str] = None
    label: Optional[str] = None
    definition: Optional[str] = None
    description: Optional[str] = None
    definition_references: Optional[List[str]] = None
    specification_references: Optional[List[str]] = None
    references: Optional[List[str]] = None
    
    # Class-specific fields
    kind: Optional[str] = None
    generalization_uris: Optional[List[str]] = None
    
    # Attribute-specific fields
    owning_class_uri: Optional[str] = None
    
    # Relationship-specific fields
    source_class_uri: Optional[str] = None
    target_class_uri: Optional[str] = None
```

#### 2.3 Remove FilterOperationsRequest
**File**: `src/api/models.py`

Remove the obsolete `FilterOperationsRequest` class as it will be replaced by delete operations.

### Phase 3: Controller Helper Functions

#### 3.1 Update Conversion Functions
**File**: `src/api/controllers/design_project_controller.py`

Update `_convert_operation_to_model` to include ID:

```python
def _convert_operation_to_model(identified_op: IdentifiedOperation) -> OntologyOperationModel:
    """
    Convert domain IdentifiedOperation to API model.
    
    This function performs a complete mapping including the operation ID.
    """
    operation = identified_op.operation
    
    # Determine operation type
    op_type = operation.operation_type.value
    
    # Create base model with ID
    base_fields = {
        'id': identified_op.id,  # NEW: Include the operation ID
        'operation_type': op_type,
        'uri': str(operation.uri),
    }
    
    # ... rest of conversion logic (existing code) ...
```

Update `_convert_model_to_operation` to return `IdentifiedOperation`:

```python
def _convert_model_to_identified_operation(model: OntologyOperationModel) -> IdentifiedOperation:
    """
    Convert API model to domain IdentifiedOperation.
    
    This allows operations sent from frontend to be applied with their IDs preserved.
    """
    from ontology.edit_operations import (
        CreateClassOperation, UpdateClassOperation, DeleteClassOperation,
        # ... other imports ...
    )
    from rdflib import URIRef
    
    # Create the underlying operation (existing logic)
    operation = _create_operation_from_model(model)  # Extract existing logic to helper
    
    # Wrap with identity
    return IdentifiedOperation(
        id=model.id,
        operation=operation,
        created_from_task_id=None  # Not tracked when coming from API
    )


def _create_operation_from_model(model: OntologyOperationModel) -> OntologyEditOperation:
    """
    Helper to create operation from model (existing logic extracted).
    """
    # ... existing conversion logic from _convert_model_to_operation ...
```

### Phase 4: Service Layer Changes

#### 4.1 Update prepare_planned_iteration
**File**: `src/design_project/service.py`

Modify to generate `IdentifiedOperation` instances:

```python
def prepare_planned_iteration(self, project_id: str, iteration_id: str) -> List[IdentifiedOperation]:
    """
    Prepares a planned design iteration by generating operations for all tasks.
    
    Returns:
        List of IdentifiedOperation instances with unique IDs
    """
    # ... existing validation logic ...
    
    all_operations: List[IdentifiedOperation] = []
    
    # Process each task
    for task in all_tasks:
        logger.info(f"... generating operations for task: {task.id} ({task.name})")
        
        # Status transition: PLANNED -> GENERATING_OPERATIONS
        task.status = DesignTaskStatus.GENERATING_OPERATIONS
        self.save_project(project)
        
        # Generate operations for this task
        task_operations = self._generate_operations_for_task(project, iteration, task)
        
        # Wrap each operation with identity
        for operation in task_operations:
            identified_op = IdentifiedOperation(
                id=str(uuid.uuid4()),  # Generate unique ID
                operation=operation,
                created_from_task_id=task.id  # Track which task created this
            )
            all_operations.append(identified_op)
        
        # Status transition: GENERATING_OPERATIONS -> OPERATIONS_GENERATED
        task.status = DesignTaskStatus.OPERATIONS_GENERATED
    
    # ... rest of existing logic ...
    
    return all_operations
```

#### 4.2 Update apply_current_iteration_changes
**File**: `src/design_project/service.py`

Update to work with `IdentifiedOperation`:

```python
def apply_current_iteration_changes(
    self,
    project_id: str,
    operations: Optional[List[IdentifiedOperation]] = None
) -> Ontology:
    """
    Apply operations to ontology.
    
    Args:
        operations: Optional list of IdentifiedOperations. If None, uses persisted operations.
    """
    # ... existing validation ...
    
    # Get operations to apply
    if operations is not None:
        ops_to_apply = operations
    else:
        if iteration.plannedOperations is None:
            raise ValueError("No operations available to apply")
        ops_to_apply = iteration.plannedOperations
    
    # Extract the actual operations from the wrappers
    actual_operations = [identified_op.operation for identified_op in ops_to_apply]
    
    # Apply operations
    for operation in actual_operations:
        self.ontology_service.apply_operation(project.designedOntology, operation)
    
    # ... rest of existing logic ...
```

#### 4.3 Add Service Methods for CRUD Operations
**File**: `src/design_project/service.py`

Add new service methods:

```python
def reorder_iteration_operations(
    self,
    project_id: str,
    iteration_id: str,
    operation_ids: List[str]
) -> None:
    """
    Reorder operations within the current iteration.
    
    Args:
        project_id: The project ID
        iteration_id: The iteration ID (must be current iteration)
        operation_ids: List of operation IDs in desired order
        
    Raises:
        ValueError: If iteration is not current or not in correct state
        ValueError: If any operation ID is invalid
    """
    project = self.load_project(project_id)
    
    if not project.currentIteration or project.currentIteration.id != iteration_id:
        raise ValueError(f"Iteration {iteration_id} is not the current iteration")
    
    if project.currentIteration.status != DesignIterationStatus.OPERATIONS_GENERATED:
        raise ValueError(f"Cannot reorder operations in status: {project.currentIteration.status}")
    
    if project.currentIteration.plannedOperations is None:
        raise ValueError("No operations to reorder")
    
    # Validate all IDs exist
    existing_ids = {op.id for op in project.currentIteration.plannedOperations}
    for op_id in operation_ids:
        if op_id not in existing_ids:
            raise ValueError(f"Operation with ID '{op_id}' not found")
    
    # Validate all operations are included (no additions/removals)
    if set(operation_ids) != existing_ids:
        raise ValueError("Operation IDs must match existing operations exactly")
    
    # Reorder
    id_to_operation = {op.id: op for op in project.currentIteration.plannedOperations}
    project.currentIteration.plannedOperations = [id_to_operation[op_id] for op_id in operation_ids]
    
    self.save_project(project)


def update_iteration_operation(
    self,
    project_id: str,
    iteration_id: str,
    operation_id: str,
    updated_operation: OntologyEditOperation
) -> IdentifiedOperation:
    """
    Update a specific operation within the current iteration.
    
    Args:
        project_id: The project ID
        iteration_id: The iteration ID (must be current iteration)
        operation_id: The ID of the operation to update
        updated_operation: The new operation data
        
    Returns:
        The updated IdentifiedOperation
        
    Raises:
        ValueError: If iteration is not current or not in correct state
        ValueError: If operation ID is not found
    """
    project = self.load_project(project_id)
    
    if not project.currentIteration or project.currentIteration.id != iteration_id:
        raise ValueError(f"Iteration {iteration_id} is not the current iteration")
    
    if project.currentIteration.status != DesignIterationStatus.OPERATIONS_GENERATED:
        raise ValueError(f"Cannot update operations in status: {project.currentIteration.status}")
    
    if project.currentIteration.plannedOperations is None:
        raise ValueError("No operations to update")
    
    # Find and update the operation
    for i, identified_op in enumerate(project.currentIteration.plannedOperations):
        if identified_op.id == operation_id:
            # Create new IdentifiedOperation with updated operation but same ID
            updated_identified_op = IdentifiedOperation(
                id=identified_op.id,
                operation=updated_operation,
                created_from_task_id=identified_op.created_from_task_id
            )
            project.currentIteration.plannedOperations[i] = updated_identified_op
            self.save_project(project)
            return updated_identified_op
    
    raise ValueError(f"Operation with ID '{operation_id}' not found")


def delete_iteration_operation(
    self,
    project_id: str,
    iteration_id: str,
    operation_id: str
) -> None:
    """
    Delete a specific operation from the current iteration.
    
    Args:
        project_id: The project ID
        iteration_id: The iteration ID (must be current iteration)
        operation_id: The ID of the operation to delete
        
    Raises:
        ValueError: If iteration is not current or not in correct state
        ValueError: If operation ID is not found
    """
    project = self.load_project(project_id)
    
    if not project.currentIteration or project.currentIteration.id != iteration_id:
        raise ValueError(f"Iteration {iteration_id} is not the current iteration")
    
    if project.currentIteration.status != DesignIterationStatus.OPERATIONS_GENERATED:
        raise ValueError(f"Cannot delete operations in status: {project.currentIteration.status}")
    
    if project.currentIteration.plannedOperations is None:
        raise ValueError("No operations to delete")
    
    # Find and remove the operation
    original_count = len(project.currentIteration.plannedOperations)
    project.currentIteration.plannedOperations = [
        op for op in project.currentIteration.plannedOperations if op.id != operation_id
    ]
    
    if len(project.currentIteration.plannedOperations) == original_count:
        raise ValueError(f"Operation with ID '{operation_id}' not found")
    
    self.save_project(project)
```

### Phase 5: Controller Endpoints

#### 5.1 Remove Filter Endpoint
**File**: `src/api/controllers/design_project_controller.py`

Delete the `filter_operations` endpoint (lines ~1937-1960).

#### 5.2 Add Reorder Endpoint
**File**: `src/api/controllers/design_project_controller.py`

Add new endpoint (following task pattern):

```python
@router.put("/projects/{project_id}/iterations/{iteration_id}/operations/reorder", response_model=SuccessResponse)
async def reorder_operations(project_id: str, iteration_id: str, request: ReorderOperationsRequest):
    """
    Reorder operations within the current iteration.
    
    User Story: Edit materialized operations for an iteration
    
    This endpoint allows users to change the order in which operations will be applied
    to the ontology. This is useful when operation order matters for semantic correctness
    (e.g., creating a class before creating its attributes).
    
    Note: This endpoint must be defined BEFORE the update_operation endpoint to avoid
    FastAPI matching "reorder" as an operation_id parameter.
    """
    try:
        logger.info(f"Reordering operations for iteration: {iteration_id} in project: {project_id}")
        
        design_project_service.reorder_iteration_operations(
            project_id=project_id,
            iteration_id=iteration_id,
            operation_ids=request.operation_ids
        )
        
        return SuccessResponse(
            success=True,
            message=f"Reordered {len(request.operation_ids)} operations"
        )
    
    except ValueError as e:
        logger.error(f"Invalid request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found"
        )
    except Exception as e:
        logger.error(f"Error reordering operations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reorder operations: {str(e)}"
        )
```

#### 5.3 Add Update Endpoint
**File**: `src/api/controllers/design_project_controller.py`

Add new endpoint:

```python
@router.put("/projects/{project_id}/iterations/{iteration_id}/operations/{operation_id}", response_model=OntologyOperationModel)
async def update_operation(
    project_id: str,
    iteration_id: str,
    operation_id: str,
    request: UpdateOperationRequest
):
    """
    Update a specific operation within the current iteration.
    
    User Story: Edit materialized operations for an iteration
    
    This endpoint allows users to modify the details of a generated operation before
    applying it to the ontology. Users can change labels, definitions, references, etc.
    """
    try:
        logger.info(f"Updating operation: {operation_id} for iteration: {iteration_id} in project: {project_id}")
        
        # Load current operation
        project = design_project_service.load_project(project_id)
        
        if not project.currentIteration or project.currentIteration.id != iteration_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Iteration {iteration_id} is not the current iteration"
            )
        
        if not project.currentIteration.plannedOperations:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No operations found"
            )
        
        # Find the operation
        identified_op = next(
            (op for op in project.currentIteration.plannedOperations if op.id == operation_id),
            None
        )
        
        if not identified_op:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Operation with ID '{operation_id}' not found"
            )
        
        # Build updated operation by applying changes to existing operation
        updated_operation = _apply_operation_updates(identified_op.operation, request)
        
        # Update through service
        updated_identified_op = design_project_service.update_iteration_operation(
            project_id=project_id,
            iteration_id=iteration_id,
            operation_id=operation_id,
            updated_operation=updated_operation
        )
        
        return _convert_operation_to_model(updated_identified_op)
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Invalid request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found"
        )
    except Exception as e:
        logger.error(f"Error updating operation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update operation: {str(e)}"
        )


def _apply_operation_updates(
    existing_operation: OntologyEditOperation,
    updates: UpdateOperationRequest
) -> OntologyEditOperation:
    """
    Helper to apply updates to an operation, creating a new instance.
    
    Since operations are immutable, this creates a new operation with updated fields.
    """
    from ontology.edit_operations import (
        CreateClassOperation, UpdateClassOperation, DeleteClassOperation,
        CreateAttributeOperation, UpdateAttributeOperation, DeleteAttributeOperation,
        CreateRelationshipOperation, UpdateRelationshipOperation, DeleteRelationshipOperation
    )
    from ontology.domain import Kind
    from rdflib import URIRef
    
    # Determine operation type and create updated instance
    # This is complex because we need to handle all operation types
    # and preserve fields that aren't being updated
    
    if isinstance(existing_operation, CreateClassOperation):
        return CreateClassOperation(
            uri=URIRef(updates.uri) if updates.uri is not None else existing_operation.uri,
            label=updates.label if updates.label is not None else existing_operation.label,
            kind=Kind(updates.kind) if updates.kind is not None else existing_operation.kind,
            definition=updates.definition if updates.definition is not None else existing_operation.definition,
            description=updates.description if updates.description is not None else existing_operation.description,
            generalization_uris=[URIRef(u) for u in updates.generalization_uris] if updates.generalization_uris is not None else existing_operation.generalization_uris,
            definition_references=updates.definition_references if updates.definition_references is not None else existing_operation.definition_references,
            specification_references=updates.specification_references if updates.specification_references is not None else existing_operation.specification_references,
            references=updates.references if updates.references is not None else existing_operation.references
        )
    
    # ... similar logic for all other operation types ...
    # (UpdateClassOperation, DeleteClassOperation, CreateAttributeOperation, etc.)
    
    raise ValueError(f"Unknown operation type: {type(existing_operation)}")
```

#### 5.4 Add Delete Endpoint
**File**: `src/api/controllers/design_project_controller.py`

Add new endpoint:

```python
@router.delete("/projects/{project_id}/iterations/{iteration_id}/operations/{operation_id}", response_model=SuccessResponse)
async def delete_operation(project_id: str, iteration_id: str, operation_id: str):
    """
    Delete a specific operation from the current iteration.
    
    User Story: Edit materialized operations for an iteration
    
    This endpoint allows users to remove unwanted operations before applying
    changes to the ontology. This is useful when AI generates operations that
    the user determines are incorrect or unnecessary.
    """
    try:
        logger.info(f"Deleting operation: {operation_id} for iteration: {iteration_id} in project: {project_id}")
        
        design_project_service.delete_iteration_operation(
            project_id=project_id,
            iteration_id=iteration_id,
            operation_id=operation_id
        )
        
        return SuccessResponse(
            success=True,
            message=f"Operation '{operation_id}' deleted successfully"
        )
    
    except ValueError as e:
        logger.error(f"Invalid request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found"
        )
    except Exception as e:
        logger.error(f"Error deleting operation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete operation: {str(e)}"
        )
```

#### 5.5 Update Apply Endpoint
**File**: `src/api/controllers/design_project_controller.py`

Update the `apply_iteration_changes` endpoint to work with the new model:

```python
# In apply_iteration_changes function, update the operations handling:

# OLD:
if request.operations is not None:
    operations = [_convert_model_to_operation(op_model) for op_model in request.operations]
else:
    operations = None

# NEW:
if request.operations is not None:
    operations = [_convert_model_to_identified_operation(op_model) for op_model in request.operations]
else:
    operations = None

# Call service (signature unchanged)
updated_ontology = design_project_service.apply_current_iteration_changes(
    project_id=project_id,
    operations=operations
)
```

### Phase 6: Storage Layer Updates

#### 6.1 Update Store Serialization
**File**: `src/design_project/store.py`

Update serialization to handle `IdentifiedOperation`:

```python
# In _serialize_iteration method:

# OLD:
if iteration.plannedOperations is not None:
    iteration_dict['plannedOperations'] = [
        self._serialize_operation(op) for op in iteration.plannedOperations
    ]

# NEW:
if iteration.plannedOperations is not None:
    iteration_dict['plannedOperations'] = [
        {
            'id': identified_op.id,
            'operation': self._serialize_operation(identified_op.operation),
            'created_from_task_id': identified_op.created_from_task_id
        }
        for identified_op in iteration.plannedOperations
    ]
```

#### 6.2 Update Store Deserialization
**File**: `src/design_project/store.py`

Update deserialization:

```python
# In _deserialize_iteration method:

# OLD:
if 'plannedOperations' in iteration_dict and iteration_dict['plannedOperations'] is not None:
    iteration.plannedOperations = [
        self._deserialize_operation(op_dict) for op_dict in iteration_dict['plannedOperations']
    ]

# NEW:
if 'plannedOperations' in iteration_dict and iteration_dict['plannedOperations'] is not None:
    from design_project.domain import IdentifiedOperation
    iteration.plannedOperations = [
        IdentifiedOperation(
            id=identified_op_dict['id'],
            operation=self._deserialize_operation(identified_op_dict['operation']),
            created_from_task_id=identified_op_dict.get('created_from_task_id')
        )
        for identified_op_dict in iteration_dict['plannedOperations']
    ]
```

### Phase 7: Testing

#### 7.1 Create Unit Tests
**File**: `tests/test_iteration_operations_crud.py`

Create comprehensive tests:

```python
"""
Unit tests for iteration operations CRUD functionality.
"""
import unittest
from src.design_project.domain import DesignProject, DesignIteration, IdentifiedOperation
from src.ontology.edit_operations import CreateClassOperation
from rdflib import URIRef

class TestIterationOperationsCRUD(unittest.TestCase):
    
    def test_reorder_operations(self):
        """Test reordering operations maintains IDs and changes order."""
        # Setup: Create iteration with 3 operations
        # Action: Reorder to [2, 0, 1]
        # Assert: Order changed, IDs preserved
        pass
    
    def test_update_operation(self):
        """Test updating operation creates new instance with same ID."""
        # Setup: Create operation
        # Action: Update label
        # Assert: Label changed, ID unchanged, operation immutable
        pass
    
    def test_delete_operation(self):
        """Test deleting operation removes it from list."""
        # Setup: Create iteration with 3 operations
        # Action: Delete middle operation
        # Assert: Only 2 operations remain, correct one deleted
        pass
    
    def test_operations_have_unique_ids(self):
        """Test that generated operations have unique IDs."""
        pass
    
    def test_operation_traceability_to_task(self):
        """Test that operations track which task created them."""
        pass

if __name__ == '__main__':
    unittest.main()
```

#### 7.2 Create Integration Tests
**File**: `tests/test_api_iteration_operations_crud.py`

Test API endpoints:

```python
"""
Integration tests for iteration operations CRUD API endpoints.
"""
import unittest
from fastapi.testclient import TestClient

class TestIterationOperationsCRUDAPI(unittest.TestCase):
    
    def test_reorder_operations_endpoint(self):
        """Test PUT /projects/{id}/iterations/{id}/operations/reorder"""
        pass
    
    def test_update_operation_endpoint(self):
        """Test PUT /projects/{id}/iterations/{id}/operations/{op_id}"""
        pass
    
    def test_delete_operation_endpoint(self):
        """Test DELETE /projects/{id}/iterations/{id}/operations/{op_id}"""
        pass
    
    def test_operations_returned_with_ids(self):
        """Test that prepare endpoint returns operations with IDs."""
        pass
    
    def test_apply_with_modified_operations(self):
        """Test applying after reorder/update/delete."""
        pass

if __name__ == '__main__':
    unittest.main()
```

### Phase 8: Documentation Updates

#### 8.1 Update API Documentation
**File**: `doc/api-enhancement-get-current-iteration-operations.md`

Update to reflect new CRUD capabilities.

#### 8.2 Update Domain Model Diagram
**File**: `doc/domain-model.puml`

Add `IdentifiedOperation` to the diagram.

#### 8.3 Update User Stories
**File**: `doc/user-stories.md`

Add or update user stories:
- "As a user, I want to reorder operations so I can control application order"
- "As a user, I want to edit operation details so I can correct AI mistakes"
- "As a user, I want to delete unwanted operations so I only apply what I need"

## Migration Strategy

### Backward Compatibility

**Existing Projects**: Projects with old-style `plannedOperations` (direct list of operations) need migration:

```python
# In FileSystemDesignProjectStore._deserialize_iteration:

if 'plannedOperations' in iteration_dict and iteration_dict['plannedOperations'] is not None:
    operations_data = iteration_dict['plannedOperations']
    
    # Check if this is old format (direct operation list) or new format (identified operations)
    if operations_data and isinstance(operations_data[0], dict):
        # Check for 'id' key to distinguish formats
        if 'id' in operations_data[0] and 'operation' in operations_data[0]:
            # New format - deserialize as IdentifiedOperation
            iteration.plannedOperations = [
                IdentifiedOperation(
                    id=identified_op_dict['id'],
                    operation=self._deserialize_operation(identified_op_dict['operation']),
                    created_from_task_id=identified_op_dict.get('created_from_task_id')
                )
                for identified_op_dict in operations_data
            ]
        else:
            # Old format - wrap with generated IDs
            import uuid
            iteration.plannedOperations = [
                IdentifiedOperation(
                    id=str(uuid.uuid4()),
                    operation=self._deserialize_operation(op_dict),
                    created_from_task_id=None
                )
                for op_dict in operations_data
            ]
```

### Rollout Plan

1. **Phase 1-2**: Domain and API model changes (no API changes yet)
2. **Phase 3-4**: Service and controller updates
3. **Phase 5**: Storage layer updates with backward compatibility
4. **Phase 6**: Deploy and migrate existing projects
5. **Phase 7**: Add new CRUD endpoints
6. **Phase 8**: Testing and documentation

## Implementation Checklist

- [ ] Phase 1: Domain Model Changes
  - [ ] Add `IdentifiedOperation` dataclass
  - [ ] Update `DesignIteration.plannedOperations` type
  
- [ ] Phase 2: API Model Changes
  - [ ] Add `id` to `OntologyOperationModel`
  - [ ] Add `ReorderOperationsRequest`
  - [ ] Add `UpdateOperationRequest`
  - [ ] Remove `FilterOperationsRequest`
  
- [ ] Phase 3: Controller Helper Functions
  - [ ] Update `_convert_operation_to_model`
  - [ ] Add `_convert_model_to_identified_operation`
  - [ ] Add `_apply_operation_updates` helper
  
- [ ] Phase 4: Service Layer Changes
  - [ ] Update `prepare_planned_iteration`
  - [ ] Update `apply_current_iteration_changes`
  - [ ] Add `reorder_iteration_operations`
  - [ ] Add `update_iteration_operation`
  - [ ] Add `delete_iteration_operation`
  
- [ ] Phase 5: Controller Endpoints
  - [ ] Remove `filter_operations` endpoint
  - [ ] Add `reorder_operations` endpoint
  - [ ] Add `update_operation` endpoint
  - [ ] Add `delete_operation` endpoint
  - [ ] Update `apply_iteration_changes` endpoint
  
- [ ] Phase 6: Storage Layer Updates
  - [ ] Update serialization in store
  - [ ] Update deserialization in store
  - [ ] Add backward compatibility for old format
  
- [ ] Phase 7: Testing
  - [ ] Create unit tests for CRUD operations
  - [ ] Create integration tests for API endpoints
  - [ ] Test backward compatibility
  
- [ ] Phase 8: Documentation
  - [ ] Update API documentation
  - [ ] Update domain model diagram
  - [ ] Update user stories

## Risk Assessment

### High Risk
- **Data migration**: Existing projects need careful migration of `plannedOperations`
- **Breaking changes**: API changes affect frontend

### Medium Risk
- **Operation immutability**: Need to ensure update creates new instances correctly
- **ID generation**: Must ensure IDs are truly unique across all operations

### Low Risk
- **Reordering logic**: Simple list manipulation
- **Delete logic**: Straightforward filtering

## Estimated Effort

- **Phase 1-2**: 2-3 hours (domain and API models)
- **Phase 3**: 3-4 hours (conversion functions)
- **Phase 4**: 4-5 hours (service layer)
- **Phase 5**: 4-5 hours (controller endpoints)
- **Phase 6**: 2-3 hours (storage layer)
- **Phase 7**: 4-6 hours (testing)
- **Phase 8**: 1-2 hours (documentation)

**Total**: 20-28 hours

## Success Criteria

1. ✅ Users can reorder operations via API
2. ✅ Users can update individual operation fields
3. ✅ Users can delete unwanted operations
4. ✅ All operations have unique, stable IDs
5. ✅ Operations maintain immutability where appropriate
6. ✅ Backward compatibility with existing projects
7. ✅ Comprehensive test coverage
8. ✅ API follows same patterns as task CRUD
