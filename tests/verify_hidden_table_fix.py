
import sys
import os

# Add the project root to the path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from discovery.tmdl_parser import load_tmdl_files
from discovery.indexer import extract_semantic_index
from config.settings import SEMANTIC_MODEL_PATH

def test_hidden_tables_are_excluded():
    print(f"Loading TMDL from: {SEMANTIC_MODEL_PATH}")
    tmdl = load_tmdl_files(SEMANTIC_MODEL_PATH)
    
    # Check if we can find the LocalDateTable in the raw TMDL loading
    hidden_tables_found = [name for name, data in tmdl.items() if data.get("isHidden")]
    print(f"Found {len(hidden_tables_found)} hidden tables in raw TMDL:")
    for t in hidden_tables_found:
        print(f" - {t}")
        
    if not hidden_tables_found:
        print("WARNING: No hidden tables found in raw files? This might mean the test data changed or parser is broken.")
    
    print("\nExtracting semantic index...")
    index = extract_semantic_index(tmdl)
    
    # Check if any hidden tables leaked into the index
    leaked_tables = []
    for table_name in index["tables"].keys():
        if "LocalDateTable" in table_name or "DateTableTemplate" in table_name:
             leaked_tables.append(table_name)
             
    if leaked_tables:
        print(f"FAILED: Found {len(leaked_tables)} internal tables in the semantic index:")
        for t in leaked_tables:
            print(f" - {t}")
        sys.exit(1)
    else:
        print("SUCCESS: No internal date tables found in the semantic index.")
        
    # Double check that 'orders_rows' IS present
    if "orders_rows" not in index["tables"]:
         print("FAILED: 'orders_rows' table is missing from index!")
         sys.exit(1)
         
    print("Verification Passed!")

if __name__ == "__main__":
    test_hidden_tables_are_excluded()
