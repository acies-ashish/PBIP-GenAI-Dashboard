import json
import os
import uuid
from core.models import BoundVisual

def materialize_visual(bound: BoundVisual, output_dir: str, index: int):
    """
    Step 6: PBIP Visual Materialization (Schema v2.4.0 compliant).
    Matches the exact structure of a Power BI Desktop 'Top N' visual.
    """
    visual_id = uuid.uuid4().hex[:6]
    visual_name = f"GenAI_Visual_{index}_{visual_id}"
    folder_path = os.path.join(output_dir, visual_name)
    os.makedirs(folder_path, exist_ok=True)

    # ---------------------------------------------------------
    # 1. Determine Visual Type & Roles
    # ---------------------------------------------------------
    pbip_visual_type = "tableEx"
    roles = {} 

    dims = [b for b in bound.bindings if b.kind == "dimension"]
    measures = [b for b in bound.bindings if b.kind == "measure"]

    if bound.visual_type == "table":
        pbip_visual_type = "tableEx"
        roles["Values"] = bound.bindings

    elif bound.visual_type in ["bar", "column", "line"]:
        if bound.visual_type == "column": pbip_visual_type = "clusteredColumnChart"
        elif bound.visual_type == "bar": pbip_visual_type = "clusteredBarChart"
        elif bound.visual_type == "line": pbip_visual_type = "lineChart"
        
        # Failsafe: Ensure Axis exists
        if not dims and len(measures) >= 2:
            print(f"[WRITER WARNING] No dimensions. Forcing {measures[0].column} to Axis.")
            forced_dim = measures.pop(0)
            forced_dim.kind = "dimension"
            forced_dim.aggregation = None
            dims = [forced_dim]

        roles["Category"] = dims
        roles["Y"] = measures

    # ---------------------------------------------------------
    # 2. Helper: Build Field Expression (Entity Scope for Visual)
    # ---------------------------------------------------------
    def build_field_expr(binding):
        # Base Column Object (Entity Reference)
        col_obj = {
            "Column": {
                "Expression": {"SourceRef": {"Entity": binding.table}},
                "Property": binding.column
            }
        }
        
        # Determine Aggregation
        agg_func = 0 # Default Sum
        if binding.aggregation == "count": agg_func = 4
        elif binding.aggregation == "avg": agg_func = 1
        elif binding.aggregation == "min": agg_func = 2
        elif binding.aggregation == "max": agg_func = 3

        # Wrap in Aggregation if measure
        if binding.kind == "measure" or binding.aggregation:
            expr = {
                "Aggregation": {
                    "Expression": col_obj, 
                    "Function": agg_func
                }
            }
            # PBI Function Syntax
            func_name = ["Sum", "Avg", "Min", "Max", "Count"][agg_func]
            if agg_func == 0: func_name = "Sum" 
            
            q_ref = f"{func_name}({binding.table}.{binding.column})"
            native_ref = f"{func_name} of {binding.column}"
            
            return expr, q_ref, native_ref
        
        return col_obj, f"{binding.table}.{binding.column}", None

    # ---------------------------------------------------------
    # 3. Build Query State (Projections)
    # ---------------------------------------------------------
    query_state = {}
    
    # Track primary fields for Filter/Sort
    primary_measure_expr = None
    primary_dim_expr = None # Entity-based expression
    primary_measure_binding = measures[0] if measures else None
    primary_dim_binding = dims[0] if dims else None

    for role, bindings in roles.items():
        if not bindings: continue
        
        projections = []
        for b in bindings:
            expr, q_ref, native_ref = build_field_expr(b)
            
            if b == primary_measure_binding: primary_measure_expr = expr
            if b == primary_dim_binding: primary_dim_expr = expr

            proj_obj = {
                "field": expr,
                "queryRef": q_ref
            }
            
            if b.kind == "dimension" and role == "Category":
                proj_obj["active"] = True
            
            if native_ref:
                proj_obj["nativeQueryRef"] = native_ref
            
            projections.append(proj_obj)
            
        query_state[role] = {"projections": projections}

    # ---------------------------------------------------------
    # 4. Handle Sorting
    # ---------------------------------------------------------
    sort_definition = None
    if bound.top_n and primary_measure_expr:
        sort_definition = {
            "sort": [
                {
                    "field": primary_measure_expr,
                    "direction": "Descending"
                }
            ],
            "isDefaultSort": True
        }

    # ---------------------------------------------------------
    # 5. Handle Top N Filter (Nested Subquery + Alias)
    # ---------------------------------------------------------
    filter_config = {}
    if bound.top_n and primary_dim_binding and primary_measure_binding:
        t_name = primary_dim_binding.table
        dim_col = primary_dim_binding.column
        meas_col = primary_measure_binding.column
        
        agg_code = 0
        if primary_measure_binding.aggregation == "count": agg_code = 4

        # We need a stable alias for the inner query to match the outer reference
        alias_name = "d"

        filter_config = {
            "filters": [
                {
                    "name": uuid.uuid4().hex[:20],
                    "type": "TopN",
                    "field": primary_dim_expr, # References Entity (Correct for global scope)
                    "filter": {
                        "Version": 2,
                        "From": [
                            # 1. The Subquery Limit
                            {
                                "Name": "subquery", 
                                "Expression": {
                                    "Subquery": {
                                        "Query": {
                                            "Version": 2,
                                            "From": [{"Name": alias_name, "Entity": t_name, "Type": 0}],
                                            "Select": [{
                                                "Column": {
                                                    "Expression": {"SourceRef": {"Source": alias_name}},
                                                    "Property": dim_col
                                                },
                                                "Name": "field"
                                            }],
                                            "OrderBy": [{
                                                "Direction": 2, # Descending
                                                "Expression": {
                                                    "Aggregation": {
                                                        "Expression": {
                                                            "Column": {
                                                                "Expression": {"SourceRef": {"Source": alias_name}},
                                                                "Property": meas_col
                                                            }
                                                        },
                                                        "Function": agg_code
                                                    }
                                                }
                                            }],
                                            "Top": bound.top_n
                                        }
                                    }
                                },
                                "Type": 2  # FIXED: Required for Subquery definitions
                            },
                            # 2. The Entity Alias (CRITICAL FIX: This defines 'd' for the Where clause)
                            {
                                "Name": alias_name,
                                "Entity": t_name,
                                "Type": 0
                            }
                        ],
                        "Where": [{
                            "Condition": {
                                "In": {
                                    "Expressions": [{
                                        "Column": {
                                            "Expression": {"SourceRef": {"Source": alias_name}}, # Refers to 'd'
                                            "Property": dim_col
                                        }
                                    }],
                                    "Table": {"SourceRef": {"Source": "subquery"}}
                                }
                            }
                        }]
                    }
                }
            ]
        }

    # ---------------------------------------------------------
    # 6. Construct Final JSON
    # ---------------------------------------------------------
    visual_container = {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.4.0/schema.json",
        "name": visual_name,
        "position": {
            "x": 10 + ((index-1) * 20),
            "y": 10 + ((index-1) * 20),
            "z": 0,
            "width": 600,
            "height": 400,
            "tabOrder": index
        },
        "visual": {
            "visualType": pbip_visual_type,
            "query": {
                "queryState": query_state
            },
            "visualContainerObjects": {
                "title": [{
                    "properties": {
                        "text": {"expr": {"Literal": {"Value": f"'{bound.title}'"}}}
                    }
                }]
            },
            "drillFilterOtherVisuals": True
        }
    }

    if sort_definition:
        visual_container["visual"]["query"]["sortDefinition"] = sort_definition
    
    if filter_config:
        visual_container["filterConfig"] = filter_config

    file_path = os.path.join(folder_path, "visual.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(visual_container, f, indent=2)
    
    print(f"[MATERIALIZER] Wrote {pbip_visual_type} with TopN={bound.top_n} to: {file_path}")