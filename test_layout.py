from core.models import BoundVisual, PhysicalBinding, VisualLayout
from agents.layout_planner import LayoutPlanner

def create_mock_visual(v_type: str, title: str):
    return BoundVisual(
        visual_name=f"mock_{v_type}",
        visual_type=v_type,
        title=title,
        bindings=[], # simplified
        top_n=None
    )

def test_layout_logic():
    print("--- TESTING LAYOUT PLANNER ---")
    planner = LayoutPlanner()
    
    # Input: 2 Cards, 2 Charts
    visuals = [
        create_mock_visual("card", "KPI: Total Sales"),
        create_mock_visual("bar", "Sales by Country"),
        create_mock_visual("card", "KPI: Total Orders"),
        create_mock_visual("line", "Sales Trend")
    ]
    
    print(f"Input: {len(visuals)} visuals ({[v.visual_type for v in visuals]})")
    
    # EXECUTE
    # Test with a dynamic title
    planned = planner.plan_layout(visuals, dashboard_title="Sales Overview Test")
    
    # VERIFY
    cards = [v for v in planned if v.visual_type == "card"]
    charts = [v for v in planned if v.visual_type != "card"]
    
    print("\n[RESULTS]")
    for v in planned:
        if v.visual_type == "textbox" and v.title != "Sales Overview Test":
             print(f"!! FAIL: Header title mismatch. Got {v.title}")
        l = v.layout
        print(f"[{v.visual_type}] {v.title}: x={l.x}, y={l.y}, w={l.width}, h={l.height}, tab={l.tabOrder}")
        
        # BASIC ASSERTIONS
        if v.visual_type == "textbox":
             print(f"HEAD found: {v.title} at y={l.y}")
             if l.y != 10:
                 print("!! FAIL: Header should be at y=10")
        elif v.visual_type == "card":
            if l.width != 1240:
                print(f"!! FAIL: Card width should be 1240, got {l.width}")
            if l.height != 110:
                print(f"!! FAIL: Card height should be 110, got {l.height}")
            if l.x != 20:
                 print(f"!! FAIL: Card should be centered at x=20, got {l.x}")
        else:
            if l.y <= 200: # Header (50) + Card (150) + Padding
                 print(f"!! FAIL: Chart potentially overlapping or too high at y={l.y}")
                 
    # Check overlaps?
    # Simplified check
    print("\nTest Complete.")

if __name__ == "__main__":
    test_layout_logic()
