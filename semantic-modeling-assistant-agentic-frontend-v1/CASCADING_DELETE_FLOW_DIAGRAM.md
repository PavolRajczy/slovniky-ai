# Cascading Delete Flow Diagram

## Decision Flow

```
User clicks "Delete" on an operation
             |
             v
    Is it a CREATE operation?
             |
         Yes |  No
             |   |
             v   v
   Find dependent ops    Simple confirm dialog
             |                    |
             v                    v
   Has dependencies?         Delete operation
             |                    |
         Yes |  No                |
             |   |                |
             v   v                |
   Show cascade | Simple confirm  |
      modal     |    dialog       |
             |  |                 |
             v  v                 |
   User confirms deletion         |
             |                    |
             v                    v
   Delete all ops in cascade    Success!
   (reverse order)
             |
             v
        Success!
```

## Dependency Detection Logic

```
For CREATE Class "Person" (uri: /Person)
             |
             v
Check all operations AFTER this one
             |
             +---> Is it an Attribute?
             |          |
             |          v
             |     Check: owning_class_uri == /Person?
             |          |
             |          v YES
             |     Add to dependents (reason: "Attribute's domain class")
             |
             +---> Is it a Relationship?
             |          |
             |          v
             |     Check: source_class_uri == /Person?
             |          |  OR
             |     Check: target_class_uri == /Person?
             |          |
             |          v YES
             |     Add to dependents (reason: "Relationship's source/target class")
             |
             +---> Is it a Class?
             |          |
             |          v
             |     Check: generalization_uris includes /Person?
             |          |
             |          v YES
             |     Add to dependents (reason: "Parent class in generalization")
             |
             +---> Is it UPDATE or DELETE?
                        |
                        v
                   Check: uri == /Person?
                        |
                        v YES
                   Add to dependents (reason: "Updates/Deletes this class")
```

## Modal UI Structure

```
+-----------------------------------------------------------------------+
|  Delete Operation with Dependencies                              [X]  |
+-----------------------------------------------------------------------+
|                                                                       |
|  +----------------------------------------------------------------+  |
|  | ⚠️  This operation has dependent operations                    |  |
|  |                                                                 |  |
|  | Deleting this CREATE operation will break 3 operations that    |  |
|  | depend on it. All dependent operations must be deleted as well.|  |
|  +----------------------------------------------------------------+  |
|                                                                       |
|  Operation to delete:                                                |
|  +----------------------------------------------------------------+  |
|  | [Add Class] [class]                                            |  |
|  | URI: /Person                                                   |  |
|  | Label: Person                                                  |  |
|  +----------------------------------------------------------------+  |
|                                                                       |
|  Dependent operations (will also be deleted):                        |
|  +----------------------------------------------------------------+  |
|  | [Add Attribute] [attribute] [Attribute's domain class]         |  |
|  | URI: /Person/name                                              |  |
|  | Label: name                                                    |  |
|  +----------------------------------------------------------------+  |
|  | [Add Attribute] [attribute] [Attribute's domain class]         |  |
|  | URI: /Person/age                                               |  |
|  | Label: age                                                     |  |
|  +----------------------------------------------------------------+  |
|  | [Modify Class] [class] [Updates this class]                    |  |
|  | URI: /Person                                                   |  |
|  +----------------------------------------------------------------+  |
|                                                                       |
|  +----------------------------------------------------------------+  |
|  | Total operations to delete: 4                                  |  |
|  +----------------------------------------------------------------+  |
|                                                                       |
|  [        Cancel        ]  [       Delete All       ]                |
|                                                                       |
+-----------------------------------------------------------------------+
```

## Deletion Order

When cascading delete is triggered, operations are deleted in **reverse order**:

```
Original order:
1. CREATE Class "Person"           <- Target for deletion
2. CREATE Attribute "name"         <- Dependent
3. CREATE Attribute "age"          <- Dependent
4. UPDATE Class "Person"           <- Dependent

Deletion order (reverse):
4. DELETE UPDATE Class "Person"
3. DELETE CREATE Attribute "age"
2. DELETE CREATE Attribute "name"
1. DELETE CREATE Class "Person"
```

This ensures that dependent operations are removed before the operation they depend on, preventing temporary inconsistencies during the deletion process.

## State Management

```typescript
// State for delete confirmation
deleteConfirmation: {
  operation: OntologyOperationModel,    // The operation user wants to delete
  dependentOps: Array<{                 // Operations that depend on it
    ...OntologyOperationModel,
    dependencyReason: string            // Why this operation depends on it
  }>
} | null

// Dependency reasons:
- "Attribute's domain class"
- "Relationship's source class"
- "Relationship's target class"
- "Parent class in generalization"
- "Updates this class/attribute/relationship"
- "Deletes this class/attribute/relationship"
```

## Example Dependency Graph

```
CREATE Class "Entity" (/Entity)
    |
    +---> CREATE Class "Person" (/Person, parent: /Entity)
    |         |
    |         +---> CREATE Attribute "name" (domain: /Person)
    |         |         |
    |         |         +---> UPDATE Attribute "name"
    |         |
    |         +---> CREATE Attribute "age" (domain: /Person)
    |         |
    |         +---> CREATE Relationship "worksFor" (source: /Person)
    |
    +---> CREATE Attribute "identifier" (domain: /Entity)

Deleting "Entity" cascades to:
  - CREATE Class "Person" (parent class dependency)
  - CREATE Attribute "identifier" (domain class dependency)

Deleting "Person" cascades to:
  - CREATE Attribute "name" (domain class dependency)
  - UPDATE Attribute "name" (target dependency)
  - CREATE Attribute "age" (domain class dependency)
  - CREATE Relationship "worksFor" (source class dependency)
```
