import os
import re

def load_tmdl_files(tmdl_root: str) -> dict:
    """
    Step 1A: Load all .tmdl files from the semantic model directory.
    """
    tables = {}
    if not os.path.exists(tmdl_root):
        raise FileNotFoundError(f"TMDL path not found: {tmdl_root}")

    for file in os.listdir(tmdl_root):
        if not file.endswith(".tmdl"):
            continue

        file_path = os.path.join(tmdl_root, file)
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        table_name, table_def = _parse_table_content(content)
        if table_name:
            tables[table_name] = table_def

    return tables

def _parse_table_content(tmdl_text: str) -> tuple:
    """
    Parses TMDL syntax to extract table names and column metadata.
    """
    lines = tmdl_text.splitlines()
    table_name = None
    columns = {}
    is_hidden = False
    current_col = None

    for raw in lines:
        line = raw.strip()
        if not line: continue

        # Identify Table
        if line.startswith("table "):
            table_name = line.replace("table", "").strip().strip("'")
            continue

        # Table Properties
        if not current_col:
            if line == "isHidden":
                is_hidden = True
            
        # Identify Column
        if line.startswith("column "):
            # Handle quoted or unquoted column names
            col_match = re.search(r"column\s+'?([^']+)'?", line)
            if col_match:
                current_col = col_match.group(1)
                columns[current_col] = {"dataType": "unknown", "summarizeBy": "none"}
            continue

        # Column Metadata
        if current_col:
            if ":" in line:
                if line.startswith("dataType:"):
                    columns[current_col]["dataType"] = line.split(":", 1)[1].strip().lower()
                elif line.startswith("summarizeBy:"):
                    columns[current_col]["summarizeBy"] = line.split(":", 1)[1].strip().lower()
                elif line.startswith("defaultHierarchy:"):
                    # Extract: LocalDateTable_... .'Date Hierarchy'
                    val = line.split(":", 1)[1].strip()
                    # We just want the table name part usually, which is before the dot
                    if "." in val:
                        columns[current_col]["variationTable"] = val.split(".")[0].strip()

    return table_name, {"columns": columns, "isHidden": is_hidden}