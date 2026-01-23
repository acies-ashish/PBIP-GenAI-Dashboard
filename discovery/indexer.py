def extract_semantic_index(tmdl_tables: dict) -> dict:
    """
    Step 1B: Categorizes TMDL artifacts into a semantic ground truth.
    PRESERVES column-level metadata (datatype, summarizeBy).
    """

    semantic_index = {
        "tables": {},
        "all_dimensions": set(),
        "all_measures": set()
    }

    for table_name, table_data in tmdl_tables.items():
        cols = table_data.get("columns", {})
        dimensions = []
        measures = {}

        # Preserve full column metadata
        column_metadata = {}

        for col_name, meta in cols.items():
            data_type = meta.get("dataType", "unknown")
            summarize = meta.get("summarizeBy", "none")

            column_metadata[col_name] = {
                "dataType": data_type,
                "summarizeBy": summarize
            }

            # Heuristic: Measure vs Dimension
            if summarize in {"sum", "count", "average", "min", "max"}:
                measures[col_name] = {
                    "dataType": data_type,
                    "summarizeBy": summarize
                }
                semantic_index["all_measures"].add(col_name)
            else:
                dimensions.append(col_name)
                semantic_index["all_dimensions"].add(col_name)

        semantic_index["tables"][table_name] = {
            # FULL metadata retained here
            "columns": column_metadata,
            "dimensions": dimensions,
            "measures": measures
        }

    # Clean up sets for JSON compatibility
    semantic_index["all_dimensions"] = sorted(list(semantic_index["all_dimensions"]))
    semantic_index["all_measures"] = sorted(list(semantic_index["all_measures"]))

    return semantic_index
