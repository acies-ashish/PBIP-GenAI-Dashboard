# semantic/semantic_validator.py

class SemanticValidationError(Exception):
    pass


def validate_semantic_index(index: dict):
    required_keys = {"tables", "all_dimensions", "all_measures"}

    if not required_keys.issubset(index):
        raise SemanticValidationError("Semantic index missing top-level keys")

    if not index["tables"]:
        raise SemanticValidationError("No tables found in semantic index")

    for table_name, table in index["tables"].items():
        if not table["columns"]:
            raise SemanticValidationError(f"Table '{table_name}' has no columns")

        for d in table["dimensions"]:
            if d not in index["all_dimensions"]:
                raise SemanticValidationError(f"Dimension '{d}' not registered globally")

        for m in table["measures"]:
            if m not in index["all_measures"]:
                raise SemanticValidationError(f"Measure '{m}' not registered globally")

    return True
