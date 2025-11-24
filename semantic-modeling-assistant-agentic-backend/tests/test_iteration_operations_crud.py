"""
Unit tests for iteration operations CRUD functionality.

This test file verifies that operations can be managed with CRUD operations:
- Reordering operations
- Updating operations
- Deleting operations
- Operations have unique IDs
- Operations maintain traceability to tasks
"""
#!/usr/bin/env python3
import unittest
import uuid
import sys
import os

# Ensure src/ is importable when running as a script
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

from rdflib import URIRef
from design_project.domain import IdentifiedOperation
from ontology.edit_operations import CreateClassOperation, OperationType
from ontology.domain import Kind


class TestIterationOperationsCRUD(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures."""
        # Create sample operations
        self.op1 = CreateClassOperation(
            uri=URIRef("http://example.org/Class1"),
            label="Class 1",
            kind=Kind.OBJECT,
            definition="First test class"
        )
        self.op2 = CreateClassOperation(
            uri=URIRef("http://example.org/Class2"),
            label="Class 2",
            kind=Kind.OBJECT,
            definition="Second test class"
        )
        self.op3 = CreateClassOperation(
            uri=URIRef("http://example.org/Class3"),
            label="Class 3",
            kind=Kind.OBJECT,
            definition="Third test class"
        )
        
        # Create identified operations
        self.task_id = str(uuid.uuid4())
        self.identified_op1 = IdentifiedOperation(
            id=str(uuid.uuid4()),
            operation=self.op1,
            created_from_task_id=self.task_id
        )
        self.identified_op2 = IdentifiedOperation(
            id=str(uuid.uuid4()),
            operation=self.op2,
            created_from_task_id=self.task_id
        )
        self.identified_op3 = IdentifiedOperation(
            id=str(uuid.uuid4()),
            operation=self.op3,
            created_from_task_id=self.task_id
        )
    
    def test_operations_have_unique_ids(self):
        """Test that operations have unique IDs."""
        ids = {self.identified_op1.id, self.identified_op2.id, self.identified_op3.id}
        self.assertEqual(len(ids), 3, "All operation IDs should be unique")
    
    def test_operation_traceability_to_task(self):
        """Test that operations track which task created them."""
        self.assertEqual(self.identified_op1.created_from_task_id, self.task_id)
        self.assertEqual(self.identified_op2.created_from_task_id, self.task_id)
        self.assertEqual(self.identified_op3.created_from_task_id, self.task_id)
    
    def test_reorder_operations(self):
        """Test reordering operations maintains IDs and changes order."""
        # Setup: Create list with 3 operations
        operations = [self.identified_op1, self.identified_op2, self.identified_op3]
        
        # Reorder to [2, 0, 1]
        new_order = [operations[1], operations[2], operations[0]]
        
        # Assert: Order changed
        self.assertEqual(new_order[0].id, self.identified_op2.id)
        self.assertEqual(new_order[1].id, self.identified_op3.id)
        self.assertEqual(new_order[2].id, self.identified_op1.id)
        
        # Assert: IDs preserved
        self.assertEqual(new_order[0].operation.label, "Class 2")
        self.assertEqual(new_order[1].operation.label, "Class 3")
        self.assertEqual(new_order[2].operation.label, "Class 1")
    
    def test_update_operation_creates_new_instance(self):
        """Test updating operation creates new instance with same ID."""
        original_id = self.identified_op1.id
        original_task_id = self.identified_op1.created_from_task_id
        
        # Create updated operation with different label
        updated_operation = CreateClassOperation(
            uri=self.op1.uri,
            label="Updated Class 1",  # Changed
            kind=self.op1.kind,
            definition=self.op1.definition
        )
        
        # Wrap in new IdentifiedOperation with same ID
        updated_identified_op = IdentifiedOperation(
            id=original_id,  # Same ID
            operation=updated_operation,
            created_from_task_id=original_task_id  # Same task ID
        )
        
        # Assert: ID unchanged
        self.assertEqual(updated_identified_op.id, original_id)
        
        # Assert: Label changed
        self.assertEqual(updated_identified_op.operation.label, "Updated Class 1")
        
        # Assert: Operation is immutable (original unchanged)
        self.assertEqual(self.identified_op1.operation.label, "Class 1")
        
        # Assert: Traceability preserved
        self.assertEqual(updated_identified_op.created_from_task_id, original_task_id)
    
    def test_delete_operation_removes_from_list(self):
        """Test deleting operation removes it from list."""
        # Setup: Create list with 3 operations
        operations = [self.identified_op1, self.identified_op2, self.identified_op3]
        
        # Delete middle operation
        operation_to_delete_id = self.identified_op2.id
        operations = [op for op in operations if op.id != operation_to_delete_id]
        
        # Assert: Only 2 operations remain
        self.assertEqual(len(operations), 2)
        
        # Assert: Correct operation deleted
        remaining_ids = {op.id for op in operations}
        self.assertIn(self.identified_op1.id, remaining_ids)
        self.assertNotIn(self.identified_op2.id, remaining_ids)
        self.assertIn(self.identified_op3.id, remaining_ids)
    
    def test_identified_operation_wraps_immutable_operation(self):
        """Test that IdentifiedOperation correctly wraps immutable operation."""
        # The underlying operation should be frozen (immutable)
        with self.assertRaises(Exception):
            # Try to modify the operation (should fail because it's frozen)
            self.identified_op1.operation.label = "Modified"
    
    def test_operations_maintain_operation_type(self):
        """Test that operations maintain their operation type."""
        self.assertEqual(self.identified_op1.operation.operation_type, OperationType.CREATE)
        self.assertEqual(self.identified_op2.operation.operation_type, OperationType.CREATE)
        self.assertEqual(self.identified_op3.operation.operation_type, OperationType.CREATE)


if __name__ == '__main__':
    unittest.main()
