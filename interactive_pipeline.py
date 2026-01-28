import shutil
import os
import sys
from discovery.tmdl_parser import load_tmdl_files
from discovery.indexer import extract_semantic_index
from discovery.linguistic import generate_linguistic_metadata
from agents.visual_planner import agent_plan_visuals
from compiler.binder import VisualBinder
from backend.pbip_writer import materialize_visual
from agents.layout_planner import LayoutPlanner
from config.settings import SEMANTIC_MODEL_PATH, REPORT_PATH
from core.models import BoundVisual
from typing import List

class DashboardSession:
    """
    Manages the conversational state of the dashboard.
    """
    def __init__(self):
        print("--- initializing dashboard session ---")
        
        # 1. Load Metadata (Once per session)
        print("[1/3] loading tmdl...")
        self.tmdl = load_tmdl_files(SEMANTIC_MODEL_PATH)
        
        print("[2/3] indexing semantics...")
        self.index = extract_semantic_index(self.tmdl)
        
        print("[3/3] generating linguistic metadata...")
        self.linguistic = generate_linguistic_metadata(self.index)
        
        # Prepare concept list for the LLM
        self.concept_list = [
            e["terms"][0] 
            for e in self.linguistic["entities"].values() 
            if e.get("kind") != "table"
        ]
        
        # STATE
        self.current_intents = [] # List of VisualIntent
        self.dashboard_title = "Dashboard"
        
        # Components
        self.binder = VisualBinder(self.linguistic)
        self.layout_planner = LayoutPlanner()
        print("--- session ready ---\n")

    def turn(self, user_query: str):
        print(f"\n>>> USER: {user_query}")
        
        # 1. PLAN / REFINE (Pass current state)
        new_intents, new_title = agent_plan_visuals(
            user_query, 
            self.concept_list, 
            current_state=self.current_intents # <--- THE KEY CHANGE
        )
        
        # Update State
        self.current_intents = new_intents
        self.dashboard_title = new_title
        
        # 2. MATERIALIZE (Re-build everything)
        self._materialize()

    def _materialize(self):
        bound_visuals = []
        
        # Helper for Variation Tables
        date_binding = None
        variation_table_name = None
        def _find_variation(tbl, col):
            t_def = self.tmdl.get(tbl, {})
            c_def = t_def.get("columns", {}).get(col, {})
            return c_def.get("variationTable")

        # BINDING
        for intent in self.current_intents:
            try:
                bound = self.binder.bind(intent)
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
                print(f"[ERROR] Failed to bind visual '{intent.title}': {e}")

        # AUTO-INJECT SLICER
        if date_binding and variation_table_name:
            # Check if slicer already exists in intents? 
            # Ideally the Planner should manage this, but for now we keep the heuristic
            # BUT we should be careful not to double-add if we are maintaining state.
            # Actually, since we rebuild from `current_intents` (which are abstract), 
            # and the slicer is an infrastructure injection, it's safe to re-inject it every time 
            # as long as it's not in the abstract state.
            
            print(f"[PIPELINE] Auto-Injecting Date Slicer")
            slicer = BoundVisual(
                visual_name="date_slicer",
                visual_type="date_slicer",
                title="Date Slicer",
                bindings=[date_binding],
                metadata={"variationTable": variation_table_name}
            )
            bound_visuals.append(slicer)

        # LAYOUT
        planned_visuals = self.layout_planner.plan_layout(bound_visuals, dashboard_title=self.dashboard_title)

        # WRITE TO DISK
        # Clear existing visuals first
        if os.path.exists(REPORT_PATH):
            for filename in os.listdir(REPORT_PATH):
                file_path = os.path.join(REPORT_PATH, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f"Failed to delete {file_path}: {e}")
        else:
            os.makedirs(REPORT_PATH, exist_ok=True)

        for i, bound in enumerate(planned_visuals, 1):
            try:
                materialize_visual(bound, REPORT_PATH, i)
            except Exception as e:
                print(f"Failed to generate visual {bound.title}: {e}")
                
        print(f"\n[SUCCESS] Dashboard updated with {len(planned_visuals)} visuals.")

def main():
    print("Starting Interactive PBIP GenAI Pipeline...")
    session = DashboardSession()
    
    print("\n---------------------------------------------------------")
    print(" CONVERSATIONAL MODE ENGAGED")
    print(" Type your query below. Type 'exit' or 'quit' to stop.")
    print("---------------------------------------------------------\n")
    
    while True:
        try:
            query = input("User> ").strip()
            if not query:
                continue
            if query.lower() in ["exit", "quit"]:
                print("Good bye!")
                break
                
            session.turn(query)
            
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
