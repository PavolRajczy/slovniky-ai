import json
from pathlib import Path
from typing import Any, List, Tuple

import jsonschema
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError


SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas"


def _load_schema(name: str) -> dict[str, Any]:
    path = SCHEMAS_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Schema not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_ofn_document(
    document: dict[str, Any],
    schema_name: str = "kompletni-schema.json",
) -> Tuple[bool, List[str]]:
    """
    Validate OFN document against a cached JSON Schema.
    Returns (is_valid, error_messages).
    """
    schema = _load_schema(schema_name)
    validator = Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    errors: List[str] = []
    for error in sorted(validator.iter_errors(document), key=lambda item: list(item.path)):
        path = ".".join(str(part) for part in error.path) or "(root)"
        errors.append(f"{path}: {error.message}")
    return len(errors) == 0, errors
