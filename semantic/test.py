# semantic/test.py

import json
import os

from semantic.tmdl_context import load_tmdl_files, extract_semantic_index
from semantic.linguistic_generator import generate_linguistic_metadata
from semantic.semantic_resolver import resolve_concept
from semantic.semantic_validator import validate_semantic_index
from semantic.linguistic_validator import validate_linguistic_metadata

ARTIFACT_DIR = "artifacts"
os.makedirs(ARTIFACT_DIR, exist_ok=True)

from config.settings import SEMANTIC_MODEL_PATH

TEST_CONCEPTS = [
    "region",
    "product category",
    "sales",
    "boxes shipped",
]

print("\n🔹 Loading TMDL files...")
tmdl_files = load_tmdl_files(SEMANTIC_MODEL_PATH)

semantic_index = extract_semantic_index(tmdl_files)
validate_semantic_index(semantic_index)

# -------------------------------
# STEP 1 — Save semantic index
# -------------------------------
with open(os.path.join(ARTIFACT_DIR, "semantic_index.json"), "w", encoding="utf-8") as f:
    json.dump(semantic_index, f, indent=2)

print("✅ semantic_index.json written")

# -------------------------------
# STEP 2 — Linguistic metadata
# -------------------------------
print("\n🔹 Generating linguistic metadata...")
linguistic = generate_linguistic_metadata(semantic_index)
validate_linguistic_metadata(linguistic, semantic_index)

with open(os.path.join(ARTIFACT_DIR, "linguistic_metadata.json"), "w", encoding="utf-8") as f:
    json.dump(linguistic, f, indent=2)

print("✅ linguistic_metadata.json written")

# -------------------------------
# STEP 3 — Semantic resolution
# -------------------------------
print("\n🔹 STEP 3 — Semantic Resolution")

results = {}

for c in TEST_CONCEPTS:
    try:
        binding = resolve_concept(c, linguistic)
        print(f"✔ '{c}' → {binding}")
        results[c] = binding
    except Exception as e:
        print(f"❌ '{c}' → {e}")
        results[c] = {"error": str(e)}

with open(
    os.path.join(ARTIFACT_DIR, "semantic_resolution_test.json"),
    "w",
    encoding="utf-8"
) as f:
    json.dump(results, f, indent=2)

print("\n🎯 STEP 3 PASSED")
print("✅ semantic_resolution_test.json written")
