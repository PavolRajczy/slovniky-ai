# OFN Slovníky konvertor

Experimentálny konvertor z interného formátu ontológie (alebo DataSpecer Simplified Semantic Model) do **OFN Slovníky JSON** (verzia `2026-02-26`, Konceptuální model).

## Inštalácia

```bash
cd ofn-converter
pip install -r requirements.txt
```

## Použitie

### Z interného `ontology.json`

```bash
python convert.py \
  --from ontology \
  --input examples/input-ontology.json \
  --base-iri "https://slovník.gov.cz/legislativní/sbírka/56/2001" \
  --output examples/output-ofn.json \
  --validate
```

### Z DataSpecer Simplified Semantic Model

```bash
python convert.py \
  --from simplified \
  --input examples/input-simplified.json \
  --base-iri "https://slovník.gov.cz/legislativní/sbírka/56/2001" \
  --title "Slovník zákona č. 56/2001 Sb." \
  --validate
```

## Testy

```bash
pip install pytest
pytest tests/
```

## Schémy

JSON Schema sú cachované v [`schemas/`](schemas/) zo `https://ofn.gov.cz/slovníky/2026-02-26/`.

## Dokumentácia

- [`doc/ofn-slovniky-integrace-a-otazky.md`](../doc/ofn-slovniky-integrace-a-otazky.md) – mapovanie, otázky pre DIA, fázy integrácie
- [`schema.md`](../schema.md) – lokálna kópia OFN špecifikácie
