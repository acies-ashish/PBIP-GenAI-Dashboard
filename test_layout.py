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
    planned = planner.plan_layout(visuals)
    
    # VERIFY
    cards = [v for v in planned if v.visual_type == "card"]
    charts = [v for v in planned if v.visual_type != "card"]
    
    print("\n[RESULTS]")
    for v in planned:
        l = v.layout
        print(f"[{v.visual_type}] {v.title}: x={l.x}, y={l.y}, w={l.width}, h={l.height}, tab={l.tabOrder}")
        
        # BASIC ASSERTIONS
        if v.visual_type == "card":
            if l.y != LayoutPlanner.PADDING:
                print(f"!! FAIL: Card should be at y={LayoutPlanner.PADDING}")
            if l.height != 150:
                print(f"!! FAIL: Card height should be 150")
        else:
            if l.y <= 150 + LayoutPlanner.PADDING:
                 print(f"!! FAIL: Chart overlapping with card row")
                 
    # Check overlaps?
    # Simplified check
    print("\nTest Complete.")

if __name__ == "__main__":
    test_layout_logic()
