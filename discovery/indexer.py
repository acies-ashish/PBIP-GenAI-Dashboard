def extract_semantic_index(tmdl_tables: dict) -> dict:
    """
    Step 1B: Categorizes TMDL artifacts into a semantic ground truth.
    """
    semantic_index = {
        "tables": {},
        "all_dimensions": set(),
        "all_measures": set()
    }

    for table_name, table_data in tmdl_tables.items():
        cols = table_data.get("columns", {})
        dimensions = []
        measures = []

        for col_name, meta in cols.items():
            dtype = meta.get("dataType", "")
            summarize = meta.get("summarizeBy", "none")

            # Heuristic for Measure vs Dimension
            # Measures usually have an active summarization (sum, count, etc)
            if summarize in {"sum", "count", "average", "min", "max"}:
                measures.append(col_name)
                semantic_index["all_measures"].add(col_name)
            else:
                dimensions.append(col_name)
                semantic_index["all_dimensions"].add(col_name)

        semantic_index["tables"][table_name] = {
            "columns": list(cols.keys()),
            "dimensions": dimensions,
            "measures": measures
        }

    # Clean up sets for JSON compatibility
    semantic_index["all_dimensions"] = sorted(list(semantic_index["all_dimensions"]))
    semantic_index["all_measures"] = sorted(list(semantic_index["all_measures"]))

    return semantic_index