"""
Knowledge Base Controller

Manages knowledge base documents and their relationship to ontology elements.
"""
from typing import List, Optional
from urllib.parse import unquote
from fastapi import APIRouter, HTTPException, status, Query
import logging

from knowledge_base.service import KnowledgeBaseService
from knowledge_base.domain import KnowledgeDocument, KnowledgeDocumentElement
from knowledge_base.document_loaders.document_loader_esel import ESELKnowledgeDocumentLoader
from knowledge_base.document_loaders.document_loader_local import LocalKnowledgeDocumentLoader
from knowledge_base.document_summarizers.document_summarizer_simple_openai import SimpleOpenAIKnowledgeDocumentSummarizer
from api.models import (
    KnowledgeDocumentSummary,
    KnowledgeDocument as KnowledgeDocumentModel,
    KnowledgeDocumentElement as KnowledgeDocumentElementModel,
    KnowledgeDocumentOutline
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize service
knowledge_base_service = KnowledgeBaseService(
    legal_knowledge_document_loader=ESELKnowledgeDocumentLoader(
        sparql_endpoint="https://opendata.eselpoint.cz/sparql"
    ),
    expert_knowledge_document_loader=LocalKnowledgeDocumentLoader(),
    document_summarizer=SimpleOpenAIKnowledgeDocumentSummarizer()
)


def _convert_element_to_model(element: KnowledgeDocumentElement) -> KnowledgeDocumentElementModel:
    """Convert domain KnowledgeDocumentElement to API model."""
    child_elements = [_convert_element_to_model(child) for child in element.childElements]
    
    return KnowledgeDocumentElementModel(
        id=element.id,
        title=element.title or "",
        content=element.content or "",
        content_summary=element.contentSummary or "",
        element_type=element.elementType,
        child_elements=child_elements,
        coverage=None
    )


def _convert_document_to_model(document: KnowledgeDocument) -> KnowledgeDocumentModel:
    """Convert domain KnowledgeDocument to API model."""
    child_elements = [_convert_element_to_model(elem) for elem in document.childElements]
    
    return KnowledgeDocumentModel(
        id=document.id,
        title=document.title or "",
        content=document.content or "",
        content_summary=document.contentSummary or "",
        element_type=document.elementType,
        child_elements=child_elements,
        coverage=None
    )


@router.get("/knowledge-base/legal", response_model=List[KnowledgeDocumentSummary])
async def list_legal_documents():
    """
    List available legal documents.
    
    Returns summary information for all legal documents in the knowledge base.
    """
    try:
        logger.info("Listing legal documents")
        documents = knowledge_base_service.list_legal_knowledge_documents()
        
        # Convert to KnowledgeDocumentSummary model
        return [
            KnowledgeDocumentSummary(
                id=doc["id"],
                title=doc["title"],
                content_summary=doc["contentSummary"],
                element_type=doc["elementType"]
            )
            for doc in documents
        ]
    except Exception as e:
        logger.error(f"Error listing legal documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list legal documents: {str(e)}"
        )


@router.get("/knowledge-base/expert", response_model=List[KnowledgeDocumentSummary])
async def list_expert_documents():
    """
    List available expert documents.
    
    Returns summary information for all expert documents in the knowledge base.
    """
    try:
        logger.info("Listing expert documents")
        documents = knowledge_base_service.list_expert_knowledge_documents()
        
        # Convert to KnowledgeDocumentSummary model
        return [
            KnowledgeDocumentSummary(
                id=doc["id"],
                title=doc["title"],
                content_summary=doc["contentSummary"],
                element_type=doc["elementType"]
            )
            for doc in documents
        ]
    except Exception as e:
        logger.error(f"Error listing expert documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list expert documents: {str(e)}"
        )


@router.get("/knowledge-base/documents/{document_id:path}/outline", response_model=KnowledgeDocumentOutline)
async def get_knowledge_document_outline(document_id: str):
    """
    Get a summarized outline of a knowledge document based on element summaries.
    
    Args:
        document_id: The ID of the knowledge document (URL-encoded)
    
    Returns:
        Hierarchical XML outline of the document
    """
    try:
        decoded_id = unquote(document_id)
        logger.info(f"Getting knowledge document outline: {decoded_id}")
        
        # Try to load from legal documents first, then expert documents
        try:
            documents = knowledge_base_service.load_legal_knowledge_documents([decoded_id])
        except:
            documents = knowledge_base_service.load_expert_knowledge_documents([decoded_id])
        
        if not documents:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledge document with ID '{document_id}' not found"
            )
        
        document = documents[0]
        outline = knowledge_base_service.get_knowledge_document_outline_from_summaries(document)
        
        return KnowledgeDocumentOutline(
            id=document.id,
            title=document.title or "",
            content_summary=document.contentSummary or "",
            outline=outline
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting knowledge document outline: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get knowledge document outline: {str(e)}"
        )


@router.get("/knowledge-base/documents/{document_id:path}", response_model=KnowledgeDocumentModel)
async def get_knowledge_document(document_id: str):
    """
    Get a specific knowledge document with its full content and hierarchical structure.
    
    User Story: Read knowledge base document
    
    Args:
        document_id: The ID of the knowledge document (URL-encoded)
    
    Returns:
        Complete knowledge document with hierarchical structure
    """
    try:
        decoded_id = unquote(document_id)
        logger.info(f"Getting knowledge document: {decoded_id}")
        
        # Try to load from legal documents first, then expert documents
        try:
            documents = knowledge_base_service.load_legal_knowledge_documents([decoded_id])
        except:
            documents = knowledge_base_service.load_expert_knowledge_documents([decoded_id])
        
        if not documents:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Knowledge document with ID '{document_id}' not found"
            )
        
        return _convert_document_to_model(documents[0])
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting knowledge document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get knowledge document: {str(e)}"
        )
