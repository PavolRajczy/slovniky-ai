"""
Convert between our Ontology domain model and DataSpecer simplified-semantic-model format.

Export (ontology → simplified): used when sending data to DataSpecer API or saving for the tool.
IRIs in the ontology's namespace are shortened (e.g. https://example.com/vocabulary#zoo → zoo);
external URIs (e.g. foaf:Organization) stay full. This keeps our internal format unchanged so
GPT prompts and other code continue to work with full URIs and our structure.

Import (simplified → ontology): when loading from DataSpecer URL, expand short IRIs using base_uri
and build our Ontology model for storage as ontology.json.

Schema: https://schemas.dataspecer.com/adapters/simplified-semantic-model.v1.0.schema.json
"""

from typing import Any, Dict, List

from rdflib import URIRef

from .domain import (
    Ontology,
    OntologyClass,
    OntologyAttribute,
    OntologyRelationship,
    Kind,
)

SIMPLIFIED_SCHEMA = "https://schemas.dataspecer.com/adapters/simplified-semantic-model.v1.0.schema.json"
DEFAULT_CARDINALITY = "many"


def _normalize_base_uri(uri: str) -> str:
    """Ensure base URI ends with # or / for appending local names."""
    if not uri:
        return uri
    s = uri.strip()
    if not s.endswith("#") and not s.endswith("/"):
        return s + "#"
    return s


def _local_name(full_uri: str) -> str:
    """Extract local name (fragment or last path segment) from full URI."""
    if "#" in full_uri:
        return full_uri.split("#")[-1]
    if "/" in full_uri:
        return full_uri.rstrip("/").split("/")[-1]
    return full_uri


def _iri_to_simplified(uri_str: str, base_uri: str) -> str:
    """Convert full URI to simplified IRI: short if in base namespace, else full."""
    if not uri_str or not uri_str.startswith("http"):
        return uri_str
    base = _normalize_base_uri(base_uri)
    if uri_str.startswith(base) or uri_str + "#" == base or uri_str + "/" == base.rstrip("#"):
        return _local_name(uri_str)
    if uri_str == base.rstrip("#").rstrip("/"):
        return _local_name(base.rstrip("#").rstrip("/"))
    # Check without trailing # on base
    base_plain = base.rstrip("#").rstrip("/")
    if uri_str == base_plain or uri_str.startswith(base_plain + "#") or uri_str.startswith(base_plain + "/"):
        return _local_name(uri_str)
    return uri_str


def _iri_to_full(iri: str, base_uri: str) -> str:
    """Convert simplified IRI (short or full) to full URI."""
    if not iri:
        return iri
    if iri.startswith("http://") or iri.startswith("https://"):
        return iri
    base = _normalize_base_uri(base_uri)
    if base.endswith("#"):
        return base + iri
    return base.rstrip("/") + "#" + iri


def _is_in_base_namespace(uri_str: str, base_uri: str) -> bool:
    """True if uri_str is in the ontology base namespace (not an external vocabulary)."""
    if not uri_str or not uri_str.startswith("http"):
        return False
    base = _normalize_base_uri(base_uri)
    base_plain = base.rstrip("#").rstrip("/")
    return (
        uri_str == base_plain
        or uri_str.startswith(base_plain + "#")
        or uri_str.startswith(base_plain + "/")
        or uri_str.startswith(base)
    )


