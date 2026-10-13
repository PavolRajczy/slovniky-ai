import re
from typing import Optional


def normalize_base_uri(uri: str) -> str:
    if not uri:
        return uri
    value = uri.strip().rstrip("/")
    return value


def local_name_from_uri(uri: str) -> str:
    if not uri:
        return ""
    if "#" in uri:
        return uri.split("#")[-1]
    return uri.rstrip("/").split("/")[-1]


def slugify_label(label: str) -> str:
    if not label:
        return "pojem"
    value = label.strip().lower()
    value = re.sub(r"\s+", "-", value)
    value = re.sub(r"[^a-z0-9áčďéěíňóřšťúůýž\-]", "", value, flags=re.IGNORECASE)
    return value or "pojem"


def pojem_iri(vocabulary_iri: str, label_or_slug: str, existing_uri: Optional[str] = None) -> str:
    if existing_uri and existing_uri.startswith("http"):
        return existing_uri
    base = normalize_base_uri(vocabulary_iri)
    slug = slugify_label(label_or_slug) if not existing_uri else existing_uri.strip("/")
    return f"{base}/pojem/{slug}"


def resolve_class_iri(
    ref: str,
    vocabulary_iri: str,
    labels_by_uri: dict[str, str],
) -> str:
    if not ref:
        return ref
    if ref.startswith("http://") or ref.startswith("https://"):
        return ref
    base = normalize_base_uri(vocabulary_iri)
    if ref.startswith("/"):
        return f"{base}{ref}"
    if "/" in ref or "#" in ref:
        return ref
    label = labels_by_uri.get(ref, ref)
    return pojem_iri(vocabulary_iri, label, existing_uri=ref)
