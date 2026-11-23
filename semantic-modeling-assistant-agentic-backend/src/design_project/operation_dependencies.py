"""
Classes referenced by proposed attributes and relationships.

The modeler sometimes proposes attributes or relationships for a class that is not in the
ontology yet. Such a change cannot be applied on its own, so the missing class is proposed
alongside it and the modeler can review both together.
"""
import re
from dataclasses import replace
from typing import Iterable, List, Optional

from rdflib import URIRef

from design_project.domain import IdentifiedOperation
from ontology.domain import Ontology
from ontology.edit_operations import (
    CreateAttributeOperation,
    CreateClassOperation,
    CreateRelationshipOperation,
    OntologyEditOperation,
    UpdateAttributeOperation,
    UpdateClassOperation,
    UpdateRelationshipOperation,
)

AUTO_ADDED_CLASS_DESCRIPTION = (
    "Added automatically because other proposed changes refer to this class. "
    "Check its name and definition before keeping it."
)


def referenced_class_uris(operation: OntologyEditOperation) -> List[URIRef]:
    """Class URIs that must exist before the operation can be applied."""
    if isinstance(operation, (CreateAttributeOperation, UpdateAttributeOperation)):
        uris = [operation.owning_class_uri]
    elif isinstance(operation, (CreateRelationshipOperation, UpdateRelationshipOperation)):
        uris = [operation.source_class_uri, operation.target_class_uri]
    elif isinstance(operation, (CreateClassOperation, UpdateClassOperation)):
        uris = list(operation.generalization_uris or [])
    else:
        uris = []
    return [uri for uri in uris if uri]


def with_missing_referenced_classes(
    ontology: Ontology,
    operations: List[OntologyEditOperation],
    pending_operations: Iterable[IdentifiedOperation] = (),
) -> List[OntologyEditOperation]:
    """
    Prepend a create-class operation for every referenced class that neither exists in the
    ontology nor is created by the given operations.

    A class already proposed by another pending work item is copied from that proposal so
    its label and definition are kept; otherwise the label is derived from the URI.
    """
    created = {op.uri for op in operations if isinstance(op, CreateClassOperation)}
    pending_classes = {
        identified.operation.uri: identified.operation
        for identified in pending_operations
        if isinstance(identified.operation, CreateClassOperation)
    }

    added: List[OntologyEditOperation] = []
    for operation in operations:
        for uri in referenced_class_uris(operation):
            if uri in ontology.classes or uri in created:
                continue
            created.add(uri)
            added.append(_class_for(uri, pending_classes.get(uri)))
    return [*added, *operations]


def class_creates_first(operations: List[IdentifiedOperation]) -> List[IdentifiedOperation]:
    """Order operations so classes exist before attributes and relationships refer to them."""
    return sorted(operations, key=lambda identified: not isinstance(identified.operation, CreateClassOperation))


def _class_for(uri: URIRef, proposed: Optional[CreateClassOperation]) -> CreateClassOperation:
    if proposed is not None:
        return replace(proposed)
    return CreateClassOperation(
        uri=uri,
        label=label_from_uri(uri),
        description=AUTO_ADDED_CLASS_DESCRIPTION,
    )


def label_from_uri(uri: str) -> str:
    """'https://example.com/vocabulary#TechnickaZpusobilost' -> 'Technicka zpusobilost'."""
    local_name = re.split(r"[#/]", str(uri).rstrip("/#"))[-1]
    words = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", local_name).replace("_", " ").replace("-", " ").split()
    if not words:
        return str(uri)
    text = " ".join(words).lower()
    return text[0].upper() + text[1:]