def ontology_to_simplified(ontology: Ontology) -> Dict[str, Any]:
    """
    Export our Ontology to DataSpecer simplified-semantic-model JSON.
    Internal ontology format and GPT prompts stay unchanged; only the exported payload is transformed.
    """
    if ontology is None:
        return {
            "$schema": SIMPLIFIED_SCHEMA,
            "classes": [],
            "attributes": [],
            "relationships": [],
            "generalizations": [],
        }
    base_uri = _normalize_base_uri(str(ontology.uri))

    classes_out: List[Dict[str, Any]] = []
    for cls in ontology.classes.values():
        uri_str = str(cls.uri)
        if not _is_in_base_namespace(uri_str, base_uri):
            continue
        iri = _iri_to_simplified(uri_str, base_uri)
        title = cls.label or ""
        desc = (cls.description or cls.definition) or ""
        classes_out.append({"iri": iri, "title": title, "description": desc})

    attributes_out: List[Dict[str, Any]] = []
    for attr in ontology.attributes.values():
        uri_str = str(attr.uri)
        if not _is_in_base_namespace(uri_str, base_uri):
            continue
        iri = _iri_to_simplified(uri_str, base_uri)
        title = attr.label or ""
        desc = (attr.description or attr.definition) or ""
        domain = _iri_to_simplified(str(attr.owningClass.uri), base_uri) if attr.owningClass and attr.owningClass.uri else ""
        attributes_out.append({
            "iri": iri,
            "title": title,
            "description": desc,
            "domain": domain,
            "domainCardinality": DEFAULT_CARDINALITY,
            "range": "",
            "rangeCardinality": DEFAULT_CARDINALITY,
        })

    def _source_uri(rel: OntologyRelationship) -> str:
        """Get source class URI from relationship; fallback: find class that has rel in outgoingRelationships."""
        if getattr(rel, "sourceClass", None) and getattr(rel.sourceClass, "uri", None):
            return str(rel.sourceClass.uri)
        for cls in ontology.classes.values():
            if rel in getattr(cls, "outgoingRelationships", []):
                if getattr(cls, "uri", None):
                    return str(cls.uri)
                break
        return ""

    def _target_uri(rel: OntologyRelationship) -> str:
        """Get target class URI from relationship; fallback: find class that has rel in incomingRelationships."""
        if getattr(rel, "targetClass", None) and getattr(rel.targetClass, "uri", None):
            return str(rel.targetClass.uri)
        for cls in ontology.classes.values():
            if rel in getattr(cls, "incomingRelationships", []):
                if getattr(cls, "uri", None):
                    return str(cls.uri)
                break
        return ""

    relationships_out: List[Dict[str, Any]] = []
    for rel in ontology.relationships.values():
        if not _is_in_base_namespace(str(rel.uri), base_uri):
            continue
        iri = _iri_to_simplified(str(rel.uri), base_uri)
        title = rel.label or ""
        desc = (rel.description or rel.definition) or ""
        src_uri = _source_uri(rel)
        tgt_uri = _target_uri(rel)
        domain = _iri_to_simplified(src_uri, base_uri) if src_uri else ""
        range_val = _iri_to_simplified(tgt_uri, base_uri) if tgt_uri else ""
        relationships_out.append({
            "iri": iri,
            "title": title,
            "description": desc,
            "domain": domain,
            "domainCardinality": DEFAULT_CARDINALITY,
            "range": range_val,
            "rangeCardinality": DEFAULT_CARDINALITY,
        })

    generalizations_out: List[Dict[str, Any]] = []
    for cls in ontology.classes.values():
        if not _is_in_base_namespace(str(cls.uri), base_uri):
            continue
        for gen in cls.generalizations or []:
            if not getattr(gen, "uri", None):
                continue
            if not _is_in_base_namespace(str(gen.uri), base_uri):
                continue
            general_iri = _iri_to_simplified(str(gen.uri), base_uri)
            special_iri = _iri_to_simplified(str(cls.uri), base_uri)
            generalizations_out.append({
                "iri": f"{special_iri}-{general_iri}",
                "title": "",
                "description": "",
                "generalClass": general_iri,
                "specialClass": special_iri,
            })

    return {
        "$schema": SIMPLIFIED_SCHEMA,
        "classes": classes_out,
        "attributes": attributes_out,
        "relationships": relationships_out,
        "generalizations": generalizations_out,
    }


