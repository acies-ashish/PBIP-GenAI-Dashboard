# semantic/linguistic_generator.py

from typing import Dict
from collections import defaultdict


def generate_linguistic_metadata(semantic_index: Dict) -> Dict:
    """
    Generates linguistic metadata strictly from the semantic index.
    - No inferred tables
    - No hallucinated entities
    """

    entities = {}

    # --------------------------------------------------
    # TABLE ENTITIES (ONLY REAL TMDL TABLES)
    # --------------------------------------------------
    for table_name in semantic_index["tables"].keys():
        entities[table_name] = {
            "kind": "table",
            "binding": {
                "table": table_name
            },
            "terms": [
                table_name.lower(),
                table_name.replace("_", " ").lower()
            ]
        }

    # --------------------------------------------------
    # COLUMN ENTITIES (BOUND TO TABLES)
    # --------------------------------------------------
    for table_name, table in semantic_index["tables"].items():
        for col in table.get("columns", []):
            entity_id = f"{table_name}.{_normalize_id(col)}"

            entities[entity_id] = {
                "kind": "column",
                "binding": {
                    "table": table_name,
                    "column": col
                },
                "terms": generate_column_terms(col)
            }

    return {
        "language": "en-US",
        "entities": entities
    }


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def generate_column_terms(column_name: str) -> list:
    """
    Deterministic term expansion (NO LLM).
    """
    base = column_name.lower()

    terms = {
        base,
        base.replace("_", " "),
    }

    # Manual enrichments (safe + generic)
    if "sales" in base and "person" in base:
        terms.update([
            "sales person",
            "sales rep",
            "sales executive",
            "sales exec"
        ])

    if base == "product":
        terms.update(["product", "item", "sku"])

    if base == "country":
        terms.update(["country", "region", "market"])

    if base == "date":
        terms.update(["date", "time", "day"])

    return sorted(terms)


def _normalize_id(text: str) -> str:
    return text.lower().replace(" ", "_")
