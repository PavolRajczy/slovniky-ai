"""
Test suite for Design Task Patterns API endpoint

This test validates that:
1. Patterns are correctly defined in the factory
2. Pattern data is correctly converted to API models  
3. The basic structure is correct for API consumption
"""

import os
import sys

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from design_project.design_task_patterns_factory import DesignTaskPatternsFactory_Basic
from design_project.domain import DesignTaskPattern


def test_patterns_factory():
    """
    Test that the patterns factory returns valid patterns.
    """
    print("\n=== Test: Patterns Factory ===\n")
    
    # Get patterns from factory
    factory = DesignTaskPatternsFactory_Basic()
    patterns = factory.get_design_task_patterns()
    
    # Verify patterns were returned
    assert patterns is not None, "Patterns should not be None"
    assert len(patterns) > 0, "Should have at least one pattern"
    
    print(f"✓ Found {len(patterns)} patterns from factory")
    
    # Verify pattern structure
    for i, pattern in enumerate(patterns):
        assert isinstance(pattern, DesignTaskPattern), f"Pattern {i} should be DesignTaskPattern"
        assert pattern.id, f"Pattern {i} should have id"
        assert pattern.name, f"Pattern {i} should have name"
        assert pattern.category, f"Pattern {i} should have category"
        # specification and whenApplicable can be None/empty
    
    print(f"✓ All patterns have valid structure")
    
    # Print pattern summary
    print("\nPattern Summary:")
    category_counts = {}
    for pattern in patterns:
        cat = pattern.category.value
        category_counts[cat] = category_counts.get(cat, 0) + 1
        print(f"  - {pattern.id}: {pattern.name} ({cat})")
    
    print(f"\nPatterns by category:")
    for cat, count in sorted(category_counts.items()):
        print(f"  - {cat}: {count} patterns")
    
    print("\n✓ Test passed: patterns factory works correctly\n")
    return patterns


def test_pattern_conversion_to_api_model():
    """
    Test that patterns can be converted to API models correctly.
    """
    print("\n=== Test: Pattern Conversion to API Model ===\n")
    
    # Import the conversion function and model
    from api.controllers.design_project_controller import _convert_pattern_to_model
    from api.models import DesignTaskPatternModel
    
    # Get patterns from factory
    factory = DesignTaskPatternsFactory_Basic()
    patterns = factory.get_design_task_patterns()
    
    # Convert first pattern to API model
    first_pattern = patterns[0]
    api_model = _convert_pattern_to_model(first_pattern)
    
    # Verify API model structure
    assert isinstance(api_model, DesignTaskPatternModel), "Should return DesignTaskPatternModel"
    assert api_model.id == first_pattern.id, "ID should match"
    assert api_model.name == first_pattern.name, "Name should match"
    assert api_model.category == first_pattern.category.value, "Category should match"
    assert api_model.specification == first_pattern.specification, "Specification should match"
    assert api_model.when_applicable == first_pattern.whenApplicable, "whenApplicable should match"
    
    print(f"✓ Pattern conversion validated")
    print(f"  - API Model ID: {api_model.id}")
    print(f"  - API Model name: {api_model.name}")
    print(f"  - API Model category: {api_model.category}")
    
    # Test converting all patterns
    for pattern in patterns:
        api_model = _convert_pattern_to_model(pattern)
        assert api_model.id == pattern.id, f"Pattern {pattern.id} conversion failed"
    
    print(f"✓ All {len(patterns)} patterns converted successfully")
    
    print("\n✓ Test passed: pattern conversion to API model works correctly\n")


def test_api_model_structure():
    """
    Test that the API model has the expected structure.
    """
    print("\n=== Test: API Model Structure ===\n")
    
    from api.models import DesignTaskPatternModel, TaskPatternsListResponse
    
    # Create a sample pattern model
    sample_pattern = DesignTaskPatternModel(
        id="TEST_01",
        name="Test Pattern",
        category="CLASS",
        specification="Test specification",
        when_applicable="Test applicability"
    )
    
    print(f"✓ DesignTaskPatternModel created successfully")
    print(f"  - id: {sample_pattern.id}")
    print(f"  - name: {sample_pattern.name}")
    print(f"  - category: {sample_pattern.category}")
    
    # Create a response model
    response = TaskPatternsListResponse(patterns=[sample_pattern])
    
    print(f"✓ TaskPatternsListResponse created successfully")
    print(f"  - patterns count: {len(response.patterns)}")
    
    # Verify the response can be serialized (important for API)
    response_dict = response.model_dump()
    assert "patterns" in response_dict, "Response should have patterns field"
    assert len(response_dict["patterns"]) == 1, "Response should have 1 pattern"
    
    print(f"✓ Response serialization works correctly")
    
    print("\n✓ Test passed: API model structure is correct\n")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("Running Design Task Patterns API Tests")
    print("="*70)
    
    patterns = test_patterns_factory()
    test_pattern_conversion_to_api_model()
    test_api_model_structure()
    
    print("\n" + "="*70)
    print("All tests completed successfully!")
    print("="*70 + "\n")

