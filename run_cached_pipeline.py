
import os
import json
import shutil
from agents.visual_planner import agent_plan_visuals
from compiler.binder import VisualBinder
from backend.pbip_writer import materialize_visual
from agents.layout_planner import LayoutPlanner
from config.settings import REPORT_PATH
from core.models import BoundVisual
from llm.token_tracker import tracker

METADATA_DIR = "metadata"

def load_metadata():
    print(f"[CACHE] Loading metadata from {METADATA_DIR}...")
    
    with open(os.path.join(METADATA_DIR, "tmdl_dump.json"), "r", encoding="utf-8") as f:
        tmdl = json.load(f)
        
    with open(os.path.join(METADATA_DIR, "linguistic_metadata.json"), "r", encoding="utf-8") as f:
        linguistic = json.load(f)
        
    return tmdl, linguistic

def run_cached_pipeline(user_query: str):
    print("--- STARTING CACHED PIPELINE ---")
    tracker.reset() # Reset stats for this run
    
    # 1. Load Metadata (Fast, no LLM)
    tmdl, linguistic = load_metadata()
    
    # 2. Get concept list
    concept_list = [
        e["terms"][0] 
        for e in linguistic["entities"].values() 
        if e.get("kind") != "table"
    ]
    
    # 3. PLAN (LLM Call 1)
    print(f"[PIPELINE] Planning visuals for: '{user_query}'")
    intents, dashboard_title = agent_plan_visuals(user_query, concept_list)
    
    # 4. BIND & INJECT
    binder = VisualBinder(linguistic)
    layout_planner = LayoutPlanner()
    bound_visuals = []
    
    date_binding = None
    variation_table_name = None
    
    # Helper to find date variations from loaded TMDL (Same logic as original pipeline)
    def _find_variation(tbl, col):
        t_def = tmdl.get(tbl, {})
        c_def = t_def.get("columns", {}).get(col, {})
        return c_def.get("variationTable")

    for intent in intents:
        try:
            bound = binder.bind(intent)
            bound_visuals.append(bound)
            
            # Auto-detect Date Slicer requirement
            if not date_binding:
                for b in bound.bindings:
                    if b.data_type and b.data_type.lower() in ["datetime", "date"]:
                        vt = _find_variation(b.table, b.column)
                        if vt:
                            date_binding = b
                            variation_table_name = vt
                            break
        except Exception as e:
            print(f"FAILED to bind visual '{intent.title}': {e}")

    # Auto-Inject Date Slicer
    if date_binding and variation_table_name:
        print(f"[PIPELINE] Auto-Injecting Date Slicer for {date_binding.table}.{date_binding.column}")
        slicer = BoundVisual(
            visual_name="date_slicer",
            visual_type="date_slicer",
            title="Date Slicer",
            bindings=[date_binding],
            metadata={"variationTable": variation_table_name}
        )
        bound_visuals.append(slicer)
        
    # 5. LAYOUT
    planned_visuals = layout_planner.plan_layout(bound_visuals, dashboard_title=dashboard_title)
    
    # 6. WRITE
    # Clear existing visuals first
    if os.path.exists(REPORT_PATH):
        print(f"[PIPELINE] Clearing visuals at {REPORT_PATH}")
        for filename in os.listdir(REPORT_PATH):
            file_path = os.path.join(REPORT_PATH, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"[PIPELINE] Failed to delete {file_path}. Reason: {e}")
    else:
        os.makedirs(REPORT_PATH, exist_ok=True)
        
    for i, bound in enumerate(planned_visuals, 1):
        try:
            materialize_visual(bound, REPORT_PATH, i)
            print(f"Successfully generated: {bound.title}")
        except Exception as e:
            print(f"Failed to generate visual {bound.title}: {e}")

    # 7. METRICS
    print("\n--- PIPELINE COMPLETE ---")
    tracker.print_summary()

if __name__ == "__main__":
    # Test Query
    query = "Give me a comprehensive performance review of the last 6 months including sales trends, category distribution, and regional revenue breakdown."
    run_cached_pipeline(query)
