"""Tests for per-project OFN persistence."""

import json
from pathlib import Path

from rdflib import URIRef

from design_project.ofn_store import (
    load_project_ofn,
    regenerate_and_save_project_ofn,
)
from ontology.domain import Kind, Ontology, OntologyClass


def test_regenerate_overwrites_project_ofn(tmp_path: Path):
    project_id = "proj-ofn-1"
    ontology = Ontology(
        uri=URIRef("https://example.org/vocab"),
        label="Test vocab",
        description="desc",
        classes={
            URIRef("https://example.org/vocab/pojem/a"): OntologyClass(
                uri=URIRef("https://example.org/vocab/pojem/a"),
                label="A",
                definition="def",
                description=None,
                kind=Kind.OBJECT,
            )
        },
    )

    first = regenerate_and_save_project_ofn(
        project_id,
        ontology,
        base_dir=str(tmp_path),
    )
    assert first["overwrote_existing"] is False
    assert (tmp_path / project_id / "ofn.json").exists()

    loaded = load_project_ofn(project_id, base_dir=str(tmp_path))
    assert loaded is not None
    assert loaded["název"]["cs"] == "Test vocab"
    assert loaded["_meta"]["project_id"] == project_id

    ontology.label = "Updated vocab"
    second = regenerate_and_save_project_ofn(
        project_id,
        ontology,
        base_dir=str(tmp_path),
    )
    assert second["overwrote_existing"] is True
    reloaded = json.loads((tmp_path / project_id / "ofn.json").read_text(encoding="utf-8"))
    assert reloaded["název"]["cs"] == "Updated vocab"
