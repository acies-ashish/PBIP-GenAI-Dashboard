from backend.pbip_writer import materialize_visual
from core.models import BoundVisual, PhysicalBinding
import os

# ---------------------------------------------------------
# MOCK SCENARIO: "Total Sales Amount"
# ---------------------------------------------------------
# Card visual showing a single aggregated KPI

mock_visual = BoundVisual(
    visual_name="test_card_001",
    visual_type="card",  # Will map to Power BI card visual
    title="TEST: Total Sales Amount",
    top_n=None,  # Not applicable for card visuals
    bindings=[
        # 1. Measure Binding ONLY
        PhysicalBinding(
            concept_name="amount",
            table="data",
            column="Amount",
            kind="measure",
            aggregation="sum"
        )
    ]
)

# ---------------------------------------------------------
# EXECUTION
# ---------------------------------------------------------
OUTPUT_DIR = os.path.join(
    os.getcwd(),
    "PowerBI",
    "PowerBI-GenAI-Dashboard.Report",
    "definition",
    "pages",
    "page-1",
    "visuals"
)

print(f"--- STARTING WRITER TEST (CARD VISUAL) ---")
print(f"Target Visual: {mock_visual.title}")
print(f"Visual Type: {mock_visual.visual_type}")

try:
    # Use a unique index to avoid collisions
    materialize_visual(mock_visual, OUTPUT_DIR, 1002)

    print(f"\n[SUCCESS] Card visual generated successfully.")
    print(f"Check folder: GenAI_Visual_1002_...")
    print(f"Verify 'visual.json' uses 'card' and contains a single measure binding.")

except Exception as e:
    print(f"\n[FAILURE] Writer crashed: {e}")
