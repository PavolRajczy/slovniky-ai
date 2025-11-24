# Design Task Patterns API Implementation

## Overview

This document describes the implementation of the API endpoint to retrieve design task patterns. This endpoint allows the frontend to fetch the list of available patterns that can be used when creating or updating design tasks.

## Problem Statement

The `CreateTaskRequest` and `UpdateTaskRequest` models require a `followed_pattern_id` field, but there was no API operation that would allow the frontend to retrieve the list of available patterns and their IDs.

## Solution

A new API endpoint has been created to expose the list of design task patterns for a project.

### Changes Made

#### 1. API Models (`src/api/models.py`)

Added two new models:

- **`DesignTaskPatternModel`**: Represents a single design task pattern
  - `id`: The unique identifier of the pattern
  - `name`: The human-readable name of the pattern
  - `category`: The category of the pattern (class, attribute, relationship)
  - `specification`: Optional detailed description of the pattern
  - `when_applicable`: Optional description of when the pattern is applicable

- **`TaskPatternsListResponse`**: Response model for the patterns list endpoint
  - `patterns`: List of `DesignTaskPatternModel` objects

#### 2. Service Layer (`src/design_project/service.py`)

Added a new method to `DesignProjectService`:

```python
def get_design_task_patterns(self, project_id: str) -> List[DesignTaskPattern]:
    """
    Gets the list of design task patterns for a project.

    Args:
        project_id (str): The ID of the project.

    Returns:
        List[DesignTaskPattern]: The list of design task patterns used in the project.
    """
    project = self.load_project(project_id)
    return project.patterns
```

#### 3. Controller Layer (`src/api/controllers/design_project_controller.py`)

Added:

- **Helper function** `_convert_pattern_to_model()`: Converts domain `DesignTaskPattern` to API `DesignTaskPatternModel`
- **API endpoint**: `GET /projects/{project_id}/patterns`
  - Returns: `TaskPatternsListResponse` containing the list of patterns
  - Status: 200 OK on success, 404 if project not found, 500 on error

#### 4. Tests (`tests/test_design_task_patterns_api.py`)

Created comprehensive unit tests covering:
- Pattern factory validation
- Pattern-to-API-model conversion
- API model structure validation

## Usage

### Endpoint

```
GET /projects/{project_id}/patterns
```

### Example Response

```json
{
  "patterns": [
    {
      "id": "DP_CLASS_01",
      "name": "Discover Domain Classes - Core Concepts",
      "category": "class",
      "specification": "Analyze the domain knowledge to identify new ontology classes...",
      "when_applicable": "When there is a need to expand the ontology with new core domain classes..."
    },
    {
      "id": "DP_ATTRIBUTE_01",
      "name": "Define Class Attributes",
      "category": "attribute",
      "specification": "Analyze the domain knowledge to identify new ontology attributes...",
      "when_applicable": "When there is a need to enrich an existing class with attributes..."
    }
  ]
}
```

### Frontend Integration

The frontend can now:

1. Call `GET /projects/{project_id}/patterns` to retrieve all available patterns
2. Display the patterns in a dropdown or selection UI when creating/updating tasks
3. Use the `pattern.id` as the value for `followed_pattern_id` in `CreateTaskRequest` or `UpdateTaskRequest`

## Available Pattern Categories

The system currently supports 21 patterns across 3 categories:

- **Class patterns** (10): For discovering, modifying, and managing ontology classes
- **Attribute patterns** (5): For defining, modifying, and managing ontology attributes
- **Relationship patterns** (6): For establishing, modifying, and managing relationships between classes

## Testing

Run the tests with:

```powershell
.\.venv\Scripts\python.exe .\tests\test_design_task_patterns_api.py
```

All tests pass successfully, validating:
- ✓ 21 patterns are correctly defined in the factory
- ✓ Pattern structure is valid (id, name, category, specification, whenApplicable)
- ✓ Pattern-to-API-model conversion works correctly
- ✓ API model can be properly serialized for JSON responses

## Architecture

The implementation follows the project's established patterns:

```
Domain Layer (design_project/domain.py)
    ↓
    DesignTaskPattern
    ↓
Factory Layer (design_task_patterns_factory.py)
    ↓
    DesignTaskPatternsFactory_Basic
    ↓
Service Layer (design_project/service.py)
    ↓
    get_design_task_patterns()
    ↓
Controller Layer (api/controllers/design_project_controller.py)
    ↓
    GET /projects/{project_id}/patterns
    ↓
API Models (api/models.py)
    ↓
    DesignTaskPatternModel, TaskPatternsListResponse
```

## Notes

- Patterns are loaded dynamically from the factory based on the project's `patternsFactoryId`
- The current implementation uses `DesignTaskPatternsFactory_Basic` which provides 21 predefined patterns
- The pattern list is stored in the project and loaded when the project is loaded
- This ensures consistency: tasks always reference patterns that exist in the project
