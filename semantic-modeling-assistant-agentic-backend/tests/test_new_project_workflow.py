"""
Quick test to verify the new project creation workflow.
This is not a rigorous test, just a smoke test to ensure the basic flow works.
"""

from design_project.service import DesignProjectService
from design_project.store import FileSystemDesignProjectStore
from ontology.service import OntologyService
from knowledge_base.service import KnowledgeBaseService
from knowledge_base.document_loaders.document_loader_esel import ESELKnowledgeDocumentLoader
from knowledge_base.document_loaders.document_loader_local import LocalKnowledgeDocumentLoader
from knowledge_base.document_summarizers.document_summarizer_simple_openai import SimpleOpenAIKnowledgeDocumentSummarizer
from knowledge_base_index.service import KnowledgeBaseIndexService
from knowledge_base_index.indexers.faiss_summary_openai_indexer import FAISSSummaryOpenAIKnowledgeDocumentIndexer
from agents.knowledge_domain_area_analyzers.knowledge_domain_area_analyzer_openai_simple import KnowledgeDomainAreaAnalyzerAgent_Simple_OpenAI
from agents.iteration_suggesters.iteration_suggester_openai_simple import IterationSuggesterAgent_Simple_OpenAI
from agents.task_planners.task_planner_openai_simple import TaskPlannerAgent_Simple_OpenAI
from agents.modelers.modeler_openai_basic import ModelerAgent_Simple_OpenAI


def test_new_project_workflow():
    """
    Test the new multi-step project creation workflow:
    1. Create empty project
    2. Add knowledge documents
    3. Set key document
    4. Generate domain areas
    """
    
    # Setup services
    ontology_service = OntologyService()
    knowledge_base_service = KnowledgeBaseService(
        legal_knowledge_document_loader=ESELKnowledgeDocumentLoader(
            sparql_endpoint="https://opendata.eselpoint.cz/sparql"
        ),
        expert_knowledge_document_loader=LocalKnowledgeDocumentLoader(),
        document_summarizer=SimpleOpenAIKnowledgeDocumentSummarizer()
    )
    knowledge_base_index_service = KnowledgeBaseIndexService(
        indexer=FAISSSummaryOpenAIKnowledgeDocumentIndexer()
    )
    
    design_project_service = DesignProjectService(
        store=FileSystemDesignProjectStore(ontology_service=ontology_service),
        knowledge_base_service=knowledge_base_service,
        ontology_service=ontology_service,
        knowledge_domain_area_analyzer_agent=KnowledgeDomainAreaAnalyzerAgent_Simple_OpenAI(
            knowledge_base_service=knowledge_base_service
        ),
        iteration_suggester_agent=IterationSuggesterAgent_Simple_OpenAI(
            knowledge_base_service=knowledge_base_service,
            knowledge_base_index_service=knowledge_base_index_service
        ),
        task_planner_agent=TaskPlannerAgent_Simple_OpenAI(
            knowledge_base_service=knowledge_base_service,
            knowledge_base_index_service=knowledge_base_index_service
        ),
        modeler_agent=ModelerAgent_Simple_OpenAI(
            knowledge_base_service=knowledge_base_service,
            knowledge_base_index_service=knowledge_base_index_service
        )
    )
    
    print("\n" + "="*70)
    print("Testing New Project Creation Workflow")
    print("="*70)
    
    # Step 1: Create empty project
    print("\n[Step 1] Creating empty project...")
    project = design_project_service.initialize_new_project(
        project_name="Test Traffic Regulations Project",
        working_ontology_uri="https://slovník.gov.cz/datový/turistické-cíle",
        knowledge_domain_name="Traffic Regulations",
        knowledge_domain_description="Domain covering traffic rules and regulations"
    )
    
    print(f"✓ Created project: {project.id}")
    print(f"  - Name: {project.name}")
    print(f"  - Knowledge domain: {project.modeledKnowledgeDomain.label}")
    print(f"  - Legal documents: {len(project.legalKnowledgeBase)}")
    print(f"  - Expert documents: {len(project.expertKnowledgeBase)}")
    print(f"  - Domain areas: {len(project.modeledKnowledgeDomain.areas)}")
    print(f"  - Key document: {project.keyKnowledgeDocument}")
    
    assert len(project.legalKnowledgeBase) == 0, "Should have no legal documents"
    assert len(project.expertKnowledgeBase) == 0, "Should have no expert documents"
    assert len(project.modeledKnowledgeDomain.areas) == 0, "Should have no domain areas"
    assert project.keyKnowledgeDocument is None, "Should have no key document"
    
    # Step 2: Add knowledge documents
    print("\n[Step 2] Adding knowledge documents...")
    legal_doc_id = "https://www.zakonyprolidi.cz/cs/2000-361"
    
    # Load and add legal document
    legal_docs = knowledge_base_service.load_legal_knowledge_documents([legal_doc_id])
    project.legalKnowledgeBase.extend(legal_docs)
    design_project_service.save_project(project)
    
    print(f"✓ Added legal documents: {len(legal_docs)}")
    for doc in legal_docs:
        print(f"  - {doc.title}")
    
    # Step 3: Set key document
    print("\n[Step 3] Setting key knowledge document...")
    project = design_project_service.set_key_knowledge_document(
        project_id=project.id,
        document_id=legal_doc_id
    )
    
    print(f"✓ Set key document: {project.keyKnowledgeDocument.title}")
    assert project.keyKnowledgeDocument is not None, "Should have key document"
    assert project.keyKnowledgeDocument.id == legal_doc_id, "Should be the correct document"
    
    # Step 4: Generate domain areas
    print("\n[Step 4] Generating domain areas...")
    areas = design_project_service.generate_domain_areas(
        project_id=project.id,
        user_instruction=""
    )
    
    print(f"✓ Generated {len(areas)} domain areas:")
    for area in areas:
        print(f"  - {area.label}: {area.description}")
        print(f"    Key concepts: {', '.join(area.keyConcepts[:5])}")
    
    assert len(areas) > 0, "Should have generated domain areas"
    
    # Verify final project state
    print("\n[Final State] Project verification...")
    final_project = design_project_service.load_project(project.id)
    
    print(f"✓ Final project state:")
    print(f"  - Legal documents: {len(final_project.legalKnowledgeBase)}")
    print(f"  - Expert documents: {len(final_project.expertKnowledgeBase)}")
    print(f"  - Domain areas: {len(final_project.modeledKnowledgeDomain.areas)}")
    print(f"  - Key document: {final_project.keyKnowledgeDocument.title if final_project.keyKnowledgeDocument else None}")
    
    assert len(final_project.legalKnowledgeBase) == 1, "Should have 1 legal document"
    assert len(final_project.modeledKnowledgeDomain.areas) > 0, "Should have domain areas"
    assert final_project.keyKnowledgeDocument is not None, "Should have key document"
    
    print("\n" + "="*70)
    print("✓ All tests passed!")
    print("="*70)
    
    return project.id


