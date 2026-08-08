from typing import Any, Dict, Optional


def multilingual_text(
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


def legal_reference_fields(
    definition_references: list[str] | None,
    specification_references: list[str] | None,
) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    defining = [ref for ref in (definition_references or []) if _is_eli_iri(ref)]
    related = [ref for ref in (specification_references or []) if _is_eli_iri(ref)]
    if defining:
        result["definující-ustanovení-právního-předpisu"] = defining
    if related:
        result["související-ustanovení-právního-předpisu"] = related
    return result


def _is_eli_iri(value: str) -> bool:
    return bool(value) and value.startswith("https://opendata.eselpoint.cz/")
