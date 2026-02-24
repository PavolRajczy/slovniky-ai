"""
Example usage of the Semantic Modeling Assistant API.

This script demonstrates how to interact with the API programmatically.
Make sure the API server is running before executing this script.

Usage:
    python examples/api_example.py
"""
import requests
import json

# API base URL
BASE_URL = "http://localhost:8000/api"


def print_response(response, title="Response"):
    """Pretty print API response."""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response:\n{json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")
    print(f"{'='*60}\n")


def main():
    """Demonstrate API usage with example requests."""
    
    print("Semantic Modeling Assistant API - Example Usage")
    print("=" * 60)
    
    # 1. Health check
    print("\n1. Checking API health...")
    response = requests.get(f"{BASE_URL}/health")
    print_response(response, "Health Check")
    
    # 2. Create a new ontology
    print("\n2. Creating a new ontology...")
    ontology_data = {
        "ontology_uri": "http://example.org/ontologies/vehicles",
        "ontology_label": "Vehicle Ontology",
        "ontology_description": "An ontology for modeling vehicles and their properties"
    }
    response = requests.post(f"{BASE_URL}/ontologies", json=ontology_data)
    print_response(response, "Create Ontology")
    if response.status_code == 409:
        print("(Ontology already exists from a previous run; continuing.)\n")
    
    # 3. Get the ontology (works for both newly created and existing)
    if response.status_code in (201, 409):
        print("\n3. Retrieving the created ontology...")
        ontology_uri = requests.utils.quote(ontology_data["ontology_uri"], safe='')
        response = requests.get(f"{BASE_URL}/ontologies/{ontology_uri}")
        print_response(response, "Get Ontology")
    
    # 4. Create a design project
    print("\n4. Creating a design project...")
    project_data = {
        "name": "Vehicle Design Project",
        "ontology_uri": "http://example.org/ontologies/vehicles",
        "legal_knowledge_document_ids": [],
        "expert_knowledge_document_ids": [],
        "knowledge_domain_name": "Vehicles",
        "knowledge_domain_description": "Domain of road vehicles and their characteristics"
    }
    response = requests.post(f"{BASE_URL}/projects", json=project_data)
    print_response(response, "Create Project")
    
    project_id = None
    if response.status_code == 201:
        project_id = response.json().get("id")
        
        # 5. Get the project
        print(f"\n5. Retrieving project {project_id}...")
        response = requests.get(f"{BASE_URL}/projects/{project_id}")
        print_response(response, "Get Project")
        
        # 6. List domain areas
        print(f"\n6. Listing domain areas for project {project_id}...")
        response = requests.get(f"{BASE_URL}/projects/{project_id}/domain-areas")
        print_response(response, "List Domain Areas")
        
        # 7. Create a manual domain area
        print(f"\n7. Creating a manual domain area...")
        area_data = {
            "label": "Car Types",
            "description": "Classification of different types of cars",
            "key_concepts": ["sedan", "SUV", "coupe", "convertible"]
        }
        response = requests.post(f"{BASE_URL}/projects/{project_id}/domain-areas", json=area_data)
        print_response(response, "Create Domain Area")
        
        area_id = None
        if response.status_code == 201:
            area_id = response.json().get("id")
            
            # 8. Suggest iterations for the area
            print(f"\n8. Suggesting iterations for area {area_id}...")
            suggest_data = {
                "focused_area_id": area_id,
                "count": 3,
                "user_instruction": "Focus on modeling basic car types"
            }
            response = requests.post(
                f"{BASE_URL}/projects/{project_id}/iterations/suggest",
                json=suggest_data
            )
            print_response(response, "Suggest Iterations")
            if response.status_code == 500:
                try:
                    msg = response.json().get("message", "") or response.json().get("detail", "")
                    if "key knowledge document" in (msg if isinstance(msg, str) else str(msg)):
                        print("(Suggest iterations requires a key knowledge document on the project; "
                              "see new_project_workflow_example.py for upload + set key document.)\n")
                except Exception:
                    pass
            
            # 9. List iterations
            print(f"\n9. Listing all iterations...")
            response = requests.get(f"{BASE_URL}/projects/{project_id}/iterations")
            print_response(response, "List Iterations")
        
        # 10. Get project ontology
        print(f"\n10. Getting project ontology...")
        response = requests.get(f"{BASE_URL}/projects/{project_id}/ontology")
        print_response(response, "Get Project Ontology")
    
    # 11. List all projects
    print("\n11. Listing all projects...")
    response = requests.get(f"{BASE_URL}/projects")
    print_response(response, "List Projects")
    
    # 12. List all ontologies
    print("\n12. Listing all ontologies...")
    response = requests.get(f"{BASE_URL}/ontologies")
    print_response(response, "List Ontologies")
    
    print("\n" + "="*60)
    print("API Example Completed!")
    print("="*60)


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to the API server.")
        print("Make sure the API is running at http://localhost:8000")
        print("\nStart the API with: python run_api.py")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
