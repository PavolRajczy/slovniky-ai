"""
Example: Using the new multi-step project creation workflow via API
"""

import requests
import json

# Base URL for the API
BASE_URL = "http://localhost:8000/api"

def create_project_example():
    """
    Example showing the complete new project creation workflow.
    """
    
    print("="*70)
    print("Multi-Step Project Creation Example")
    print("="*70)
    
    # Step 1: Create empty project
    print("\n[Step 1] Creating empty project...")
    response = requests.post(
        f"{BASE_URL}/projects",
        json={
            "name": "Traffic Regulations Project",
            "ontology_uri": "https://slovník.gov.cz/datový/turistické-cíle",
            "knowledge_domain_name": "Traffic Regulations",
            "knowledge_domain_description": "Domain covering traffic rules and road safety"
        }
    )
    response.raise_for_status()
    project = response.json()
    project_id = project["id"]
    
    print(f"✓ Created project: {project_id}")
    print(f"  Name: {project['name']}")
    print(f"  Domain: {project['knowledge_domain_name']}")
    print(f"  Legal documents: {len(project['legal_knowledge_document_ids'])}")
    print(f"  Domain areas: {len(project['domain_areas'])}")
    
    # Step 2a: Add legal knowledge documents
    print("\n[Step 2a] Adding legal knowledge documents...")
    response = requests.post(
        f"{BASE_URL}/projects/{project_id}/knowledge-base/legal",
        json={
            "document_ids": [
                "https://www.zakonyprolidi.cz/cs/2000-361"
            ]
        }
    )
    response.raise_for_status()
    result = response.json()
    print(f"✓ {result['message']}")
    
    # Step 2b: Add expert knowledge documents (optional)
    print("\n[Step 2b] Adding expert knowledge documents...")
    # In this example, we skip expert documents
    print("  (Skipped - no expert documents to add)")
    
    # Step 3: Set key knowledge document
    print("\n[Step 3] Setting key knowledge document...")
    response = requests.put(
        f"{BASE_URL}/projects/{project_id}/key-document",
        json={
            "document_id": "https://www.zakonyprolidi.cz/cs/2000-361"
        }
    )
    response.raise_for_status()
    result = response.json()
    print(f"✓ {result['message']}")
    
    # Step 4: Generate domain areas
    print("\n[Step 4] Generating domain areas...")
    response = requests.post(
        f"{BASE_URL}/projects/{project_id}/domain-areas/generate",
        json={
            "user_instruction": "Focus on road infrastructure and traffic management"
        }
    )
    response.raise_for_status()
    areas = response.json()
    
    print(f"✓ Generated {len(areas)} domain areas:")
    for area in areas:
        print(f"\n  Area: {area['label']}")
        print(f"  Description: {area['description']}")
        print(f"  Key concepts: {', '.join(area['key_concepts'][:5])}")
    
    # Step 5: Get final project state
    print("\n[Step 5] Getting final project state...")
    response = requests.get(f"{BASE_URL}/projects/{project_id}")
    response.raise_for_status()
    final_project = response.json()
    
    print(f"✓ Final project state:")
    print(f"  Legal documents: {len(final_project['legal_knowledge_document_ids'])}")
    print(f"  Expert documents: {len(final_project['expert_knowledge_document_ids'])}")
    print(f"  Domain areas: {len(final_project['domain_areas'])}")
    
    print("\n" + "="*70)
    print("✓ Project creation completed!")
    print("="*70)
    print(f"\nProject ID: {project_id}")
    
    return project_id


def error_examples():
    """
    Examples of error cases in the new workflow.
    """
    
    print("\n" + "="*70)
    print("Error Handling Examples")
    print("="*70)
    
    # Create a test project
    response = requests.post(
        f"{BASE_URL}/projects",
        json={
            "name": "Error Test Project",
            "ontology_uri": "https://slovník.gov.cz/datový/turistické-cíle"
        }
    )
    project_id = response.json()["id"]
    
    # Error 1: Try to set key document before adding any documents
    print("\n[Error 1] Setting key document before adding documents...")
    try:
        response = requests.put(
            f"{BASE_URL}/projects/{project_id}/key-document",
            json={
                "document_id": "https://www.zakonyprolidi.cz/cs/2000-361"
            }
        )
        response.raise_for_status()
        print("✗ Should have failed!")
    except requests.HTTPError as e:
        print(f"✓ Correctly failed with: {e.response.json()['detail']}")
    
    # Error 2: Try to generate domain areas without setting key document
    print("\n[Error 2] Generating domain areas without key document...")
    try:
        response = requests.post(
            f"{BASE_URL}/projects/{project_id}/domain-areas/generate",
            json={}
        )
        response.raise_for_status()
        print("✗ Should have failed!")
    except requests.HTTPError as e:
        print(f"✓ Correctly failed with: {e.response.json()['detail']}")
    
    print("\n" + "="*70)
    print("✓ Error handling working correctly!")
    print("="*70)


if __name__ == "__main__":
    # Make sure the API is running on http://localhost:8000
    print("Note: Make sure the API is running on http://localhost:8000")
    print("Run: python run_api.py")
    print()
    
    try:
        # Test if API is available
        response = requests.get(f"{BASE_URL}/ontologies")
        
        # Run the example
        project_id = create_project_example()
        
        # Show error examples
        error_examples()
        
    except requests.ConnectionError:
        print("ERROR: Could not connect to API at http://localhost:8000")
        print("Please start the API first: python run_api.py")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
