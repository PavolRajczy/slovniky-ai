#!/usr/bin/env python3
"""CLI for converting internal ontology formats to OFN Slovníky JSON."""

import argparse
import json
import sys
from pathlib import Path

from ofn_converter import ontology_dict_to_ofn, simplified_to_ofn, validate_ofn_document


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert ontology to OFN Slovníky JSON")
    parser.add_argument(
        "--from",
        dest="source_format",
        choices=["ontology", "simplified"],
        default="ontology",
        help="Input format (default: ontology)",
    )
    parser.add_argument("--input", required=True, help="Path to input JSON file")
    parser.add_argument("--output", help="Path to output JSON file (default: stdout)")
    parser.add_argument(
        "--base-iri",
        help="Vocabulary base IRI (required for simplified; optional override for ontology)",
    )
    parser.add_argument(
        "--title",
        help="Czech vocabulary title override",
    )
    parser.add_argument(
        "--description",
        help="Czech vocabulary description override",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate output against OFN kompletní JSON Schema",
    )
    parser.add_argument(
        "--schema",
        default="kompletni-schema.json",
        help="Schema file name in schemas/ (default: kompletni-schema.json)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 1

    with input_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if args.source_format == "ontology":
        vocabulary_iri = args.base_iri or data.get("uri")
        if not vocabulary_iri:
            print("Vocabulary IRI missing. Provide --base-iri or uri in input.", file=sys.stderr)
            return 1
        if args.title:
            data = dict(data)
            data["label"] = args.title
        if args.description:
            data = dict(data)
            data["description"] = args.description
        result = ontology_dict_to_ofn(data, vocabulary_iri=vocabulary_iri)
    else:
        vocabulary_iri = args.base_iri
        if not vocabulary_iri:
            print("--base-iri is required for simplified input.", file=sys.stderr)
            return 1
        result = simplified_to_ofn(
            data,
            vocabulary_iri=vocabulary_iri,
            title_cs=args.title,
            description_cs=args.description,
        )

    if args.validate:
        is_valid, errors = validate_ofn_document(result, schema_name=args.schema)
        if not is_valid:
            print("Validation failed:", file=sys.stderr)
            for message in errors:
                print(f"  - {message}", file=sys.stderr)
            return 2

    output_text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output_text + "\n", encoding="utf-8")
        print(f"Wrote {output_path}")
    else:
        print(output_text)

    if args.validate:
        print("Validation: OK", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
