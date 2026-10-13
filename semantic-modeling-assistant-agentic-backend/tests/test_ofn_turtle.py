"""Tests for OFN JSON → Turtle serialization."""

from rdflib import Graph, URIRef
from rdflib.namespace import OWL, RDF, SKOS

from ontology.ofn_export import ontology_to_ofn
from ontology.ofn_turtle import ofn_document_to_turtle
from ontology.domain import Kind, Ontology, OntologyAttribute, OntologyClass, OntologyRelationship


def test_ofn_document_to_turtle_includes_labels_and_types():
    class_vehicle = OntologyClass(
        uri=URIRef("https://slovník.gov.cz/legislativní/sbírka/56/2001/pojem/silniční-vozidlo"),
        label="Silniční vozidlo",
        definition="Motorové alebo nemotorové vozidlo.",
        description=None,
        kind=Kind.OBJECT,
    )
    class_owner = OntologyClass(
        uri=URIRef("https://slovník.gov.cz/legislativní/sbírka/56/2001/pojem/vlastník-vozidla"),
        label="Vlastník vozidla",
        definition="Vlastník vozidla",
        description=None,
        kind=Kind.SUBJECT,
    )
    attr = OntologyAttribute(
        uri=URIRef("https://slovník.gov.cz/legislativní/sbírka/56/2001/pojem/registračná-značka"),
        label="registračná značka",
        definition="Evidenčné číslo.",
        description=None,
        owningClass=class_vehicle,
    )
    rel = OntologyRelationship(
        uri=URIRef("https://slovník.gov.cz/legislativní/sbírka/56/2001/pojem/je-vlastníkom"),
        label="je vlastníkom",
        definition="Vzťah vlastníka a vozidla.",
        description=None,
        sourceClass=class_owner,
        targetClass=class_vehicle,
    )
    ontology = Ontology(
        uri=URIRef("https://slovník.gov.cz/legislativní/sbírka/56/2001"),
        label="Slovník zákona č. 56/2001 Sb.",
        description="Testovací slovník",
        classes={class_vehicle.uri: class_vehicle, class_owner.uri: class_owner},
        attributes={attr.uri: attr},
        relationships={rel.uri: rel},
    )

    turtle = ofn_document_to_turtle(ontology_to_ofn(ontology))
    graph = Graph().parse(data=turtle, format="turtle")

    vocabulary = URIRef("https://slovník.gov.cz/legislativní/sbírka/56/2001")
    vehicle = URIRef("https://slovník.gov.cz/legislativní/sbírka/56/2001/pojem/silniční-vozidlo")
    assert (vocabulary, RDF.type, OWL.Ontology) in graph
    assert (vehicle, RDF.type, OWL.Class) in graph
    assert (vehicle, SKOS.inScheme, vocabulary) in graph
    assert "Silniční vozidlo" in turtle
    assert "je vlastníkom" in turtle
    assert "registračná značka" in turtle
