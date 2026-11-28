from typing import Any, Dict, Optional

from .convert_common import build_pojmy_from_elements, build_vocabulary_root, finalize_document


def ontology_dict_to_ofn(
    data: Dict[str, Any],
    vocabulary_iri: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Convert internal ontology.json dict (FilesystemOntologyStore format) to OFN Slovníky JSON.
    """
    if data is None:
        raise ValueError("ontology data cannot be None")

    vocab_iri = vocabulary_iri or data.get("uri")
    if not vocab_iri:
        raise ValueError("vocabulary IRI is required (use --base-iri or uri in input)")

    classes_input: Dict[str, Any] = data.get("classes") or {}
    attributes_input: Dict[str, Any] = data.get("attributes") or {}
    relationships_input: Dict[str, Any] = data.get("relationships") or {}

    classes = list(classes_input.values())
    attributes = list(attributes_input.values())
    relationships = []
    for rel in relationships_input.values():
        item = dict(rel)
        if not item.get("sourceClass") and item.get("domain"):
            item["sourceClass"] = item["domain"]
        if not item.get("targetClass") and item.get("range"):
            item["targetClass"] = item["range"]
        relationships.append(item)

    root = build_vocabulary_root(
        vocabulary_iri=vocab_iri,
        title_cs=data.get("label") or vocab_iri,
        description_cs=data.get("description"),
    )
    pojmy = build_pojmy_from_elements(vocab_iri, classes, attributes, relationships)
    return finalize_document(root, pojmy)