def simplified_to_ontology(data: Dict[str, Any], base_uri: str) -> Ontology:
    """
    Import from DataSpecer simplified-semantic-model JSON into our Ontology model.
    Short IRIs are expanded with base_uri; full URIs are kept as-is.
    """
    if data is None:
        raise ValueError("simplified data cannot be None")
    base = _normalize_base_uri(base_uri)

    classes_in: List[Dict[str, Any]] = data.get("classes") or []
    relationships_in: List[Dict[str, Any]] = data.get("relationships") or []
    attributes_in: List[Dict[str, Any]] = data.get("attributes") or []
    generalizations_in: List[Dict[str, Any]] = data.get("generalizations") or []

    classes_by_id: Dict[str, OntologyClass] = {}
    for c in classes_in:
        iri = c.get("iri")
        if not iri:
            continue
        full_uri = _iri_to_full(iri, base)
        title = c.get("title") or ""
        desc = c.get("description") or ""
        cls_obj = OntologyClass(
            uri=URIRef(full_uri),
            label=title,
            definition=desc,
            description=desc,
            kind=Kind.OBJECT,
            definition_references=[],
            specification_references=[],
            references=[],
        )
        classes_by_id[full_uri] = cls_obj

    def resolve_class_ref(ref: str):
        if not ref:
            return None
        full = _iri_to_full(ref, base)
        if full not in classes_by_id:
            classes_by_id[full] = OntologyClass(
                uri=URIRef(full),
                label=ref,
                definition=None,
                description=None,
                kind=Kind.OBJECT,
                definition_references=[],
                specification_references=[],
                references=[],
            )
        return classes_by_id[full]

    attrs_by_id: Dict[str, OntologyAttribute] = {}
    for a in attributes_in:
        iri = a.get("iri")
        if not iri:
            continue
        full_uri = _iri_to_full(iri, base)
        domain_ref = a.get("domain")
        owning = resolve_class_ref(domain_ref) if domain_ref else None
        attr_obj = OntologyAttribute(
            uri=URIRef(full_uri),
            label=a.get("title") or "",
            definition=a.get("description") or "",
            description=a.get("description") or "",
            owningClass=owning,
            definition_references=[],
            specification_references=[],
            references=[],
        )
        attrs_by_id[full_uri] = attr_obj
        if owning:
            owning.attributes.append(attr_obj)

    rels_by_id: Dict[str, OntologyRelationship] = {}
    for r in relationships_in:
        iri = r.get("iri")
        if not iri:
            continue
        full_uri = _iri_to_full(iri, base)
        src = resolve_class_ref(r.get("domain"))
        tgt = resolve_class_ref(r.get("range"))
        rel_obj = OntologyRelationship(
            uri=URIRef(full_uri),
            label=r.get("title") or "",
            definition=r.get("description") or "",
            description=r.get("description") or "",
            sourceClass=src,
            targetClass=tgt,
            definition_references=[],
            specification_references=[],
            references=[],
        )
        rels_by_id[full_uri] = rel_obj
        if src:
            src.outgoingRelationships.append(rel_obj)
        if tgt:
            tgt.incomingRelationships.append(rel_obj)

    for g in generalizations_in:
        general_ref = g.get("generalClass")
        special_ref = g.get("specialClass")
        if not general_ref or not special_ref:
            continue
        general_full = _iri_to_full(general_ref, base)
        special_full = _iri_to_full(special_ref, base)
        gen_cls = classes_by_id.get(general_full)
        spec_cls = classes_by_id.get(special_full)
        if gen_cls and spec_cls:
            if gen_cls not in spec_cls.generalizations:
                spec_cls.generalizations.append(gen_cls)
            if spec_cls not in gen_cls.specializations:
                gen_cls.specializations.append(spec_cls)

    ontology_uri_ref = URIRef(base)
    return Ontology(
        uri=ontology_uri_ref,
        label="",
        description=None,
        classes={URIRef(k): v for k, v in classes_by_id.items()},
        attributes={URIRef(k): v for k, v in attrs_by_id.items()},
        relationships={URIRef(k): v for k, v in rels_by_id.items()},
    )
