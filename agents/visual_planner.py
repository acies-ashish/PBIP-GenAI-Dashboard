import json
from typing import List, Tuple
from llm.clients import planner_client
from config.settings import DASHBOARD_MODEL
from core.models import VisualIntent
from llm.token_tracker import tracker

def agent_plan_visuals(user_query: str, available_concepts: List[str]) -> Tuple[List[VisualIntent], str]:
    """
    Step 4: Abstract Visual Planning.
    Produces VisualIntent objects. It is forbidden from seeing table names.
    """
    client = planner_client()

    # Enhanced prompt with specific visual selection rules
    prompt = f"""
    You are a Power BI Architect. 
    Analyze the user query and plan the visuals using ONLY the provided concepts.
    
    User Query: "{user_query}"
    Available Concepts: {available_concepts}
    
    ### STRICT COLUMN SELECTION RULES:
    1. NEVER invent column names. USE ONLY THE EXACT STRINGS from 'Available Concepts'.
    2. If the user asks for "Date" or "Time", DO NOT use a generic "Date" column. Look for specific columns like 'order_date', 'ship_date', etc. in the list.
    3. If a concept is not in the list, ignore it or find the closest match from the list.

    
    ### VISUAL SELECTION RULES:
    
    **PRIORITY 1 - KPIs/Cards (if user explicitly asks for KPIs, metrics, or key numbers):**
    - ALWAYS include a "Key Performance Indicators" card if the query implies a performance review or overview.
    - If the user asks for "KPIs", "key metrics", "best metrics", "important numbers", or "top metrics", create ONE "card" visual containing ALL the requested KPIs
    - Each card can contain up to 5 concepts (measures only, no dimensions)
    - Card title should be descriptive (e.g., "Key Performance Indicators")
    - Only include MEASURES (numeric values), never dimensions
    - Examples of KPI requests: "show 3 KPIs", "top metrics", "key numbers", "important KPIs"
    
    **PRIORITY 2 - Charts (for comparisons, trends, distributions):**
    1. **Comparison by Category**: If comparing a measure across categories (e.g., "sales by region", "sales by product"), use "bar" or "column"
    2. **Trend Over Time**: If analyzing over time (e.g., "sales over time", "monthly revenue"), use "line"
    3. **Distribution/Share**: If asking for parts of a whole (e.g., "sales share by category"), use "pie"
    4. **Top N Rankings**: If ranking is implied (e.g., "top 5 products"), use "bar" and set "top_n" to the number
    5. **Detailed Data Table**: If asking for raw data or multiple columns (e.g., "list products and prices"), use "table"
    
    **IMPORTANT DISTINCTIONS:**
    - "Sales by category" = bar/column chart (comparison)
    - "Total sales" or "Sales KPI" = card visual (single metric)
    - "3 best KPIs" = ONE card with 3 measures
    - "Sales and profit" (no breakdown) = ONE card with both measures
    - "Sales by product AND show KPIs" = bar chart + separate card visual
    
    ### EXAMPLES:
    
    Query: "Show me 3 KPIs"
    Response: {{"charts": [{{"title": "Key Metrics", "visual_type": "card", "concepts": ["total_price", "quantity", "unit_price"], "top_n": null}}]}}
    
    Query: "Sales by category"
    Response: {{"charts": [{{"title": "Sales by Category", "visual_type": "bar", "concepts": ["category", "total_price"], "top_n": null}}]}}
    
    Query: "Sales by product and show 2 KPIs"
    Response: {{"charts": [
        {{"title": "Sales by Product", "visual_type": "bar", "concepts": ["product", "total_price"], "top_n": null}},
        {{"title": "Key Metrics", "visual_type": "card", "concepts": ["total_price", "quantity"], "top_n": null}}
    ]}}
    
    Return a JSON object with:
    1. "dashboard_title": A short, relevant title for the dashboard based on the query (e.g. "Sales Overview").
    2. "charts": Array of visuals.
    
    Each chart must follow this schema:
    {{
      "title": "Title",
      "visual_type": "table | bar | column | line | pie | card",
      "concepts": ["concept1", "concept2"],
      "top_n": null
    }}
    
    CRITICAL: If user asks for "N KPIs" or "N metrics", create ONE card with N measure concepts, NOT N separate cards.
    """

    response = client.chat.completions.create(
        model=DASHBOARD_MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    
    # Track usage
    tracker.track(response.usage)
    
    
    try:
        raw_data = json.loads(response.choices[0].message.content)
        
        # DEBUG: Print raw LLM response
        print("\n[VISUAL PLANNER DEBUG] Raw LLM Response:")
        print(json.dumps(raw_data, indent=2))
        
        title = raw_data.get("dashboard_title", "Dashboard")
        # Parse into Pydantic models for strict validation
        intents = [VisualIntent(**chart) for chart in raw_data.get("charts", [])]
        
        # DEBUG: Print parsed intents
        print(f"\n[VISUAL PLANNER DEBUG] Parsed {len(intents)} visual intents:")
        for i, intent in enumerate(intents, 1):
            print(f"  {i}. {intent.visual_type.upper()}: {intent.title} | concepts={intent.concepts} | top_n={intent.top_n}")
        print("[VISUAL PLANNER DEBUG END]\n")
        
        return intents, title
    except Exception as e:
        print(f"[PLANNER ERROR] Failed to parse LLM response: {e}")
        print(f"[PLANNER ERROR] Raw response: {response.choices[0].message.content}")
        return [], "Dashboard"