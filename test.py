from backend.pbip_writer import materialize_visual
from core.models import BoundVisual, PhysicalBinding
import os

# ---------------------------------------------------------
# MOCK SCENARIO: "Top 3 Products by Amount"
# ---------------------------------------------------------
# This replicates the exact output expected from the Binder
# for a Clustered Bar Chart with a Top N filter.

mock_visual = BoundVisual(
    visual_name="test_chart_001",
    visual_type="bar", # Will map to clusteredBarChart
    title="TEST: Top 3 Products by Amount",
    top_n=3,
    bindings=[
        # 1. Dimension Binding (Category/Axis)
        PhysicalBinding(
            concept_name="product",
            table="data",
            column="Product",
            kind="dimension",
            aggregation=None
        ),
        # 2. Measure Binding (Y-Axis/Values)
        PhysicalBinding(
            concept_name="amount",
            table="data",
            column="Amount",
            kind="measure",
            aggregation="sum" # Explicit aggregation
        )
    ]
)

# ---------------------------------------------------------
# EXECUTION
# ---------------------------------------------------------
# Define where to save the test visual
# Change this path if your folder structure is different
OUTPUT_DIR = os.path.join(os.getcwd(), "PowerBI", "PowerBI-GenAI-Dashboard.Report", "definition", "pages", "page-1", "visuals")

print(f"--- STARTING WRITER TEST ---")
print(f"Target Visual: {mock_visual.title}")
print(f"Top N: {mock_visual.top_n}")

try:
    # Call the writer function directly
    materialize_visual(mock_visual, OUTPUT_DIR, 999) # Using index 999 to stand out
    
    print(f"\n[SUCCESS] Visual generated successfully.")
    print(f"Check folder: GenAI_Visual_999_...")
    print(f"Verify 'visual.json' contains 'filterConfig' and 'sortDefinition'.")

except Exception as e:
    print(f"\n[FAILURE] Writer crashed: {e}")