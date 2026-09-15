from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .constants import DEFAULT_XSD_RANGE, OFN_CONTEXT, VOCABULARY_TYPES
from .iri import local_name_from_uri, pojem_iri, resolve_class_iri, slugify_label
from .text import legal_reference_fields, multilingual_text


def build_vocabulary_root(
    vocabulary_iri: str,
    title_cs: str,
    description_cs: Optional[str] = None,
    title_en: Optional[str] = None,
    description_en: Optional[str] = None,
    created: Optional[str] = None,
    updated: Optional[str] = None,
) -> Dict[str, Any]:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")
    if now.endswith("+0000"):
        now = now[:-2] + ":00"

    root: Dict[str, Any] = {
        "@context": OFN_CONTEXT,
        "iri": vocabulary_iri,
        "typ": list(VOCABULARY_TYPES),
        "název": multilingual_text(title_cs, title_en) or {"cs": title_cs or vocabulary_iri},
    }
    popis = multilingual_text(description_cs, description_en)
    if popis:
        root["popis"] = popis
    root["vytvořeno"] = {
        "typ": "Časový okamžik",
        "datum": created or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }
    root["aktualizováno"] = {
        "typ": "Časový okamžik",
        "datum_a_čas": updated or now,
    }
    return root


def class_typ_tags(kind: Optional[str]) -> List[str]:
    tags = ["Koncept", "Pojem", "Třída"]
    if kind == "subject":
        tags.append("Typ subjektu práva")
    elif kind == "object":
        tags.append("Typ objektu práva")
    return tags


def build_pojmy_from_elements(
    vocabulary_iri: str,
    classes: List[Dict[str, Any]],
    attributes: List[Dict[str, Any]],
    relationships: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    labels_by_uri: Dict[str, str] = {}
    for cls in classes:
        uri = cls.get("uri") or ""
        labels_by_uri[uri] = cls.get("label") or local_name_from_uri(uri)

    pojmy: List[Dict[str, Any]] = []

    for cls in classes:
        uri = cls.get("uri")
        if not uri:
            continue
        label = cls.get("label") or local_name_from_uri(uri)
        iri = pojem_iri(vocabulary_iri, label, existing_uri=uri)
        pojem: Dict[str, Any] = {
            "iri": iri,
            "typ": class_typ_tags(cls.get("kind")),
            "název": multilingual_text(label) or {"cs": label},
        }
        definice = multilingual_text(cls.get("definition"))
        if definice:
            pojem["definice"] = definice
        popis = multilingual_text(cls.get("description"))
        if popis and popis != definice:
            pojem["popis"] = popis
        pojem.update(
            legal_reference_fields(
                cls.get("definition_references"),
                cls.get("specification_references"),
            )
        )
        generalizations = cls.get("generalizations") or []
        if generalizations:
            pojem["nadřazená-třída"] = [
                resolve_class_iri(ref, vocabulary_iri, labels_by_uri) for ref in generalizations
            ]
        pojmy.append(pojem)

    for rel in relationships:
        uri = rel.get("uri")
        if not uri:
            continue
        label = rel.get("label") or local_name_from_uri(uri)
        source = rel.get("sourceClass") or rel.get("domain")
        target = rel.get("targetClass") or rel.get("range")
        if not source or not target:
            continue
        pojem = {
            "iri": pojem_iri(vocabulary_iri, label, existing_uri=uri),
            "typ": ["Koncept", "Pojem", "Vztah"],
            "název": multilingual_text(label) or {"cs": label},
            "definiční-obor": resolve_class_iri(source, vocabulary_iri, labels_by_uri),
            "obor-hodnot": resolve_class_iri(target, vocabulary_iri, labels_by_uri),
        }
        definice = multilingual_text(rel.get("definition"))
        if definice:
            pojem["definice"] = definice
        popis = multilingual_text(rel.get("description"))
        if popis and popis != definice:
            pojem["popis"] = popis
        pojem.update(
            legal_reference_fields(
                rel.get("definition_references"),
                rel.get("specification_references"),
            )
        )
        pojmy.append(pojem)

    for attr in attributes:
        uri = attr.get("uri")
        if not uri:
            continue
        label = attr.get("label") or local_name_from_uri(uri)
        domain = attr.get("owningClass") or attr.get("domain")
        if not domain:
            continue
        range_value = attr.get("range") or DEFAULT_XSD_RANGE
        if range_value and not range_value.startswith("http") and ":" not in range_value:
            range_value = DEFAULT_XSD_RANGE
        if range_value and not range_value.startswith("xsd:") and range_value.startswith("http"):
            range_value = resolve_class_iri(range_value, vocabulary_iri, labels_by_uri)
        pojem = {
            "iri": pojem_iri(vocabulary_iri, label, existing_uri=uri),
            "typ": ["Koncept", "Pojem", "Vlastnost"],
            "název": multilingual_text(label) or {"cs": label},
            "definiční-obor": resolve_class_iri(domain, vocabulary_iri, labels_by_uri),
            "obor-hodnot": range_value or DEFAULT_XSD_RANGE,
        }
        definice = multilingual_text(attr.get("definition"))
        if definice:
            pojem["definice"] = definice
        popis = multilingual_text(attr.get("description"))
        if popis and popis != definice:
            pojem["popis"] = popis
        pojem.update(
            legal_reference_fields(
                attr.get("definition_references"),
                attr.get("specification_references"),
            )
        )
        pojmy.append(pojem)

    return pojmy


def finalize_document(root: Dict[str, Any], pojmy: List[Dict[str, Any]]) -> Dict[str, Any]:
    result = dict(root)
    if pojmy:
        result["pojmy"] = pojmy
    return result
