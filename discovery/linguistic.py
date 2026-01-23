import re

def generate_linguistic_metadata(semantic_index: dict) -> dict:
    """
    Step 2: Creates the machine-facing ontology for concept resolution.
    This provides the 'Vocabulary' for the LLM Planner.
    """
    entities = {}

    for table_name, table_info in semantic_index["tables"].items():
        # Add Table as an entity
        entities[table_name] = {
            "kind": "table",
            "binding": {"table": table_name},
            "terms": [table_name.lower(), table_name.replace("_", " ").lower()]
        }

        # Add Columns/Measures as entities
        for col in table_info["columns"]:
            entity_id = f"{table_name}.{col.lower().replace(' ', '_')}"
            
            is_measure = col in table_info["measures"]
            
            entities[entity_id] = {
                "kind": "measure" if is_measure else "column",
                "binding": {
                    "table": table_name,
                    "column": col,
                    "measure": is_measure,
                    "dataType": table_info["columns"][col]["dataType"]
                },
                "terms": _expand_terms(col)
            }

    return {
        "language": "en-US",
        "entities": entities
    }

def _expand_terms(name: str) -> list:
    """
    Generates synonyms and variants for a column name.
    """
    clean = name.lower()
    variants = {clean, clean.replace("_", " "), clean.replace("-", " ")}
    
    # Common Business Synonyms
    synonyms = {
        "sales": ["revenue", "amount", "sales", "turnover"],
        "country": ["region", "geo", "location", "market"],
        "product": ["item", "sku", "commodity"],
        "date": ["time", "period", "day"]
    }
    
    for key, syns in synonyms.items():
        if key in clean:
            variants.update(syns)
            
    return sorted(list(variants))