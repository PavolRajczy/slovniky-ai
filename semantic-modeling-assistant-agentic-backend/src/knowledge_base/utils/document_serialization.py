"""
Document serialization utilities for knowledge base components.

This module provides common functionality for converting KnowledgeDocument objects
to and from dictionary format for JSON serialization.
"""

from typing import Optional
from knowledge_base.domain import KnowledgeDocument, KnowledgeDocumentElement


def knowledge_document_content_to_dict(doc: KnowledgeDocument) -> dict:
    """
    Convert KnowledgeDocument content part to dictionary for JSON serialization.
    Only includes: id, title, content, contentSummary, childElements, elementType.
    
    Args:
        doc: The KnowledgeDocument to convert
        
    Returns:
        Dictionary representation of the document content part
    """
    def element_to_content_dict(element: KnowledgeDocumentElement) -> dict:
        return {
            'id': element.id,
            'title': element.title,
            'content': element.content,
            'contentSummary': element.contentSummary,
            'childElements': [element_to_content_dict(child) for child in element.childElements],
            'elementType': element.elementType
        }
    
    return element_to_content_dict(doc)


def knowledge_document_metadata_to_dict(doc: KnowledgeDocument) -> dict:
    """
    Convert KnowledgeDocument metadata part to dictionary for JSON serialization.
    Only includes: id, definedOntologyElements, specifiedOntologyElements, 
    referencedOntologyElements.
    
    Args:
        doc: The KnowledgeDocument to convert
        
    Returns:
        Dictionary representation of the document metadata part
    """
    def element_to_metadata_dict(element: KnowledgeDocumentElement) -> dict:
        metadata = {
            'id': element.id,
            'definedOntologyElements': element.definedOntologyElements,  # Store actual metadata
            'specifiedOntologyElements': element.specifiedOntologyElements,
            'referencedOntologyElements': element.referencedOntologyElements
        }
        
        # Include metadata for child elements
        child_metadata = {}
        for child in element.childElements:
            child_meta = element_to_metadata_dict(child)
            if any(child_meta[key] for key in ['definedOntologyElements', 'specifiedOntologyElements', 'referencedOntologyElements']):
                child_metadata[child.id] = child_meta
        
        if child_metadata:
            metadata['childElementsMetadata'] = child_metadata
            
        return metadata
    
    return element_to_metadata_dict(doc)


def knowledge_document_to_dict(doc: KnowledgeDocument) -> dict:
    """
    Convert KnowledgeDocument to dictionary for JSON serialization.
    This function is kept for backward compatibility and merges both content and metadata.
    
    Args:
        doc: The KnowledgeDocument to convert
        
    Returns:
        Dictionary representation of the complete document
    """
    def element_to_dict(element: KnowledgeDocumentElement) -> dict:
        return {
            'id': element.id,
            'title': element.title,
            'content': element.content,
            'contentSummary': element.contentSummary,
            'childElements': [element_to_dict(child) for child in element.childElements],
            'elementType': element.elementType,
            'definedOntologyElements': [],  # These are complex objects, skip for now
            'specifiedOntologyElements': [],
            'referencedOntologyElements': []
        }
    
    return element_to_dict(doc)


def dict_to_knowledge_document_content(content_data: dict) -> KnowledgeDocument:
    """
    Convert dictionary from JSON to KnowledgeDocument (content part only).
    
    Args:
        content_data: Dictionary containing the document content data
        
    Returns:
        KnowledgeDocument instance created from the content dictionary
    """
    def dict_to_content_element(elem_data: dict, parent=None) -> KnowledgeDocumentElement:
        # Check if this should be a KnowledgeDocument or KnowledgeDocumentElement
        element_type = elem_data.get('elementType', 'KnowledgeDocumentElement')
        
        if element_type in ['KnowledgeDocument', 'Document', 'LegalAct']:
            element = KnowledgeDocument(
                id=elem_data['id'],
                title=elem_data.get('title'),
                content=elem_data.get('content'),
                contentSummary=elem_data.get('contentSummary'),
                childElements=[],
                parentElement=parent,
                elementType=element_type
            )
        else:
            element = KnowledgeDocumentElement(
                id=elem_data['id'],
                title=elem_data.get('title'),
                content=elem_data.get('content'),
                contentSummary=elem_data.get('contentSummary'),
                childElements=[],
                parentElement=parent,
                elementType=element_type
            )
        
        # Recursively create child elements
        for child_data in elem_data.get('childElements', []):
            child_element = dict_to_content_element(child_data, parent=element)
            element.childElements.append(child_element)
        
        return element
    
    return dict_to_content_element(content_data)


def apply_metadata_to_knowledge_document(doc: KnowledgeDocument, metadata_data: dict) -> None:
    """
    Apply metadata from dictionary to an existing KnowledgeDocument.
    
    Args:
        doc: The KnowledgeDocument to update with metadata
        metadata_data: Dictionary containing the document metadata
    """
    def apply_metadata_to_element(element: KnowledgeDocumentElement, elem_metadata: dict) -> None:
        if elem_metadata.get('id') == element.id:
            # Apply metadata to this element
            element.definedOntologyElements = elem_metadata.get('definedOntologyElements', [])
            element.specifiedOntologyElements = elem_metadata.get('specifiedOntologyElements', [])
            element.referencedOntologyElements = elem_metadata.get('referencedOntologyElements', [])
            
            # Apply metadata to child elements if present
            child_metadata = elem_metadata.get('childElementsMetadata', {})
            for child in element.childElements:
                if child.id in child_metadata:
                    apply_metadata_to_element(child, child_metadata[child.id])
    
    apply_metadata_to_element(doc, metadata_data)


def merge_content_and_metadata(content_data: dict, metadata_data: dict) -> KnowledgeDocument:
    """
    Create a KnowledgeDocument by merging content and metadata dictionaries.
    
    Args:
        content_data: Dictionary containing the document content
        metadata_data: Dictionary containing the document metadata
        
    Returns:
        KnowledgeDocument instance with both content and metadata
    """
    doc = dict_to_knowledge_document_content(content_data)
    apply_metadata_to_knowledge_document(doc, metadata_data)
    return doc


def dict_to_knowledge_document(data: dict) -> KnowledgeDocument:
    """
    Convert dictionary from JSON to KnowledgeDocument.
    
    Args:
        data: Dictionary containing the document data
        
    Returns:
        KnowledgeDocument instance created from the dictionary
    """
    def dict_to_element(elem_data: dict, parent=None) -> KnowledgeDocumentElement:
        # Check if this should be a KnowledgeDocument or KnowledgeDocumentElement
        element_type = elem_data.get('elementType', 'KnowledgeDocumentElement')
        
        if element_type in ['KnowledgeDocument', 'Document', 'LegalAct']:
            element = KnowledgeDocument(
                id=elem_data['id'],
                title=elem_data.get('title'),
                content=elem_data.get('content'),
                contentSummary=elem_data.get('contentSummary'),
                childElements=[],
                parentElement=parent,
                elementType=element_type
            )
        else:
            element = KnowledgeDocumentElement(
                id=elem_data['id'],
                title=elem_data.get('title'),
                content=elem_data.get('content'),
                contentSummary=elem_data.get('contentSummary'),
                childElements=[],
                parentElement=parent,
                elementType=element_type
            )
        
        # Recursively create child elements
        for child_data in elem_data.get('childElements', []):
            child_element = dict_to_element(child_data, parent=element)
            element.childElements.append(child_element)
        
        return element
    
    return dict_to_element(data)
