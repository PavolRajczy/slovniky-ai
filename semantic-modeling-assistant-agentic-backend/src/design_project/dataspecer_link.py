"""
Fetch a Dataspecer vocabulary and turn its semantic model into an ontology.

The Dataspecer origin comes from DATASPECER_BACKEND so a local host can later
be replaced with the real API without changing call sites.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlencode

import requests
from dotenv import load_dotenv

from ontology.dataspecer_simplified import ontology_to_simplified, simplified_to_ontology
from ontology.domain import Ontology

SEMANTIC_MODEL_TYPE = "http://dataspecer.com/resources/local/semantic-model"
DEFAULT_DATASPECER_BACKEND = "http://localhost:3100"


class DataspecerLinkError(Exception):
    """Dataspecer could not supply a vocabulary for a new project."""

    def __init__(self, message: str, status_code: int = 502) -> None:
        super().__init__(message)
        self.status_code = status_code


def export_url_for_package(package_iri: str) -> str:
    """PUT URL of the vocabulary's semantic model on the configured Dataspecer origin."""
    package = _get_json("/resources/packages", {"iri": package_iri})
    semantic_model = _semantic_model_child(package)
    if semantic_model is None or not semantic_model.get("iri"):
        raise DataspecerLinkError(
            f"Dataspecer package '{package_iri}' has no semantic model to export into.",
            status_code=422,
        )
    query = urlencode({"iri": semantic_model["iri"]})
    return f"{dataspecer_backend_url()}/simplified-semantic-model?{query}"


def push_vocabulary(package_iri: str, ontology: Ontology) -> None:
    """Replace the vocabulary's semantic model in Dataspecer with the given ontology."""
    url = export_url_for_package(package_iri)
    try:
        response = requests.put(url, json=ontology_to_simplified(ontology), timeout=30)
        response.raise_for_status()
    except requests.RequestException as error:
        raise DataspecerLinkError(f"Failed to update Dataspecer at {url}: {error}") from error


def dataspecer_backend_url() -> str:
    """Origin of the Dataspecer API, without a trailing slash."""
    load_dotenv()
    configured = os.environ.get("DATASPECER_BACKEND", DEFAULT_DATASPECER_BACKEND)
    return configured.rstrip("/")


def import_vocabulary(package_iri: str) -> Tuple[str, Ontology]:
    """
    Load the vocabulary package and import its semantic model.

    Returns the vocabulary label and the ontology built from the simplified model.
    """
    package = _get_json("/resources/packages", {"iri": package_iri})
    name = _language_label((package.get("userMetadata") or {}).get("label")) or package_iri
    semantic_model = _semantic_model_child(package)
    if semantic_model is None:
        raise DataspecerLinkError(
            f"Dataspecer package '{package_iri}' has no semantic model.",
            status_code=422,
        )

    model_iri = semantic_model.get("iri")
    if not model_iri:
        raise DataspecerLinkError(
            f"Dataspecer package '{package_iri}' has a semantic model without an IRI.",
            status_code=422,
        )

    blob = _get_json("/resources/blob", {"iri": model_iri})
    base_iri = blob.get("baseIri") or blob.get("base_iri")
    if not isinstance(base_iri, str) or not base_iri.strip():
        raise DataspecerLinkError(
            f"Semantic model '{model_iri}' has no base IRI.",
            status_code=422,
        )

    simplified = _get_json("/simplified-semantic-model", {"iri": model_iri})
    ontology = simplified_to_ontology(simplified, base_iri.strip())
    if not ontology.label:
        ontology.label = name
    return name, ontology


def _semantic_model_child(package: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    for child in package.get("subResources") or []:
        types = child.get("types") or []
        if SEMANTIC_MODEL_TYPE in types:
            return child
    return None


def _language_label(label: Any) -> Optional[str]:
    if isinstance(label, str) and label.strip():
        return label.strip()
    if isinstance(label, dict):
        for key in ("en", "cs", "sk"):
            value = label.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        for value in label.values():
            if isinstance(value, str) and value.strip():
                return value.strip()
    return None


def _get_json(path: str, query: Dict[str, str]) -> Dict[str, Any]:
    url = f"{dataspecer_backend_url()}{path}?{urlencode(query)}"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as error:
        raise DataspecerLinkError(f"Failed to reach Dataspecer at {url}: {error}") from error
    except ValueError as error:
        raise DataspecerLinkError(f"Dataspecer returned invalid JSON from {url}.") from error
    if not isinstance(data, dict):
        raise DataspecerLinkError(f"Dataspecer returned an unexpected payload from {url}.")
    return data
