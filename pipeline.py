from discovery.tmdl_parser import load_tmdl_files
from discovery.indexer import extract_semantic_index
from discovery.linguistic import generate_linguistic_metadata
from agents.visual_planner import agent_plan_visuals
from compiler.binder import VisualBinder
from backend.pbip_writer import materialize_visual
from config.settings import SEMANTIC_MODEL_PATH, REPORT_PATH

def run_genai_pipeline(user_query: str):
    # --- INFRASTRUCTURE (Step 1 & 2) ---
    tmdl = load_tmdl_files(SEMANTIC_MODEL_PATH)
    index = extract_semantic_index(tmdl)
    linguistic = generate_linguistic_metadata(index)
    
    # Get flat list of terms for the LLM to choose from
    concept_list = [e["terms"][0] for e in linguistic["entities"].values()]

    # --- FRONTEND (Step 3 & 4) ---
    # Convert query into Abstract Intent
    intents = agent_plan_visuals(user_query, concept_list)

    # --- MIDDLE & BACKEND (Step 5 & 6) ---
    binder = VisualBinder(linguistic)
    
    for i, intent in enumerate(intents, 1):
        try:
            # Deterministic Binding (Semantic -> Physical)
            bound_visual = binder.bind(intent)
            
            # Deterministic Materialization (Physical -> PBIP)
            # materialize_visual(bound_visual, REPORT_PATH, i)
            
            print(f"Successfully generated: {bound_visual.title}")
        except Exception as e:
            print(f"Failed to generate visual {i}: {e}")

if __name__ == "__main__":
    run_genai_pipeline("sales overview")