def test_error_cases():
    """
    Test error cases for the new workflow.
    """
    
    # Setup services (minimal for testing)
    ontology_service = OntologyService()
    knowledge_base_service = KnowledgeBaseService(
        legal_knowledge_document_loader=ESELKnowledgeDocumentLoader(
            sparql_endpoint="https://opendata.eselpoint.cz/sparql"
        ),
        expert_knowledge_document_loader=LocalKnowledgeDocumentLoader(),
        document_summarizer=SimpleOpenAIKnowledgeDocumentSummarizer()
    )
    knowledge_base_index_service = KnowledgeBaseIndexService(
        indexer=FAISSSummaryOpenAIKnowledgeDocumentIndexer()
    )
    
    design_project_service = DesignProjectService(
        store=FileSystemDesignProjectStore(ontology_service=ontology_service),
        knowledge_base_service=knowledge_base_service,
        ontology_service=ontology_service,
        knowledge_domain_area_analyzer_agent=KnowledgeDomainAreaAnalyzerAgent_Simple_OpenAI(
            knowledge_base_service=knowledge_base_service
        ),
        iteration_suggester_agent=IterationSuggesterAgent_Simple_OpenAI(
            knowledge_base_service=knowledge_base_service,
            knowledge_base_index_service=knowledge_base_index_service
        ),
        task_planner_agent=TaskPlannerAgent_Simple_OpenAI(
            knowledge_base_service=knowledge_base_service,
            knowledge_base_index_service=knowledge_base_index_service
        ),
        modeler_agent=ModelerAgent_Simple_OpenAI(
            knowledge_base_service=knowledge_base_service,
            knowledge_base_index_service=knowledge_base_index_service
        )
    )
    
    print("\n" + "="*70)
    print("Testing Error Cases")
    print("="*70)
    
    # Create empty project
    project = design_project_service.initialize_new_project(
        project_name="Error Test Project",
        working_ontology_uri="https://slovník.gov.cz/datový/turistické-cíle",
        knowledge_domain_name="Test Domain"
    )
    
    # Test 1: Try to set key document that doesn't exist in knowledge base
    print("\n[Test 1] Setting non-existent key document...")
    try:
        design_project_service.set_key_knowledge_document(
            project_id=project.id,
            document_id="non-existent-doc-id"
        )
        print("✗ Should have raised ValueError")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"✓ Correctly raised ValueError: {e}")
    
    # Test 2: Try to generate domain areas without setting key document
    print("\n[Test 2] Generating domain areas without key document...")
    try:
        design_project_service.generate_domain_areas(
            project_id=project.id
        )
        print("✗ Should have raised ValueError")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        print(f"✓ Correctly raised ValueError: {e}")
    
    print("\n" + "="*70)
    print("✓ All error tests passed!")
    print("="*70)


if __name__ == "__main__":
    # Run the main workflow test
    project_id = test_new_project_workflow()
    
    # Run error case tests
    test_error_cases()
    
    print(f"\n✓ Test completed successfully!")
    print(f"  Created project ID: {project_id}")
