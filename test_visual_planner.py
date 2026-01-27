"""
Quick test script for visual planner without running full pipeline.
Tests if KPIs are being generated correctly.
"""

import sys
sys.path.insert(0, '.')

from agents.visual_planner import agent_plan_visuals

# Test queries
test_queries = [
    "Sales by category and Sales by product along with 3 best KPIs",
    "Show me 3 KPIs",
    "Generate 3 charts",
    "Top 5 products by sales",
    "Total sales and total quantity",
]

# Mock concept list (use your actual concepts)
concepts = [
    "category", "product_name", "total_price", "quantity", "unit_price",
    "order_date", "customer_name", "region", "order_status"
]

print("=" * 80)
print("VISUAL PLANNER TEST - KPI Generation")
print("=" * 80)

for i, query in enumerate(test_queries, 1):
    print(f"\n{'=' * 80}")
    print(f"TEST {i}: {query}")
    print(f"{'=' * 80}")
    
    try:
        intents, title = agent_plan_visuals(query, concepts)
        
        print(f"\nDashboard Title: {title}")
        print(f"Generated {len(intents)} visuals:\n")
        
        for j, intent in enumerate(intents, 1):
            print(f"{j}. Visual Type: {intent.visual_type.upper()}")
            print(f"   Title: {intent.title}")
            print(f"   Concepts: {intent.concepts}")
            if intent.top_n:
                print(f"   Top N: {intent.top_n}")
            print()
        
        # Check for KPIs
        kpi_count = sum(1 for i in intents if i.visual_type == "card")
        if "kpi" in query.lower() or "metric" in query.lower():
            if kpi_count > 0:
                print(f"✅ SUCCESS: Found {kpi_count} KPI card(s)")
            else:
                print(f"❌ FAILED: No KPI cards found but query requested KPIs!")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
