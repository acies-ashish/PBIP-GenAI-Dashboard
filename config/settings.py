# config/settings.py
from dotenv import load_dotenv
import os
load_dotenv()

PROJECT_ROOT = os.getenv("PROJECT_ROOT")

REPORT_PATH = os.path.join(
    PROJECT_ROOT,
    "PowerBI",
    "PowerBI-GenAI-Dashboard.Report",
    "definition",
    "pages",
    "page-1",
    "visuals"
)

SEMANTIC_MODEL_PATH = os.path.join(
    PROJECT_ROOT,
    "PowerBI",
    "PowerBI-GenAI-Dashboard.SemanticModel",
    "definition",
    "tables"
)

LINGUISTIC_METADATA_PATH = os.path.join(
    PROJECT_ROOT,
    "semantic",
    "linguistic_metadata.json"
)

VISUAL_WIDTH = 450
VISUAL_HEIGHT = 300
VISUAL_PADDING = 40

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(BASE_DIR)  # project root


TEMPLATE_MAP = {
    "bar": os.path.join(BASE_DIR, "template", "column-template.json"),
    "column": os.path.join(BASE_DIR, "template", "column-template.json"),
    "line": os.path.join(BASE_DIR, "template", "line-template.json"),
    "pie": os.path.join(BASE_DIR, "template", "pie-template.json"),
    "table": os.path.join(BASE_DIR, "template", "table-template.json")
}

PLANNER_MODEL = "llama-3.3-70b-versatile"
DASHBOARD_MODEL = "llama-3.3-70b-versatile"

# -------------------------------
# Synonym Generation Settings
# -------------------------------
SYNONYM_MODEL = PLANNER_MODEL  # Use same model as planner for synonym generation
ENABLE_LLM_SYNONYMS = True  # Set to False to use basic fallback expansion only
SYNONYM_CACHE_PATH = os.path.join(BASE_DIR, "cache", "synonyms_cache.json")  # Cache for generated synonyms