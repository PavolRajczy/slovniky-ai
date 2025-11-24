# Cascading Delete Testing Scenarios

## Test Scenarios for Operation Delete Functionality

### Scenario 1: Delete CREATE Class with Attributes
**Setup:**
1. Operation 1: CREATE Class "Person" (uri: `/Person`)
2. Operation 2: CREATE Attribute "name" (owning_class_uri: `/Person`)
3. Operation 3: CREATE Attribute "age" (owning_class_uri: `/Person`)

**Action:** Delete Operation 1

**Expected Result:**
- Modal appears showing:
  - Operation to delete: CREATE Class "Person"
  - Dependent operations (2):
    - CREATE Attribute "name" - Reason: "Attribute's domain class"
    - CREATE Attribute "age" - Reason: "Attribute's domain class"
  - Total to delete: 3 operations

**Verification:** After confirming, all 3 operations should be deleted

---

### Scenario 2: Delete CREATE Class with Relationships
**Setup:**
1. Operation 1: CREATE Class "Person" (uri: `/Person`)
2. Operation 2: CREATE Class "Organization" (uri: `/Organization`)
3. Operation 3: CREATE Relationship "worksFor" (source_class_uri: `/Person`, target_class_uri: `/Organization`)

**Action:** Delete Operation 1

**Expected Result:**
- Modal appears showing:
  - Operation to delete: CREATE Class "Person"
  - Dependent operations (1):
    - CREATE Relationship "worksFor" - Reason: "Relationship's source class"
  - Total to delete: 2 operations

---

### Scenario 3: Delete CREATE Class with Subclass
**Setup:**
1. Operation 1: CREATE Class "Entity" (uri: `/Entity`)
2. Operation 2: CREATE Class "Person" (uri: `/Person`, generalization_uris: [`/Entity`])

**Action:** Delete Operation 1

**Expected Result:**
- Modal appears showing:
  - Operation to delete: CREATE Class "Entity"
  - Dependent operations (1):
    - CREATE Class "Person" - Reason: "Parent class in generalization"
  - Total to delete: 2 operations

---

### Scenario 4: Delete CREATE Class with Updates
**Setup:**
1. Operation 1: CREATE Class "Person" (uri: `/Person`)
2. Operation 2: UPDATE Class (uri: `/Person`, label: "Updated Person")
3. Operation 3: CREATE Attribute "name" (owning_class_uri: `/Person`)

**Action:** Delete Operation 1

**Expected Result:**
- Modal appears showing:
  - Operation to delete: CREATE Class "Person"
  - Dependent operations (2):
    - UPDATE Class - Reason: "Updates this class"
    - CREATE Attribute "name" - Reason: "Attribute's domain class"
  - Total to delete: 3 operations

---

### Scenario 5: Complex Dependency Chain
**Setup:**
1. Operation 1: CREATE Class "Entity" (uri: `/Entity`)
2. Operation 2: CREATE Class "Person" (uri: `/Person`, generalization_uris: [`/Entity`])
3. Operation 3: CREATE Attribute "identifier" (owning_class_uri: `/Entity`)
4. Operation 4: CREATE Attribute "name" (owning_class_uri: `/Person`)
5. Operation 5: CREATE Class "Organization" (uri: `/Organization`)
6. Operation 6: CREATE Relationship "worksFor" (source_class_uri: `/Person`, target_class_uri: `/Organization`)

**Action:** Delete Operation 1 (CREATE Class "Entity")

**Expected Result:**
- Modal appears showing:
  - Operation to delete: CREATE Class "Entity"
  - Dependent operations (2):
    - CREATE Class "Person" - Reason: "Parent class in generalization"
    - CREATE Attribute "identifier" - Reason: "Attribute's domain class"
  - Total to delete: 3 operations

**Note:** Operation 4 and 6 depend on Person, not Entity, so they won't be deleted

---

### Scenario 6: Delete CREATE Attribute (No Dependencies)
**Setup:**
1. Operation 1: CREATE Class "Person" (uri: `/Person`)
2. Operation 2: CREATE Attribute "name" (owning_class_uri: `/Person`)
3. Operation 3: CREATE Attribute "age" (owning_class_uri: `/Person`)

**Action:** Delete Operation 2

**Expected Result:**
- Simple confirmation dialog (no cascade modal)
- Only Operation 2 is deleted

---

### Scenario 7: Delete CREATE Attribute with Updates
**Setup:**
1. Operation 1: CREATE Class "Person" (uri: `/Person`)
2. Operation 2: CREATE Attribute "name" (owning_class_uri: `/Person`, uri: `/Person/name`)
3. Operation 3: UPDATE Attribute (uri: `/Person/name`, label: "Full Name")

**Action:** Delete Operation 2

**Expected Result:**
- Modal appears showing:
  - Operation to delete: CREATE Attribute "name"
  - Dependent operations (1):
    - UPDATE Attribute - Reason: "Updates this attribute"
  - Total to delete: 2 operations

---

### Scenario 8: Delete UPDATE Operation (No Dependencies)
**Setup:**
1. Operation 1: CREATE Class "Person" (uri: `/Person`)
2. Operation 2: UPDATE Class (uri: `/Person`, label: "Updated Person")
3. Operation 3: CREATE Attribute "name" (owning_class_uri: `/Person`)

**Action:** Delete Operation 2

**Expected Result:**
- Simple confirmation dialog (no cascade modal)
- Only Operation 2 is deleted
- Operations 1 and 3 remain intact

---

### Scenario 9: Operations in Wrong Order (Should Not Cascade)
**Setup:**
1. Operation 1: CREATE Attribute "name" (owning_class_uri: `/Person`)
2. Operation 2: CREATE Class "Person" (uri: `/Person`)

**Action:** Delete Operation 2

**Expected Result:**
- Simple confirmation dialog (no cascade modal)
- Only Operation 2 is deleted
- Operation 1 remains (though it will be invalid when applied)

**Note:** The system only checks for dependencies in operations that come AFTER the deleted operation

---

### Scenario 10: Relationship with Both Endpoints Dependent
**Setup:**
1. Operation 1: CREATE Class "Person" (uri: `/Person`)
2. Operation 2: CREATE Class "Organization" (uri: `/Organization`)
3. Operation 3: CREATE Relationship "worksFor" (source_class_uri: `/Person`, target_class_uri: `/Organization`)

**Action:** Delete Operation 2 (Organization)

**Expected Result:**
- Modal appears showing:
  - Operation to delete: CREATE Class "Organization"
  - Dependent operations (1):
    - CREATE Relationship "worksFor" - Reason: "Relationship's target class"
  - Total to delete: 2 operations

---

## UI/UX Testing Checklist

- [ ] Modal appears with correct warning banner (yellow background)
- [ ] Operation to delete is highlighted (red background)
- [ ] All dependent operations are listed with correct badges
- [ ] Dependency reasons are clear and accurate
- [ ] Total count is correct
- [ ] Cancel button closes modal without deleting
- [ ] Delete All button triggers cascade delete
- [ ] Loading state shows "Deleting..." during operation
- [ ] Success: Modal closes and operations list refreshes
- [ ] Error: Error message displays in modal
- [ ] Simple delete (no dependencies) still works with basic confirm
- [ ] UPDATE and DELETE operations bypass cascade logic
