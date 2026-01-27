from discovery.tmdl_parser import load_tmdl_files
from discovery.indexer import extract_semantic_index
from discovery.linguistic import generate_linguistic_metadata
import shutil
import os
from agents.visual_planner import agent_plan_visuals
from compiler.binder import VisualBinder
from backend.pbip_writer import materialize_visual
from agents.layout_planner import LayoutPlanner
from config.settings import SEMANTIC_MODEL_PATH, REPORT_PATH
from core.models import BoundVisual

def run_genai_pipeline(user_query: str):
    # --- INFRASTRUCTURE (Step 1 & 2) ---
    tmdl = load_tmdl_files(SEMANTIC_MODEL_PATH)
    index = extract_semantic_index(tmdl)
    linguistic = generate_linguistic_metadata(index)
    
    # Get flat list of terms for the LLM to choose from
    # EXCLUDE tables to prevent the LLM from selecting them as concepts
    concept_list = [
        e["terms"][0] 
        for e in linguistic["entities"].values() 
        if e.get("kind") != "table"
    ]

    # --- FRONTEND (Step 3 & 4) ---
    # Convert query into Abstract Intent
    intents, dashboard_title = agent_plan_visuals(user_query, concept_list)

    # --- MIDDLE & BACKEND (Step 5 & 6) ---
    binder = VisualBinder(linguistic)
    layout_planner = LayoutPlanner()
    
    bound_visuals = []
    
    # 5a. Bind all visuals ( Semantic -> Physical )
    # 5a. Bind all visuals ( Semantic -> Physical )
    date_binding = None
    variation_table_name = None
    
    # Helper to find date variations from loaded TMDL
    def _find_variation(tbl, col):
        # We need to access individual table defs from tmdl
        t_def = tmdl.get(tbl, {})
        c_def = t_def.get("columns", {}).get(col, {})
        return c_def.get("variationTable")

    for intent in intents:
        try:
            bound = binder.bind(intent)
            bound_visuals.append(bound)
            
            # Check for date columns to trigger slicer
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
            
    # 5a.2. Auto-Inject Date Slicer
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

    # 5b. Plan Layout ( Assign positions )
    planned_visuals = layout_planner.plan_layout(bound_visuals, dashboard_title=dashboard_title)

    # 6. Materialize ( Physical -> PBIP )
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

if __name__ == "__main__":
    run_genai_pipeline("Give me a comprehensive performance review of the last 6 months including sales trends, category distribution, and regional revenue breakdown.")