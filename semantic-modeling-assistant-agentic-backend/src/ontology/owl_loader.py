"""
Load an ontology from an OWL/RDF URL (GET request).
Supports Turtle (.ttl) and RDF/OWL XML. Converts to the internal Ontology domain model and can be stored via OntologyService.

Optional: merge external vocabularies (e.g. FOAF) so that domain/range references like
<http://xmlns.com/foaf/0.1/Organization> resolve to full class definitions. FOAF TTL artifact:
https://datagov-cz.github.io/cache-slovniku/foaf.ttl
"""

from typing import List, Optional

import requests
from rdflib import Graph, URIRef
from rdflib.namespace import RDF, RDFS, OWL

from .domain import Ontology, OntologyClass, OntologyAttribute, OntologyRelationship, Kind


OWL_NS = "http://www.w3.org/2002/07/owl#"
RDFS_NS = "http://www.w3.org/2000/01/rdf-schema#"


def _get_label(g: Graph, subject: URIRef) -> str:
    """Get rdfs:label for a resource, with optional language preference."""
    labels = list(g.objects(subject, RDFS.label))
    if not labels:
        return ""
    # Prefer literal with no lang or "en"
    for lit in labels:
        if hasattr(lit, "language") and lit.language in ("en", ""):
            return str(lit)
        if not hasattr(lit, "language"):
            return str(lit)
    return str(labels[0])


def _parse_into_graph(g: Graph, content: str, url: str, content_type: str) -> None:
    """Parse RDF content into graph; format inferred from content_type and url."""
    if "turtle" in content_type or "ttl" in content_type or ".ttl" in url or "turtle" in url:
        g.parse(data=content, format="turtle")
    elif "rdf+xml" in content_type or "xml" in content_type or ".owl" in url or ".rdf" in url:
        g.parse(data=content, format="xml")
    else:
        try:
            g.parse(data=content, format="turtle")
        except Exception:
            g.parse(data=content, format="xml")


