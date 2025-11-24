# API Enhancement: Get Iteration Operations

## Problem Statement

When a client prepares an iteration using `POST /projects/{project_id}/iterations/{iteration_id}/prepare`, the backend:
1. Generates ontology operations using AI
2. Stores these operations in `DesignIteration.plannedOperations`
3. Returns the operations to the client

However, if the client reloads (e.g., browser refresh, app restart), there was no API endpoint to retrieve these already-prepared operations without triggering the prepare process again.

## Solution

Added a new GET endpoint to retrieve prepared operations for an iteration, following the established pattern for iteration operations:

```
GET /projects/{project_id}/iterations/{iteration_id}/operations
```

This endpoint follows the same URL pattern as other iteration operation endpoints:
- `POST /projects/{project_id}/iterations/{iteration_id}/prepare`
- `POST /projects/{project_id}/iterations/{iteration_id}/apply`
- `POST /projects/{project_id}/iterations/{iteration_id}/cancel`

### Endpoint Details

**Response Model:** `IterationPreparedResponse`
```json
{
  "iteration_id": "string",
  "status": "prepared",
  "operations": [
    {
      "operation_type": "create",
      "target_type": "class",
      "uri": "http://example.org/Class1",
      "label": "Class 1",
      ...
    }
  ]
}
```

**Status Codes:**
- `200 OK` - Successfully retrieved operations
- `404 NOT FOUND` - Project not found
- `409 CONFLICT` - Iteration is not the current iteration OR iteration has no prepared operations
- `500 INTERNAL SERVER ERROR` - Server error

**Validation Rules:**

The endpoint enforces that operations can only be retrieved when meaningful:
1. The iteration ID in the URL must match the current iteration ID
2. The iteration must have prepared operations (i.e., in a state where operations have been generated but not yet applied)

This ensures operations are only accessible for the active iteration that's ready for review/application.

**Status Mapping:**

The endpoint maps internal `DesignIterationStatus` to API-visible statuses:
- `OPERATIONS_GENERATED` → `"prepared"`
- `GENERATING_OPERATIONS` → `"generating"`
- `APPLYING_OPERATIONS` → `"applying"`

### Use Cases

1. **Client Reload After Prepare**: User prepares iteration, closes browser, returns later - client can retrieve operations without re-running AI generation

2. **Multi-user Scenarios**: Different users viewing the same project can see what operations are ready to be applied

3. **Resume Workflow**: Application can check if there's a prepared iteration on startup and resume from that point

### Implementation

**File:** `src/api/controllers/design_project_controller.py`

The endpoint:
1. Loads the project
2. Verifies the iteration ID matches the current iteration
3. Validates that the iteration has prepared operations
4. Converts operations from domain model to API model
5. Returns the response with appropriate status

**Test File:** `tests/test_api_get_current_iteration_operations.py`

Test coverage includes:
- Successfully retrieving operations for current iteration
- Error when iteration is not the current iteration (wrong ID)
- Error when no current iteration exists
- Error when operations not prepared
- Error when project not found
- Status mapping for different iteration states

### Related Endpoints

- `POST /projects/{project_id}/iterations/{iteration_id}/prepare` - Generates operations (first-time)
- `POST /projects/{project_id}/iterations/{iteration_id}/apply` - Applies the operations to ontology
- `POST /projects/{project_id}/iterations/{iteration_id}/cancel` - Cancels prepared iteration

### Workflow Example

```
1. Client: POST /iterations/{id}/prepare
   Server: Generates operations, returns them
   
2. Client crashes/reloads
   
3. Client: GET /iterations/{id}/operations
   Server: Returns same operations without regenerating
          (validates that {id} is the current iteration)
   
4. Client: POST /iterations/{id}/apply
   Server: Applies operations to ontology
```

## Testing

Run the test suite:
```powershell
.\.venv\Scripts\python.exe .\tests\test_api_get_current_iteration_operations.py
```

All 6 test cases should pass:
- ✅ test_get_operations_success
- ✅ test_get_operations_no_current_iteration
- ✅ test_get_operations_no_prepared_operations
- ✅ test_get_operations_project_not_found
- ✅ test_get_operations_wrong_iteration_id
- ✅ test_status_mapping
