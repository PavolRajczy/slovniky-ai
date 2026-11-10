"""Shared setup for tests marked ``live`` (real e-Sbírka endpoint and LLM API)."""
from design_project.design_task_patterns_factory import DesignTaskPatternsFactory_Basic
from design_project.domain import DesignProject, KnowledgeDomain, KnowledgeDomainArea
from knowledge_base.document_loaders.document_loader_esel import ESELKnowledgeDocumentLoader
from knowledge_base.document_loaders.document_loader_local import LocalKnowledgeDocumentLoader
from knowledge_base.document_summarizers.document_summarizer_simple_openai import SimpleOpenAIKnowledgeDocumentSummarizer
from knowledge_base.domain import KnowledgeDocument
from knowledge_base.service import ESEL_SPARQL_ENDPOINT, LEGAL_DOCUMENT_ID_PREFIX, KnowledgeBaseService
from ontology.domain import Ontology

LIVE_LEGAL_DOCUMENT_ID = f"{LEGAL_DOCUMENT_ID_PREFIX}/2001/56/2025-07-01"
LIVE_DATA_DIR = "data_test/knowledge_base"


def create_live_knowledge_base_service() -> KnowledgeBaseService:
    return KnowledgeBaseService(
        legal_knowledge_document_loader=ESELKnowledgeDocumentLoader(
            ESEL_SPARQL_ENDPOINT,
            base_dir=f"{LIVE_DATA_DIR}/esel",
        ),
        expert_knowledge_document_loader=LocalKnowledgeDocumentLoader(base_dir=f"{LIVE_DATA_DIR}/local"),
        document_summarizer=SimpleOpenAIKnowledgeDocumentSummarizer(),
    )


def create_vehicle_domain() -> KnowledgeDomain:
    return KnowledgeDomain(
        label="Doména silničních vozidel a jejich provozu",
        description="Tato doména pokrývá znalosti týkající se různých typů silničních vozidel, jejich technických specifikací, registrace, a pravidel provozu na pozemních komunikacích.",
        areas=[],
    )


def create_registration_area(domain: KnowledgeDomain) -> KnowledgeDomainArea:
    return KnowledgeDomainArea(
        id="area-registration",
        label="Registrace vozidel",
        description="Oblast zabývající se registračními postupy, požadavky a dokumenty pro silniční vozidla.",
        parent=domain,
        keyConcepts=["registrace", "vozidlo", "technický průkaz", "státní poznávací značka"],
        modelingClasses=[],
        modelingAttributes=[],
        modelingRelationships=[],
        explainingKnowledgeResources=[],
    )


def create_vehicle_project(key_document: KnowledgeDocument, domain: KnowledgeDomain) -> DesignProject:
    return DesignProject(
        id="test-project-1",
        name="Test Vehicle Registration Project",
        finishedIterations=[],
        currentIteration=None,
        plannedIterations=[],
        patterns=DesignTaskPatternsFactory_Basic.get_design_task_patterns(),
        patternsFactoryId=DesignTaskPatternsFactory_Basic.get_factory_id(),
        legalKnowledgeBase=[key_document],
        expertKnowledgeBase=[],
        keyKnowledgeDocument=key_document,
        modeledKnowledgeDomain=domain,
        designedOntology=Ontology(
            uri="https://example.org/test-ontology#",
            label="Test Vehicle Ontology",
            description="A test ontology for vehicle registration domain.",
            classes={},
            attributes={},
            relationships={},
        ),
    )