def load_ontology_from_url(
    url: str,
    external_vocabulary_urls: Optional[List[str]] = None,
) -> Ontology:
    """
    Fetch ontology from URL (GET), parse as Turtle or RDF/OWL XML, and build Ontology domain model.

    Optionally merge external vocabularies (e.g. FOAF) into the same graph so that domain/range
    references (e.g. foaf:Organization) resolve to full class definitions. External URLs are
    the TTL/OWL artifact URLs (e.g. hasArtifact from DataSpecer spec: FOAF
    https://datagov-cz.github.io/cache-slovniku/foaf.ttl).

    Args:
        url: Full URL (e.g. https://tool.dataspecer.com/api/preview/en/model.owl.ttl?iri=...)
        external_vocabulary_urls: Optional list of URLs of external vocabularies to merge (e.g. FOAF TTL).

    Returns:
        Ontology: The loaded ontology (classes, attributes, relationships).

    Raises:
        requests.RequestException: On fetch failure.
        ValueError: On parse failure or empty ontology.
    """
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    content = response.text
    content_type = (response.headers.get("Content-Type") or "").lower()

    g = Graph()
    _parse_into_graph(g, content, url, content_type)

    # Determine main ontology URI before merging externals (so we keep main doc as primary)
    ontology_uri_ref = None
    for s in g.subjects(RDF.type, OWL.Ontology):
        ontology_uri_ref = s
        break
    if ontology_uri_ref is None:
        for prefix, ns in g.namespaces():
            if prefix == "" or str(ns).startswith("http"):
                ontology_uri_ref = URIRef(str(ns).rstrip("#/"))
                break
    if ontology_uri_ref is None:
        raise ValueError("Could not determine ontology URI from the document")

    # Merge external vocabularies (e.g. FOAF) so domain/range references resolve
    for ext_url in external_vocabulary_urls or []:
        ext_url = ext_url.strip()
        if not ext_url:
            continue
        try:
            ext_response = requests.get(ext_url, timeout=30)
            ext_response.raise_for_status()
            ext_content = ext_response.text
            ext_content_type = (ext_response.headers.get("Content-Type") or "").lower()
            _parse_into_graph(g, ext_content, ext_url, ext_content_type)
        except Exception:
            # Skip failed external vocab; main ontology still loads
            pass

    ontology_uri_ref = URIRef(str(ontology_uri_ref)) if not isinstance(ontology_uri_ref, URIRef) else ontology_uri_ref
    ontology_uri_str = str(ontology_uri_ref)
    if not ontology_uri_str.endswith("#") and not ontology_uri_str.endswith("/"):
        ontology_uri_str = ontology_uri_str + "#"

    # Collect classes (owl:Class or rdfs:Class)
    classes_by_uri: dict = {}
    for s in g.subjects(RDF.type, OWL.Class):
        if isinstance(s, URIRef):
            uri_str = str(s)
            if uri_str not in classes_by_uri:
                classes_by_uri[uri_str] = OntologyClass(
                    uri=URIRef(uri_str),
                    label=_get_label(g, s) or uri_str.split("#")[-1].split("/")[-1],
                    definition=None,
                    description=None,
                    kind=Kind.OBJECT,
                    definition_references=[],
                    specification_references=[],
                    references=[],
                )
    for s in g.subjects(RDF.type, RDFS.Class):
        if isinstance(s, URIRef):
            uri_str = str(s)
            if uri_str not in classes_by_uri:
                classes_by_uri[uri_str] = OntologyClass(
                    uri=URIRef(uri_str),
                    label=_get_label(g, s) or uri_str.split("#")[-1].split("/")[-1],
                    definition=None,
                    description=None,
                    kind=Kind.OBJECT,
                    definition_references=[],
                    specification_references=[],
                    references=[],
                )

    def ensure_class(uri_ref) -> OntologyClass:
        uri_str = str(uri_ref)
        if uri_str not in classes_by_uri:
            classes_by_uri[uri_str] = OntologyClass(
                uri=URIRef(uri_str),
                label=uri_str.split("#")[-1].split("/")[-1],
                definition=None,
                description=None,
                kind=Kind.OBJECT,
                definition_references=[],
                specification_references=[],
                references=[],
            )
        return classes_by_uri[uri_str]

    # rdfs:subClassOf -> generalizations
    for s, o in g.subject_objects(RDFS.subClassOf):
        if isinstance(s, URIRef) and isinstance(o, URIRef):
            sub_uri = str(s)
            super_uri = str(o)
            if sub_uri in classes_by_uri and super_uri in classes_by_uri:
                sub_c = classes_by_uri[sub_uri]
                super_c = classes_by_uri[super_uri]
                if super_c not in sub_c.generalizations:
                    sub_c.generalizations.append(super_c)
                if sub_c not in super_c.specializations:
                    super_c.specializations.append(sub_c)

    # Object properties -> OntologyRelationship (domain = source, range = target)
    relationships_by_uri: dict = {}
    for s in g.subjects(RDF.type, OWL.ObjectProperty):
        if not isinstance(s, URIRef):
            continue
        uri_str = str(s)
        domain_list = list(g.objects(s, RDFS.domain))
        range_list = list(g.objects(s, RDFS.range))
        source_class = ensure_class(domain_list[0]) if domain_list and isinstance(domain_list[0], URIRef) else None
        target_class = ensure_class(range_list[0]) if range_list and isinstance(range_list[0], URIRef) else None
        rel = OntologyRelationship(
            uri=URIRef(uri_str),
            label=_get_label(g, s) or uri_str.split("#")[-1].split("/")[-1],
            definition=None,
            description=None,
            sourceClass=source_class,
            targetClass=target_class,
            definition_references=[],
            specification_references=[],
            references=[],
        )
        relationships_by_uri[uri_str] = rel
        if source_class:
            source_class.outgoingRelationships.append(rel)
        if target_class:
            target_class.incomingRelationships.append(rel)

    # Datatype properties -> OntologyAttribute (domain = owning class)
    attributes_by_uri: dict = {}
    for s in g.subjects(RDF.type, OWL.DatatypeProperty):
        if not isinstance(s, URIRef):
            continue
        uri_str = str(s)
        domain_list = list(g.objects(s, RDFS.domain))
        owning_class = ensure_class(domain_list[0]) if domain_list and isinstance(domain_list[0], URIRef) else None
        attr = OntologyAttribute(
            uri=URIRef(uri_str),
            label=_get_label(g, s) or uri_str.split("#")[-1].split("/")[-1],
            definition=None,
            description=None,
            owningClass=owning_class,
            definition_references=[],
            specification_references=[],
            references=[],
        )
        attributes_by_uri[uri_str] = attr
        if owning_class:
            owning_class.attributes.append(attr)

    ontology = Ontology(
        uri=ontology_uri_ref,
        label=_get_label(g, ontology_uri_ref) if ontology_uri_ref else "",
        description=None,
        classes={URIRef(k): v for k, v in classes_by_uri.items()},
        attributes={URIRef(k): v for k, v in attributes_by_uri.items()},
        relationships={URIRef(k): v for k, v in relationships_by_uri.items()},
    )
    return ontology
