
import os
import json
import shutil
from discovery.tmdl_parser import load_tmdl_files
from discovery.indexer import extract_semantic_index
from discovery.linguistic import generate_linguistic_metadata
from config.settings import SEMANTIC_MODEL_PATH
from llm.token_tracker import tracker

METADATA_DIR = "metadata"

def build_metadata():
    print("--- STARTING METADATA BUILD ---")
    
    # Ensure metadata directory exists
    if not os.path.exists(METADATA_DIR):
        os.makedirs(METADATA_DIR)
        
    # 1. Load TMDL
    print(f"[BUILD] Loading TMDL from {SEMANTIC_MODEL_PATH}...")
    tmdl = load_tmdl_files(SEMANTIC_MODEL_PATH)
    
    # Save TMDL dump (for variation checking in pipeline)
    # We strip out some heavy parts if needed, but saving full dict is safer for now
    with open(os.path.join(METADATA_DIR, "tmdl_dump.json"), "w", encoding="utf-8") as f:
        json.dump(tmdl, f, indent=2)
    
    # 2. Build Index
    print("[BUILD] Extracting Semantic Index...")
    index = extract_semantic_index(tmdl)
    
    with open(os.path.join(METADATA_DIR, "semantic_index.json"), "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)
        
    # 3. Generate Linguistic Metadata (LLM Calls)
    print("[BUILD] Generating Linguistic Metadata (using LLM)...")
    tracker.reset() # Reset before heavy lifting
    linguistic = generate_linguistic_metadata(index)
    
    with open(os.path.join(METADATA_DIR, "linguistic_metadata.json"), "w", encoding="utf-8") as f:
        json.dump(linguistic, f, indent=2)
        
    print(f"\n[BUILD] SUCCESS! Metadata saved to '{METADATA_DIR}/'")
    tracker.print_summary()

if __name__ == "__main__":
    build_metadata()
