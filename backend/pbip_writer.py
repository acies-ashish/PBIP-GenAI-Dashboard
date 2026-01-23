import json
import os
import uuid
from core.models import BoundVisual, PhysicalBinding

# -------------------------------------------------------------------------
# 1. THE VISUAL REGISTRY (Configuration)
# -------------------------------------------------------------------------
VISUAL_REGISTRY = {
    "table": {
        "pbi_type": "tableEx",
        "roles": {
            "dimensions": "Values",
            "measures": "Values"
        }
    },
    "bar": {
        "pbi_type": "barChart",
        "roles": {
            "dimensions": "Category",
            "measures": "Y"
        }
    },
    "column": {
        "pbi_type": "columnChart",
        "roles": {
            "dimensions": "Category",
            "measures": "Y"
        }
    },
    "line": {
        "pbi_type": "lineChart",
        "roles": {
            "dimensions": "Category",
            "measures": "Y"
        }
    },
    "pie": { # Added based on your template
        "pbi_type": "pieChart",
        "roles": {
            "dimensions": "Category",
            "measures": "Y"
        }
    }
}

# -------------------------------------------------------------------------
# 2. FIELD FACTORY (The Source of Truth)
# -------------------------------------------------------------------------
class FieldFactory:
    """
    Generates standardized Power BI Field Expressions.
    """
    @staticmethod
    def create_base_expression(binding: PhysicalBinding, alias: str = None):
        entity = alias if alias else binding.table
        return {
            "Column": {
                "Expression": {"SourceRef": {"Entity": entity}} if not alias else {"SourceRef": {"Source": alias}},
                "Property": binding.column
            }
        }

    @staticmethod
    def create_aggregation_expression(binding: PhysicalBinding, alias: str = None):
        col_expr = FieldFactory.create_base_expression(binding, alias)
        agg_map = {"sum": 0, "avg": 1, "min": 2, "max": 3, "count": 4}
        func_id = agg_map.get(binding.aggregation, 0)
        return {
            "Aggregation": {
                "Expression": col_expr, 
                "Function": func_id
            }
        }, func_id

# -------------------------------------------------------------------------
# 3. FEATURE BUILDERS (Additive Logic)
# -------------------------------------------------------------------------
def build_top_n_filter(dim_binding: PhysicalBinding, measure_binding: PhysicalBinding, n: int):
    t_name = dim_binding.table
    alias_name = "d"
    
    dim_expr_alias = FieldFactory.create_base_expression(dim_binding, alias=alias_name)
    meas_expr_alias, func_id = FieldFactory.create_aggregation_expression(measure_binding, alias=alias_name)
    dim_expr_entity = FieldFactory.create_base_expression(dim_binding)

    return {
        "name": uuid.uuid4().hex[:20],
        "type": "TopN",
        "field": dim_expr_entity,
        "filter": {
            "Version": 2,
            "From": [
                {
                    "Name": "subquery", 
                    "Expression": {
                        "Subquery": {
                            "Query": {
                                "Version": 2,
                                "From": [{"Name": alias_name, "Entity": t_name, "Type": 0}],
                                "Select": [{
                                    "Column": dim_expr_alias["Column"],
                                    "Name": "field"
                                }],
                                "OrderBy": [{
                                    "Direction": 2, 
                                    "Expression": meas_expr_alias
                                }],
                                "Top": n
                            }
                        }
                    },
                    "Type": 2
                },
                {
                    "Name": alias_name,
                    "Entity": t_name,
                    "Type": 0
                }
            ],
            "Where": [{
                "Condition": {
                    "In": {
                        "Expressions": [dim_expr_alias],
                        "Table": {"SourceRef": {"Source": "subquery"}}
                    }
                }
            }]
        }
    }

