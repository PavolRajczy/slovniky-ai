from typing import Any, Dict, List, Optional

from .convert_common import build_pojmy_from_elements, build_vocabulary_root, finalize_document
from .iri import local_name_from_uri, pojem_iri


def _normalize_base_uri(uri: str) -> str:
    if not uri:
        return uri
    value = uri.strip()
    if not value.endswith("#") and not value.endswith("/"):
        return value + "#"
    return value


def _iri_to_full(iri: str, base_uri: str) -> str:
    if not iri:
        return iri
    if iri.startswith("http://") or iri.startswith("https://"):
        return iri
    base = _normalize_base_uri(base_uri)
    if base.endswith("#"):
        return base + iri
    return base.rstrip("/") + "#" + iri


def simplified_to_ofn(
    data: Dict[str, Any],
    vocabulary_iri: str,
    title_cs: Optional[str] = None,
    description_cs: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Convert DataSpecer simplified-semantic-model JSON to OFN Slovníky JSON.
    """
    if data is None:
        raise ValueError("simplified data cannot be None")
    if not vocabulary_iri:
        raise ValueError("vocabulary_iri is required")

    base = _normalize_base_uri(vocabulary_iri)
    vocab_root = base.rstrip("#").rstrip("/")

    classes_in: List[Dict[str, Any]] = data.get("classes") or []
    attributes_in: List[Dict[str, Any]] = data.get("attributes") or []
    relationships_in: List[Dict[str, Any]] = data.get("relationships") or []
    generalizations_in: List[Dict[str, Any]] = data.get("generalizations") or []

    classes: List[Dict[str, Any]] = []
    for item in classes_in:
        iri = item.get("iri")
        if not iri:
            continue
        full_uri = _iri_to_full(iri, vocab_root)
        classes.append({
            "uri": full_uri,
            "label": item.get("title") or local_name_from_uri(full_uri),
            "definition": item.get("description"),
            "description": item.get("description"),
            "kind": "object",
            "generalizations": [],
            "definition_references": [],
            "specification_references": [],
        })

    classes_by_short = {local_name_from_uri(c["uri"]): c for c in classes}
    classes_by_uri = {c["uri"]: c for c in classes}

    for gen in generalizations_in:
        special = gen.get("specialClass")
        general = gen.get("generalClass")
        if not special or not general:
            continue
        special_uri = _iri_to_full(special, vocab_root)
        general_uri = _iri_to_full(general, vocab_root)
        target = classes_by_uri.get(special_uri) or classes_by_short.get(special)
        if target is not None:
            target.setdefault("generalizations", []).append(general_uri)

    attributes: List[Dict[str, Any]] = []
    for item in attributes_in:
        iri = item.get("iri")
        if not iri:
            continue
        full_uri = _iri_to_full(iri, vocab_root)
        domain = item.get("domain")
        attributes.append({
            "uri": full_uri,
            "label": item.get("title") or local_name_from_uri(full_uri),
            "definition": item.get("description"),
            "description": item.get("description"),
            "owningClass": _iri_to_full(domain, vocab_root) if domain else None,
            "range": item.get("range") or "xsd:string",
            "definition_references": [],
            "specification_references": [],
        })

    relationships: List[Dict[str, Any]] = []
    for item in relationships_in:
        iri = item.get("iri")
        if not iri:
            continue
        full_uri = _iri_to_full(iri, vocab_root)
        domain = item.get("domain")
        range_val = item.get("range")
        relationships.append({
            "uri": full_uri,
            "label": item.get("title") or local_name_from_uri(full_uri),
            "definition": item.get("description"),
            "description": item.get("description"),
            "sourceClass": _iri_to_full(domain, vocab_root) if domain else None,
            "targetClass": _iri_to_full(range_val, vocab_root) if range_val else None,
            "definition_references": [],
            "specification_references": [],
        })

    inferred_title = title_cs
    if not inferred_title and classes:
        inferred_title = classes[0].get("label") or vocab_root

    root = build_vocabulary_root(
        vocabulary_iri=vocab_root,
        title_cs=inferred_title or vocab_root,
        description_cs=description_cs,
    )
    pojmy = build_pojmy_from_elements(vocab_root, classes, attributes, relationships)
    return finalize_document(root, pojmy)
