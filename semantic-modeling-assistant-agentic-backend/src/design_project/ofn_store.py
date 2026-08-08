"""
Persist OFN Slovníky JSON per design project.

Stored as `data/projects/{project_id}/ofn.json` and overwritten on each regenerate.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from ontology.domain import Ontology
from ontology.ofn_export import ontology_to_ofn

OFN_FILENAME = "ofn.json"


def project_ofn_path(project_id: str, base_dir: str = "data/projects") -> str:
    return os.path.join(base_dir, project_id, OFN_FILENAME)


def save_project_ofn(
    project_id: str,
    document: Dict[str, Any],
    base_dir: str = "data/projects",
) -> str:
    """
    Write OFN JSON for the project, overwriting any previous file.

    Returns a project-relative path suitable for UI feedback (e.g. `ofn.json`).
    """
    project_dir = os.path.join(base_dir, project_id)
    os.makedirs(project_dir, exist_ok=True)
    absolute_path = os.path.join(project_dir, OFN_FILENAME)
    payload = dict(document)
    payload["_meta"] = {
        "project_id": project_id,
        "saved_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "overwrote_existing": os.path.exists(absolute_path),
    }
    with open(absolute_path, "w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
    return OFN_FILENAME


def load_project_ofn(
    project_id: str,
    base_dir: str = "data/projects",
) -> Optional[Dict[str, Any]]:
    absolute_path = project_ofn_path(project_id, base_dir=base_dir)
    if not os.path.exists(absolute_path):
        return None
    with open(absolute_path, "r", encoding="utf-8") as file:
        return json.load(file)


def regenerate_and_save_project_ofn(
    project_id: str,
    ontology: Ontology,
    base_dir: str = "data/projects",
    vocabulary_iri: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Convert ontology to OFN and overwrite `ofn.json` for the project.

    Returns:
        {
          "path": "ofn.json",
          "absolute_path": "...",
          "pojmy_count": int,
          "overwrote_existing": bool,
          "document": { ... OFN without _meta for API consumers ... }
        }
    """
    absolute_path = project_ofn_path(project_id, base_dir=base_dir)
    overwrote = os.path.exists(absolute_path)
    document = ontology_to_ofn(ontology, vocabulary_iri=vocabulary_iri)
    relative_path = save_project_ofn(project_id, document, base_dir=base_dir)
    return {
        "path": relative_path,
        "absolute_path": os.path.abspath(absolute_path),
        "pojmy_count": len(document.get("pojmy") or []),
        "overwrote_existing": overwrote,
        "document": document,
    }
