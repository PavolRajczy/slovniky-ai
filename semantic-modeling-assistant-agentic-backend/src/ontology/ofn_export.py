"""
Convert Ontology domain model to OFN Slovníky JSON (2026-02-26, Konceptuální model).

Logic mirrors the standalone `ofn-converter` package.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from ontology.domain import Kind, Ontology

OFN_VERSION = "2026-02-26"
OFN_CONTEXT = f"https://ofn.gov.cz/slovníky/{OFN_VERSION}/kompletní/kontext.jsonld"
VOCABULARY_TYPES = ["Slovník", "Tezaurus", "Konceptuální model"]
DEFAULT_XSD_RANGE = "xsd:string"
ELI_PREFIX = "https://opendata.eselpoint.cz/"


def ontology_to_ofn(
    ontology: Ontology,
    vocabulary_iri: Optional[str] = None,
) -> Dict[str, Any]:
    """Export Ontology to OFN Slovníky JSON-LD document."""
    if ontology is None:
        raise ValueError("ontology cannot be None")

    vocab_iri = vocabulary_iri or str(ontology.uri)
    if not vocab_iri:
        raise ValueError("vocabulary IRI is required")

    labels_by_uri: Dict[str, str] = {}
    for cls in ontology.classes.values():
        uri = str(cls.uri)
        labels_by_uri[uri] = cls.label or _local_name_from_uri(uri)

    root = _build_vocabulary_root(
        vocabulary_iri=vocab_iri,
        title_cs=ontology.label or vocab_iri,
        description_cs=ontology.description,
    )
    pojmy = _build_pojmy(ontology, vocab_iri, labels_by_uri)
    if pojmy:
        root["pojmy"] = pojmy
    return root


def _build_vocabulary_root(
    vocabulary_iri: str,
    title_cs: str,
    description_cs: Optional[str] = None,
) -> Dict[str, Any]:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")
    if now.endswith("+0000"):
        now = now[:-2] + ":00"

    root: Dict[str, Any] = {
        "@context": OFN_CONTEXT,
        "iri": vocabulary_iri,
        "typ": list(VOCABULARY_TYPES),
        "název": _multilingual_text(title_cs) or {"cs": title_cs or vocabulary_iri},
    }
    popis = _multilingual_text(description_cs)
    if popis:
        root["popis"] = popis
    root["vytvořeno"] = {
        "typ": "Časový okamžik",
        "datum": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }
    root["aktualizováno"] = {
        "typ": "Časový okamžik",
        "datum_a_čas": now,
    }
    return root


def _build_pojmy(
    ontology: Ontology,
    vocabulary_iri: str,
    labels_by_uri: Dict[str, str],
) -> List[Dict[str, Any]]:
    pojmy: List[Dict[str, Any]] = []

    for cls in ontology.classes.values():
        uri = str(cls.uri)
        label = cls.label or _local_name_from_uri(uri)
        pojem: Dict[str, Any] = {
            "iri": _pojem_iri(vocabulary_iri, label, existing_uri=uri),
            "typ": _class_typ_tags(cls.kind),
            "název": _multilingual_text(label) or {"cs": label},
        }
        definice = _multilingual_text(cls.definition)
        if definice:
            pojem["definice"] = definice
        popis = _multilingual_text(cls.description)
        if popis and popis != definice:
            pojem["popis"] = popis
        pojem.update(
            _legal_reference_fields(cls.definition_references, cls.specification_references)
        )
        if cls.generalizations:
            pojem["nadřazená-třída"] = [
                _resolve_class_iri(str(g.uri), vocabulary_iri, labels_by_uri)
                for g in cls.generalizations
            ]
        pojmy.append(pojem)

    for rel in ontology.relationships.values():
        uri = str(rel.uri)
        label = rel.label or _local_name_from_uri(uri)
        source = str(rel.sourceClass.uri) if rel.sourceClass and rel.sourceClass.uri else None
        target = str(rel.targetClass.uri) if rel.targetClass and rel.targetClass.uri else None
        if not source or not target:
            continue
        pojem = {
            "iri": _pojem_iri(vocabulary_iri, label, existing_uri=uri),
            "typ": ["Koncept", "Pojem", "Vztah"],
            "název": _multilingual_text(label) or {"cs": label},
            "definiční-obor": _resolve_class_iri(source, vocabulary_iri, labels_by_uri),
            "obor-hodnot": _resolve_class_iri(target, vocabulary_iri, labels_by_uri),
        }
        definice = _multilingual_text(rel.definition)
        if definice:
            pojem["definice"] = definice
        popis = _multilingual_text(rel.description)
        if popis and popis != definice:
            pojem["popis"] = popis
        pojem.update(
            _legal_reference_fields(rel.definition_references, rel.specification_references)
        )
        pojmy.append(pojem)

    for attr in ontology.attributes.values():
        uri = str(attr.uri)
        label = attr.label or _local_name_from_uri(uri)
        domain = str(attr.owningClass.uri) if attr.owningClass and attr.owningClass.uri else None
        if not domain:
            continue
        pojem = {
            "iri": _pojem_iri(vocabulary_iri, label, existing_uri=uri),
            "typ": ["Koncept", "Pojem", "Vlastnost"],
            "název": _multilingual_text(label) or {"cs": label},
            "definiční-obor": _resolve_class_iri(domain, vocabulary_iri, labels_by_uri),
            "obor-hodnot": DEFAULT_XSD_RANGE,
        }
        definice = _multilingual_text(attr.definition)
        if definice:
            pojem["definice"] = definice
        popis = _multilingual_text(attr.description)
        if popis and popis != definice:
            pojem["popis"] = popis
        pojem.update(
            _legal_reference_fields(attr.definition_references, attr.specification_references)
        )
        pojmy.append(pojem)

    return pojmy


def _class_typ_tags(kind: Optional[Kind]) -> List[str]:
    tags = ["Koncept", "Pojem", "Třída"]
    if kind == Kind.SUBJECT:
        tags.append("Typ subjektu práva")
    elif kind == Kind.OBJECT:
        tags.append("Typ objektu práva")
    return tags


def _multilingual_text(
    cs_value: Optional[str],
    en_value: Optional[str] = None,
) -> Optional[Dict[str, str]]:
    cs = (cs_value or "").strip()
    en = (en_value or "").strip()
    if not cs and not en:
        return None
    result: Dict[str, str] = {}
    if cs:
        result["cs"] = cs
    if en:
        result["en"] = en
    if not result.get("cs") and result.get("en"):
        result["cs"] = result["en"]
    return result


def _legal_reference_fields(
    definition_references: Optional[List[str]],
    specification_references: Optional[List[str]],
) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    defining = [ref for ref in (definition_references or []) if ref.startswith(ELI_PREFIX)]
    related = [ref for ref in (specification_references or []) if ref.startswith(ELI_PREFIX)]
    if defining:
        result["definující-ustanovení-právního-předpisu"] = defining
    if related:
        result["související-ustanovení-právního-předpisu"] = related
    return result


def _normalize_base_uri(uri: str) -> str:
    return uri.strip().rstrip("/") if uri else uri


def _local_name_from_uri(uri: str) -> str:
    if not uri:
        return ""
    if "#" in uri:
        return uri.split("#")[-1]
    return uri.rstrip("/").split("/")[-1]


def _slugify_label(label: str) -> str:
    if not label:
        return "pojem"
    value = label.strip().lower()
    value = re.sub(r"\s+", "-", value)
    value = re.sub(r"[^a-z0-9áčďéěíňóřšťúůýž\-]", "", value, flags=re.IGNORECASE)
    return value or "pojem"


def _pojem_iri(vocabulary_iri: str, label_or_slug: str, existing_uri: Optional[str] = None) -> str:
    if existing_uri and existing_uri.startswith("http"):
        return existing_uri
    base = _normalize_base_uri(vocabulary_iri)
    slug = _slugify_label(label_or_slug) if not existing_uri else existing_uri.strip("/")
    return f"{base}/pojem/{slug}"


def _resolve_class_iri(
    ref: str,
    vocabulary_iri: str,
    labels_by_uri: Dict[str, str],
) -> str:
    if not ref:
        return ref
    if ref.startswith("http://") or ref.startswith("https://"):
        return ref
    base = _normalize_base_uri(vocabulary_iri)
    if ref.startswith("/"):
        return f"{base}{ref}"
    if "/" in ref or "#" in ref:
        return ref
    label = labels_by_uri.get(ref, ref)
    return _pojem_iri(vocabulary_iri, label, existing_uri=ref)
