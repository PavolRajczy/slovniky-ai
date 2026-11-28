"""Legal document IRIs are queried on the current e-Sbírka host."""
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from knowledge_base.service import ESEL_SPARQL_ENDPOINT, canonical_legal_document_id


CANONICAL = "https://opendata.eselpoint.gov.cz/esel-esb/eli/cz/sb/2012/89/2026-01-01"


def test_sparql_endpoint_is_the_gov_host():
    assert ESEL_SPARQL_ENDPOINT == "https://opendata.eselpoint.gov.cz/sparql"


def test_gov_host_is_unchanged():
    assert canonical_legal_document_id(CANONICAL) == CANONICAL


def test_legacy_host_is_rewritten_to_the_gov_iri():
    given = "https://opendata.eselpoint.cz/esel-esb/eli/cz/sb/2012/89/2026-01-01"
    assert canonical_legal_document_id(given) == CANONICAL


def test_other_hosts_are_rejected():
    with pytest.raises(ValueError, match="Invalid legal knowledge document ID"):
        canonical_legal_document_id("https://example.com/esel-esb/eli/cz/sb/2012/89/2026-01-01")
