# semantic/semantic_bindings.py
from semantic.semantic_resolver import resolve_concept

def normalize_table_chart(chart: dict) -> dict:
    """
    Normalizes table chart schema from LLM into a deterministic form.
    """

    # --- Dimensions ---
    if "dimension_concepts" not in chart:
        if "dimension_concept" in chart:
            chart["dimension_concepts"] = [chart.pop("dimension_concept")]
        elif "dimensions" in chart:
            chart["dimension_concepts"] = chart.pop("dimensions")
        else:
            chart["dimension_concepts"] = []

    # --- Measures ---
    if "measure_concepts" not in chart:
        if "measure_concept" in chart and chart["measure_concept"]:
            chart["measure_concepts"] = [chart.pop("measure_concept")]
        else:
            chart["measure_concepts"] = []

    # Force list
    if isinstance(chart["dimension_concepts"], str):
        chart["dimension_concepts"] = [chart["dimension_concepts"]]

    if isinstance(chart["measure_concepts"], str):
        chart["measure_concepts"] = [chart["measure_concepts"]]

    return chart


def bind_chart_concepts(chart: dict, linguistic: dict) -> dict:
    """
    Builds physical column bindings for TABLE visuals.
    Supports multiple dimensions and measures.
    """

    if chart["type"] != "table":
        raise ValueError("Only table visuals are supported")

    columns = []

    # ---- Dimensions (no aggregation) ----
    for concept in chart.get("dimension_concepts", []):
        binding = resolve_concept(concept, linguistic)
        columns.append({
            "entity": binding["entity"],
            "column": binding["column"],
            "aggregation": None
        })

    # ---- Measures (SUM by default) ----
    for concept in chart.get("measure_concepts", []):
        binding = resolve_concept(concept, linguistic)
        columns.append({
            "entity": binding["entity"],
            "column": binding["column"],
            "aggregation": "SUM"
        })

    if not columns:
        raise ValueError("No columns resolved for table")

    chart["columns"] = columns
    return chart
