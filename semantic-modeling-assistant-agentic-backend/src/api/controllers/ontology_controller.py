"""
Ontology Controller

Manages ontologies independently from design projects.
"""
from typing import List
from urllib.parse import unquote
from fastapi import APIRouter, HTTPException, status
from rdflib import URIRef
import logging

from ontology.service import OntologyService
from ontology.domain import Ontology, OntologyClass, OntologyAttribute, OntologyRelationship
from api.models import (
    OntologyModel,
    OntologyMetadata,
    OntologyClassModel,
    OntologyAttributeModel,
    OntologyRelationshipModel,
    CreateOntologyRequest,
    UpdateOntologyRequest
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize service
ontology_service = OntologyService()


def _convert_ontology_to_model(ontology: Ontology) -> OntologyModel:
    """Convert domain Ontology to API OntologyModel."""
    classes = []
    for ont_class in ontology.classes.values():
        classes.append(OntologyClassModel(
            uri=str(ont_class.uri),
            label=ont_class.label,
            definition=ont_class.definition,
            description=ont_class.description,
            parent_classes=[str(g.uri) for g in ont_class.generalizations],
            definition_references=ont_class.definition_references if hasattr(ont_class, 'definition_references') else [],
            specification_references=ont_class.specification_references if hasattr(ont_class, 'specification_references') else [],
            references=ont_class.references if hasattr(ont_class, 'references') else []
        ))
    
    attributes = []
    for ont_attr in ontology.attributes.values():
        attributes.append(OntologyAttributeModel(
            uri=str(ont_attr.uri),
            label=ont_attr.label,
            definition=ont_attr.definition,
            description=ont_attr.description,
            domain_class=str(ont_attr.owningClass.uri),
            range_type="string",  # Simplified - actual implementation would extract from RDF
            definition_references=ont_attr.definition_references if hasattr(ont_attr, 'definition_references') else [],
            specification_references=ont_attr.specification_references if hasattr(ont_attr, 'specification_references') else [],
            references=ont_attr.references if hasattr(ont_attr, 'references') else []
        ))
    
    relationships = []
    for ont_rel in ontology.relationships.values():
        relationships.append(OntologyRelationshipModel(
            uri=str(ont_rel.uri),
            label=ont_rel.label,
            definition=ont_rel.definition,
            description=ont_rel.description,
            domain_class=str(ont_rel.sourceClass.uri),
            range_class=str(ont_rel.targetClass.uri),
            definition_references=ont_rel.definition_references if hasattr(ont_rel, 'definition_references') else [],
            specification_references=ont_rel.specification_references if hasattr(ont_rel, 'specification_references') else [],
            references=ont_rel.references if hasattr(ont_rel, 'references') else []
        ))
    
    return OntologyModel(
        uri=str(ontology.uri),
        label=ontology.label,
        description=ontology.description or "",
        classes=classes,
        attributes=attributes,
        relationships=relationships
    )


@router.get("/ontologies", response_model=List[OntologyMetadata])
async def list_ontologies():
    """
    List all available ontologies.
    
    Returns metadata for all ontologies in the system.
    """
    try:
        logger.info("Listing all ontologies")
        ontologies = ontology_service.list_ontologies()
        return [
            OntologyMetadata(
                uri=str(o.uri),
                label=o.label,
                description=o.description or ""
            ) for o in ontologies
        ]
    except Exception as e:
        logger.error(f"Error listing ontologies: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list ontologies: {str(e)}"
        )


@router.get("/ontologies/{ontology_uri:path}", response_model=OntologyModel)
async def get_ontology(ontology_uri: str):
    """
    Get a specific ontology by URI.
    
    Args:
        ontology_uri: The URI of the ontology (URL-encoded)
    
    Returns:
        Complete ontology with all classes, attributes, and relationships
    """
    try:
        # Decode the URI
        decoded_uri = unquote(ontology_uri)
        logger.info(f"Getting ontology: {decoded_uri}")
        
        ontology = ontology_service.load_ontology(decoded_uri)
        return _convert_ontology_to_model(ontology)
    
    except FileNotFoundError:
        logger.warning(f"Ontology not found: {ontology_uri}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ontology with URI '{ontology_uri}' not found"
        )
    except ValueError as e:
        logger.error(f"Invalid ontology URI: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting ontology: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get ontology: {str(e)}"
        )


@router.post("/ontologies", response_model=OntologyMetadata, status_code=status.HTTP_201_CREATED)
async def create_ontology(request: CreateOntologyRequest):
    """
    Create a new empty ontology.
    
    User Story: Create a new empty ontology
    
    Args:
        request: Ontology creation request with URI, label, and description
    
    Returns:
        Metadata of the created ontology
    """
    try:
        logger.info(f"Creating ontology: {request.ontology_uri}")
        
        # Check if ontology already exists
        if ontology_service.ontology_exists(request.ontology_uri):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ontology with URI '{request.ontology_uri}' already exists"
            )
        
        # Create the ontology
        ontology = ontology_service.create_empty_ontology(
            ontology_uri=request.ontology_uri,
            label=request.ontology_label,
            description=request.ontology_description
        )
        
        # Store it
        ontology_service.store_ontology(ontology)
        
        return OntologyMetadata(
            uri=str(ontology.uri),
            label=ontology.label,
            description=ontology.description or ""
        )
    
    except ValueError as e:
        logger.error(f"Invalid ontology data: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating ontology: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create ontology: {str(e)}"
        )


@router.put("/ontologies/{ontology_uri:path}", response_model=OntologyMetadata)
async def update_ontology(ontology_uri: str, request: UpdateOntologyRequest):
    """
    Update ontology metadata (label, description).
    
    User Story: Change an existing ontology
    
    Args:
        ontology_uri: The URI of the ontology (URL-encoded)
        request: Update request with new label and/or description
    
    Returns:
        Updated ontology metadata
    """
    try:
        # Decode the URI
        decoded_uri = unquote(ontology_uri)
        logger.info(f"Updating ontology: {decoded_uri}")
        
        # Load the ontology
        ontology = ontology_service.load_ontology(decoded_uri)
        
        # Update metadata
        if request.ontology_label is not None:
            ontology.label = request.ontology_label
        
        if request.ontology_description is not None:
            ontology.description = request.ontology_description
        
        # Store the updated ontology
        ontology_service.store_ontology(ontology)
        
        return OntologyMetadata(
            uri=str(ontology.uri),
            label=ontology.label,
            description=ontology.description or ""
        )
    
    except FileNotFoundError:
        logger.warning(f"Ontology not found: {ontology_uri}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ontology with URI '{ontology_uri}' not found"
        )
    except ValueError as e:
        logger.error(f"Invalid update data: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating ontology: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update ontology: {str(e)}"
        )
