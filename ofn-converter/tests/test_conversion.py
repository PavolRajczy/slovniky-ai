import json
from pathlib import Path

import pytest

from ofn_converter import ontology_dict_to_ofn, simplified_to_ofn, validate_ofn_document
from ofn_converter.constants import OFN_CONTEXT
from ofn_converter.iri import pojem_iri, slugify_label


EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"
VOCABULARY_IRI = "https://slovník.gov.cz/legislativní/sbírka/56/2001"


@pytest.fixture
def ontology_data() -> dict:
    with (EXAMPLES_DIR / "input-ontology.json").open("r", encoding="utf-8") as handle:
        return json.load(handle)


@pytest.fixture
def simplified_data() -> dict:
    with (EXAMPLES_DIR / "input-simplified.json").open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_slugify_label_preserves_czech_characters():
    assert slugify_label("Silniční vozidlo") == "silniční-vozidlo"


def test_pojem_iri_uses_existing_uri():
    existing = "https://slovník.gov.cz/legislativní/sbírka/56/2001/pojem/silniční-vozidlo"
    assert pojem_iri(VOCABULARY_IRI, "ignored", existing_uri=existing) == existing


def test_ontology_to_ofn_structure(ontology_data):
    result = ontology_dict_to_ofn(ontology_data, vocabulary_iri=VOCABULARY_IRI)

    assert result["@context"] == OFN_CONTEXT
    assert result["iri"] == VOCABULARY_IRI
    assert "Slovník" in result["typ"]
    assert "Konceptuální model" in result["typ"]
    assert result["název"]["cs"] == "Slovník zákona č. 56/2001 Sb."
    assert len(result["pojmy"]) == 4

    classes = [p for p in result["pojmy"] if "Třída" in p["typ"]]
    relationships = [p for p in result["pojmy"] if "Vztah" in p["typ"]]
    properties = [p for p in result["pojmy"] if "Vlastnost" in p["typ"]]

    assert len(classes) == 2
    assert len(relationships) == 1
    assert len(properties) == 1

    vehicle = next(p for p in classes if p["název"]["cs"] == "Silniční vozidlo")
    assert "Typ objektu práva" in vehicle["typ"]
    assert "nadřazená-třída" in vehicle
    assert "definující-ustanovení-právního-předpisu" in vehicle

    owner = next(p for p in classes if p["název"]["cs"] == "Vlastník vozidla")
    assert "Typ subjektu práva" in owner["typ"]

    relation = relationships[0]
    assert relation["definiční-obor"].endswith("/vlastník-vozidla")
    assert relation["obor-hodnot"].endswith("/silniční-vozidlo")

    prop = properties[0]
    assert prop["definiční-obor"].endswith("/silniční-vozidlo")
    assert prop["obor-hodnot"] == "xsd:string"


def test_simplified_to_ofn_structure(simplified_data):
    result = simplified_to_ofn(
        simplified_data,
        vocabulary_iri=VOCABULARY_IRI,
        title_cs="Slovník zákona č. 56/2001 Sb.",
    )

    assert result["iri"] == VOCABULARY_IRI
    assert len(result["pojmy"]) == 4
    labels = {p["název"]["cs"] for p in result["pojmy"]}
    assert "Silniční vozidlo" in labels
    assert "je vlastníkem" in labels


def test_ontology_output_validates_against_schema(ontology_data):
    result = ontology_dict_to_ofn(ontology_data, vocabulary_iri=VOCABULARY_IRI)
    is_valid, errors = validate_ofn_document(result)
    assert is_valid, errors


def test_simplified_output_validates_against_schema(simplified_data):
    result = simplified_to_ofn(
        simplified_data,
        vocabulary_iri=VOCABULARY_IRI,
        title_cs="Slovník zákona č. 56/2001 Sb.",
    )
    is_valid, errors = validate_ofn_document(result)
    assert is_valid, errors