# -------------------------------------------------------------------------
# 4. MAIN WRITER FUNCTION
# -------------------------------------------------------------------------
def materialize_visual(bound: BoundVisual, output_dir: str, index: int):
    visual_id = uuid.uuid4().hex[:6]
    visual_name = f"GenAI_Visual_{index}_{visual_id}"
    folder_path = os.path.join(output_dir, visual_name)
    os.makedirs(folder_path, exist_ok=True)

    # A. Config
    config = VISUAL_REGISTRY.get(bound.visual_type, VISUAL_REGISTRY["table"])
    pbi_type = config["pbi_type"]
    
    # B. Bindings
    dims = [b for b in bound.bindings if b.kind == "dimension"]
    measures = [b for b in bound.bindings if b.kind == "measure"]

    if bound.visual_type != "table" and not dims and len(measures) >= 2:
        print("[WRITER] Converting first measure to dimension for chart safety.")
        forced_dim = measures.pop(0)
        forced_dim.kind = "dimension"
        forced_dim.aggregation = None
        dims = [forced_dim]

    # C. Build Query State
    query_state = {}
    
    def _humanize(s):
        """Converts 'payment_method' -> 'Payment Method'"""
        return s.replace("_", " ").title()

    def add_projection(role_name, binding_list):
        if not binding_list: return
        if role_name not in query_state: query_state[role_name] = {"projections": []}
        
        for b in binding_list:
            human_name = _humanize(b.column)
            
            if b.kind == "measure":
                field_expr, _ = FieldFactory.create_aggregation_expression(b)
                func = b.aggregation.capitalize() if b.aggregation else "Sum"
                q_ref = f"{func}({b.table}.{b.column})"
                
                query_state[role_name]["projections"].append({
                    "field": field_expr,
                    "queryRef": q_ref,
                    "nativeQueryRef": human_name,
                    "displayName": human_name
                })
            else:
                field_expr = FieldFactory.create_base_expression(b)
                q_ref = f"{b.table}.{b.column}"
                query_state[role_name]["projections"].append({
                    "field": field_expr,
                    "queryRef": q_ref,
                    "nativeQueryRef": human_name,
                    "active": True,
                    "displayName": human_name
                })

    add_projection(config["roles"]["dimensions"], dims)
    add_projection(config["roles"]["measures"], measures)

    # D. Additive Features
    sort_def = None
    filter_config = {}

    if bound.top_n and dims and measures:
        primary_dim = dims[0]
        primary_meas = measures[0]
        
        # Sort Definition (Top N)
        meas_expr, _ = FieldFactory.create_aggregation_expression(primary_meas)
        sort_def = {
            "sort": [{"field": meas_expr, "direction": "Descending"}],
            "isDefaultSort": True
        }

        # Filter Config (Top N)
        filter_obj = build_top_n_filter(primary_dim, primary_meas, bound.top_n)
        filter_config = {"filters": [filter_obj]}
    
    # Default Sort for Bar/Column/Pie charts (if Top N is NOT present)
    elif bound.visual_type in ["bar", "column", "pie"] and measures:
         meas_expr, _ = FieldFactory.create_aggregation_expression(measures[0])
         sort_def = {
            "sort": [{"field": meas_expr, "direction": "Descending"}],
            "isDefaultSort": True
        }

    # E. Construct Final JSON
    visual_container = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.4.0/schema.json",
        "name": visual_name,
        "position": {
            "x": 10 + ((index-1) * 20), "y": 10 + ((index-1) * 20), "z": 0,
            "width": 600, "height": 400, "tabOrder": index
        },
        "visual": {
            "visualType": pbi_type,
            "query": {
                "queryState": query_state
            },
            "visualContainerObjects": {
                "title": [{"properties": {"text": {"expr": {"Literal": {"Value": f"'{bound.title}'"}}}}}]
            },
            "drillFilterOtherVisuals": True
        }
    }

    if sort_def:
        visual_container["visual"]["query"]["sortDefinition"] = sort_def
    
    if filter_config:
        visual_container["filterConfig"] = filter_config

    with open(os.path.join(folder_path, "visual.json"), "w", encoding="utf-8") as f:
        json.dump(visual_container, f, indent=2)
        
    print(f"[WRITER] Generated {pbi_type} at {folder_path}")