"""Unit tests for OFN Slovníky export."""

from rdflib import URIRef

from ontology.domain import Kind, Ontology, OntologyAttribute, OntologyClass, OntologyRelationship
from ontology.ofn_export import ontology_to_ofn


def test_ontology_to_ofn_builds_conceptual_model():
    class_vehicle = OntologyClass(
        uri=URIRef("https://slovník.gov.cz/legislativní/sbírka/56/2001/pojem/silniční-vozidlo"),
        label="Silniční vozidlo",
        definition="Motorové nebo nemotorové vozidlo.",
        description=None,
        kind=Kind.OBJECT,
        definition_references=[
            "https://opendata.eselpoint.cz/esel-esb/eli/cz/sb/2001/56/2026-01-01/dokument/norma/cast_1/par_2/odst_1"
        ],
    )
    class_owner = OntologyClass(
        uri=URIRef("https://slovník.gov.cz/legislativní/sbírka/56/2001/pojem/vlastník-vozidla"),
        label="Vlastník vozidla",
        definition="Vlastník vozidla",
        description=None,
        kind=Kind.SUBJECT,
    )
    attr = OntologyAttribute(
        uri=URIRef("https://slovník.gov.cz/legislativní/sbírka/56/2001/pojem/registrační-značka"),
        label="registrační značka",
        definition="Evidenční číslo.",
        description=None,
        owningClass=class_vehicle,
    )
    rel = OntologyRelationship(
        uri=URIRef("https://slovník.gov.cz/legislativní/sbírka/56/2001/pojem/je-vlastníkem"),
        label="je vlastníkem",
        definition="Vztah vlastníka a vozidla.",
        description=None,
        sourceClass=class_owner,
        targetClass=class_vehicle,
    )

    ontology = Ontology(
        uri=URIRef("https://slovník.gov.cz/legislativní/sbírka/56/2001"),
        label="Slovník zákona č. 56/2001 Sb.",
        description="Testovací slovník",
        classes={
            class_vehicle.uri: class_vehicle,
            class_owner.uri: class_owner,
        },
        attributes={attr.uri: attr},
        relationships={rel.uri: rel},
    )

    document = ontology_to_ofn(ontology)

    assert document["typ"] == ["Slovník", "Tezaurus", "Konceptuální model"]
    assert document["název"]["cs"] == "Slovník zákona č. 56/2001 Sb."
    assert len(document["pojmy"]) == 4

    by_label = {p["název"]["cs"]: p for p in document["pojmy"]}
    assert "Typ objektu práva" in by_label["Silniční vozidlo"]["typ"]
    assert "Typ subjektu práva" in by_label["Vlastník vozidla"]["typ"]
    assert by_label["je vlastníkem"]["definiční-obor"].endswith("vlastník-vozidla")
    assert by_label["registrační značka"]["obor-hodnot"] == "xsd:string"
    assert by_label["Silniční vozidlo"]["definující-ustanovení-právního-předpisu"]
