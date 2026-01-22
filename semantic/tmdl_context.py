# semantic/tmdl_context.py
import os

# -------------------------------------------------
# Load all TMDL files
# -------------------------------------------------
def load_tmdl_files(tmdl_root: str) -> dict:
    tables = {}

    for file in os.listdir(tmdl_root):
        if not file.endswith(".tmdl"):
            continue

        with open(os.path.join(tmdl_root, file), "r", encoding="utf-8") as f:
            content = f.read()

        table_name, table_def = parse_tmdl_table(content)
        tables[table_name] = table_def

    return tables


# -------------------------------------------------
# Parse a single TMDL table
# -------------------------------------------------
def parse_tmdl_table(tmdl_text: str) -> tuple[str, dict]:
    lines = tmdl_text.splitlines()

    table_name = None
    columns = {}
    current_col = None

    for raw in lines:
        line = raw.strip()

        if line.startswith("table "):
            table_name = line.replace("table", "").strip()
            continue

        if line.startswith("column "):
            col = line.replace("column", "").strip().strip("'")
            current_col = col
            columns[col] = {}
            continue

        if current_col:
            if line.startswith("dataType:"):
                columns[current_col]["dataType"] = line.split(":", 1)[1].strip().lower()
            elif line.startswith("summarizeBy:"):
                columns[current_col]["summarizeBy"] = line.split(":", 1)[1].strip().lower()

    return table_name, {"columns": columns}


# -------------------------------------------------
# Build semantic index (STRICT)
# -------------------------------------------------
def extract_semantic_index(tmdl_files: dict) -> dict:
    semantic_index = {
        "tables": {},
        "all_dimensions": set(),
        "all_measures": set()
    }

    for table_name, table in tmdl_files.items():
        cols = table["columns"]

        dimensions = []
        measures = []

        for col_name, meta in cols.items():
            dtype = meta.get("dataType", "")
            summarize = meta.get("summarizeBy", "")

            if dtype in {"string", "date", "datetime"}:
                dimensions.append(col_name)
                semantic_index["all_dimensions"].add(col_name)

            if summarize in {"sum", "count", "average", "min", "max"}:
                measures.append(col_name)
                semantic_index["all_measures"].add(col_name)

        semantic_index["tables"][table_name] = {
            "columns": list(cols.keys()),
            "dimensions": dimensions,
            "measures": measures
        }

    # Convert sets → lists for JSON safety
    semantic_index["all_dimensions"] = sorted(semantic_index["all_dimensions"])
    semantic_index["all_measures"] = sorted(semantic_index["all_measures"])

    return semantic_index
