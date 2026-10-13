"""
Serialize an OFN Slovníky JSON-LD document to Turtle.

Term mapping follows the official JSON-LD context:
https://ofn.gov.cz/slovníky/2026-02-26/kompletní/kontext.jsonld
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, Mapping, Optional

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, OWL, RDF, RDFS, SKOS, XSD

SLOVNIKY = Namespace("https://slovník.gov.cz/generický/datový-slovník-ofn-slovníků/pojem/")
VSGOV = Namespace("https://slovník.gov.cz/veřejný-sektor/pojem/")

TYPE_IRIS: Dict[str, URIRef] = {
    "Slovník": SLOVNIKY["slovník"],
    "Tezaurus": SKOS.ConceptScheme,
    "Tezaurus": SKOS.ConceptScheme,
    "Konceptuální model": OWL.Ontology,
    "Konceptuální model": OWL.Ontology,
    "Koncept": SKOS.Concept,
    "Pojem": SLOVNIKY["pojem"],
    "Třída": OWL.Class,
    "Vztah": OWL.ObjectProperty,
    "Vlastnost": OWL.DatatypeProperty,
    "Typ objektu práva": VSGOV["typ-objektu-práva"],
    "Typ subjektu práva": VSGOV["typ-subjektu-práva"],
}


def ofn_document_to_turtle(document: Mapping[str, Any]) -> str:
    """Convert an OFN JSON document (without `_meta`) to Turtle."""
    graph = Graph()
    graph.bind("skos", SKOS)
    graph.bind("dcterms", DCTERMS)
    graph.bind("owl", OWL)
    graph.bind("rdfs", RDFS)
    graph.bind("xsd", XSD)
    graph.bind("slovníky", SLOVNIKY)
    graph.bind("vsgov", VSGOV)

    vocabulary_iri = document.get("iri")
    if not vocabulary_iri:
        raise ValueError("OFN document is missing iri")
    vocabulary = URIRef(str(vocabulary_iri))

    _add_types(graph, vocabulary, document.get("typ"))
    _add_language_text(graph, vocabulary, SKOS.prefLabel, document.get("název"))
    _add_language_text(graph, vocabulary, DCTERMS.description, document.get("popis"))

    for pojem in document.get("pojmy") or []:
        pojem_iri = pojem.get("iri")
        if not pojem_iri:
            continue
        subject = URIRef(str(pojem_iri))
        graph.add((subject, SKOS.inScheme, vocabulary))
        _add_types(graph, subject, pojem.get("typ"))
        _add_language_text(graph, subject, SKOS.prefLabel, pojem.get("název"))
        _add_language_text(graph, subject, DCTERMS.description, pojem.get("popis"))
        _add_language_text(graph, subject, SKOS.definition, pojem.get("definice"))
        _add_uri(graph, subject, RDFS.domain, pojem.get("definiční-obor"))
        _add_uri(graph, subject, RDFS.range, pojem.get("obor-hodnot"))
        _add_uri_list(graph, subject, RDFS.subClassOf, pojem.get("nadřazená-třída"))
        _add_uri_list(graph, subject, RDFS.subPropertyOf, pojem.get("nadřazený-vztah"))
        _add_uri_list(graph, subject, RDFS.subPropertyOf, pojem.get("nadřazená-vlastnost"))
        _add_uri_list(
            graph,
            subject,
            SLOVNIKY["definující-ustanovení"],
            pojem.get("definující-ustanovení-právního-předpisu"),
        )
        _add_uri_list(
            graph,
            subject,
            SLOVNIKY["související-ustanovení"],
            pojem.get("související-ustanovení-právního-předpisu"),
        )

    return graph.serialize(format="turtle")


def _add_types(graph: Graph, subject: URIRef, types: Optional[Iterable[Any]]) -> None:
    for type_name in types or []:
        mapped = TYPE_IRIS.get(str(type_name))
        if mapped is not None:
            graph.add((subject, RDF.type, mapped))


def _add_language_text(
    graph: Graph,
    subject: URIRef,
    predicate: URIRef,
    value: Optional[Mapping[str, Any]],
) -> None:
    if not isinstance(value, Mapping):
        return
    for language, text in value.items():
        if text:
            graph.add((subject, predicate, Literal(str(text), lang=str(language))))


def _add_uri(graph: Graph, subject: URIRef, predicate: URIRef, value: Optional[Any]) -> None:
    resolved = _to_uri(value)
    if resolved is not None:
        graph.add((subject, predicate, resolved))


def _add_uri_list(
    graph: Graph,
    subject: URIRef,
    predicate: URIRef,
    values: Optional[Iterable[Any]],
) -> None:
    for value in values or []:
        _add_uri(graph, subject, predicate, value)


def _to_uri(value: Optional[Any]) -> Optional[URIRef]:
    if not value:
        return None
    text = str(value).strip()
    if text in {"xsd:string", "xsd:string"}:
        return XSD.string
    if text.startswith("xsd:"):
        return XSD[text.split(":", 1)[1]]
    if text.startswith("http://") or text.startswith("https://"):
        return URIRef(text)
    return None
