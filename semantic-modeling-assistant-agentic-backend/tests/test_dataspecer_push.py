"""
Tests for sending the designed ontology to the project's linked Dataspecer vocabulary.
"""
from unittest.mock import Mock, patch

import pytest
import requests
from rdflib import URIRef

from design_project.dataspecer_link import SEMANTIC_MODEL_TYPE, DataspecerLinkError
from ontology.domain import Ontology, OntologyClass

from fakes import create_fake_design_project_service

DATASPECER_BACKEND = "http://dataspecer.test"
PACKAGE_IRI = "urn:package:vehicles"
SEMANTIC_MODEL_IRI = "urn:model:vehicles"
ONTOLOGY_URI = "http://example.org/vehicles#"


@pytest.fixture(autouse=True)
def dataspecer_backend(monkeypatch):
    monkeypatch.setenv("DATASPECER_BACKEND", DATASPECER_BACKEND)


def create_project(service, dataspecer_package_iri=None):
    vehicle = OntologyClass(uri=URIRef(f"{ONTOLOGY_URI}Vehicle"), label="Vehicle", definition="A road vehicle.", description=None)
    service.ontology_service.store_ontology(
        Ontology(uri=URIRef(ONTOLOGY_URI), label="Vehicles", description=None, classes={vehicle.uri: vehicle})
    )
    return service.initialize_new_project(
        project_name="Vehicles",
        working_ontology_uri=ONTOLOGY_URI,
        dataspecer_package_iri=dataspecer_package_iri,
    )


def package_response() -> Mock:
    response = Mock()
    response.json.return_value = {
        "iri": PACKAGE_IRI,
        "subResources": [{"iri": SEMANTIC_MODEL_IRI, "types": [SEMANTIC_MODEL_TYPE]}],
    }
    return response


def test_push_sends_the_designed_ontology_to_the_linked_semantic_model(tmp_path):
    service = create_fake_design_project_service(str(tmp_path))
    project = create_project(service, PACKAGE_IRI)

    with patch("design_project.dataspecer_link.requests.get", return_value=package_response()), \
            patch("design_project.dataspecer_link.requests.put", return_value=Mock()) as put:
        pushed = service.push_ontology_to_dataspecer(project.id)

    assert pushed is True
    put.assert_called_once()
    url = put.call_args.args[0]
    assert url == f"{DATASPECER_BACKEND}/simplified-semantic-model?iri=urn%3Amodel%3Avehicles"
    payload = put.call_args.kwargs["json"]
    assert [cls["title"] for cls in payload["classes"]] == ["Vehicle"]


def test_push_raises_when_dataspecer_rejects_the_update(tmp_path):
    service = create_fake_design_project_service(str(tmp_path))
    project = create_project(service, PACKAGE_IRI)
    rejected = Mock()
    rejected.raise_for_status.side_effect = requests.HTTPError("500 Server Error")

    with patch("design_project.dataspecer_link.requests.get", return_value=package_response()), \
            patch("design_project.dataspecer_link.requests.put", return_value=rejected):
        with pytest.raises(DataspecerLinkError, match="Failed to update Dataspecer"):
            service.push_ontology_to_dataspecer(project.id)


def test_push_raises_when_dataspecer_is_unreachable(tmp_path):
    service = create_fake_design_project_service(str(tmp_path))
    project = create_project(service, PACKAGE_IRI)

    with patch("design_project.dataspecer_link.requests.get", side_effect=requests.ConnectionError("refused")):
        with pytest.raises(DataspecerLinkError, match="Failed to reach Dataspecer"):
            service.push_ontology_to_dataspecer(project.id)


def test_push_is_skipped_for_a_project_without_dataspecer_link(tmp_path):
    service = create_fake_design_project_service(str(tmp_path))
    project = create_project(service)

    with patch("design_project.dataspecer_link.requests.get") as get, \
            patch("design_project.dataspecer_link.requests.put") as put:
        pushed = service.push_ontology_to_dataspecer(project.id)

    assert pushed is False
    get.assert_not_called()
    put.assert_not_called()
