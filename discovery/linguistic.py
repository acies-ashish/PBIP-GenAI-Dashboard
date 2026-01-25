# discovery/linguistic.py

def generate_linguistic_metadata(semantic_index: dict) -> dict:
    """
    Step 2: Creates the machine-facing ontology for concept resolution.
    """

    entities = {}

    for table_name, table_info in semantic_index["tables"].items():
        # -------------------------------
        # Table entity
        # -------------------------------
        entities[table_name] = {
            "kind": "table",
            "binding": {"table": table_name},
            "terms": [
                table_name.lower(),
                table_name.replace("_", " ").lower()
            ]
        }

        # -------------------------------
        # Column / Measure entities
        # -------------------------------
        for col_name, col_meta in table_info["columns"].items():
            is_measure = col_name in table_info.get("measures", {})

            entity_id = f"{table_name}.{col_name.lower().replace(' ', '_')}"

            entities[entity_id] = {
                "kind": "measure" if is_measure else "column",
                "binding": {
                    "table": table_name,
                    "column": col_name,
                    "measure": is_measure,
                    "dataType": col_meta.get("dataType")
                },
                "terms": _expand_terms(col_name, is_measure)
            }

    # ---------------- DEBUG: LINGUISTIC METADATA ----------------
    print("\n[LINGUISTIC DEBUG] Entities")
    for entity_id, entity in entities.items():
        binding = entity["binding"]
        print(
            f"  {entity_id} | "
            f"measure={binding.get('measure')} | "
            f"dataType={binding.get('dataType')} | "
            f"terms={entity['terms']}"
        )
    print("[LINGUISTIC DEBUG END]\n")
    # -----------------------------------------------------------

    return {
        "language": "en-US",
        "entities": entities
    }


def _expand_terms(name: str, is_measure: bool) -> list:
    """
    Generates controlled synonyms.
    Prevents numeric concepts from leaking to dimensions.
    """

    clean = name.lower()
    variants = {
        clean,
        clean.replace("_", " "),
        clean.replace("-", " ")
    }

    # -------------------------------
    # Numeric measures ONLY
    # -------------------------------
    if is_measure:
        numeric_synonyms = {
            "amount": ["amount", "value", "total"],
            "sales": ["sales", "revenue", "turnover"],
            "cost": ["cost", "expense"],
            "price": ["price", "rate"]
        }

        for key, syns in numeric_synonyms.items():
            if key in clean:
                variants.update(syns)

    # -------------------------------
    # Dimensions ONLY
    # -------------------------------
    else:
        dimension_synonyms = {
            "product": ["product", "item", "sku", "commodity"],
            "country": ["country", "region", "market", "geo"],
            "date": ["date", "time", "period", "day"],
            "person": ["person", "employee", "salesperson"]
        }

        for key, syns in dimension_synonyms.items():
            if key in clean:
                variants.update(syns)

    return sorted(variants)