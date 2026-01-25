import json
from typing import List
from llm.clients import planner_client
from config.settings import DASHBOARD_MODEL
from core.models import VisualIntent

def agent_plan_visuals(user_query: str, available_concepts: List[str]) -> List[VisualIntent]:
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
    
    ### VISUAL SELECTION RULES:
    1. **Single Value / KPI**: If the user asks for a single aggregate (e.g., "total sales", "count of orders"), use "card".
    2. **Comparison**: If comparing a measure across categories (e.g., "sales by region"), use "bar" or "column".
    3. **Trend**: If analyzing over time (e.g., "sales over time", "monthly revenue"), use "line".
    4. **Distribution**: If asking for parts of a whole (e.g., "sales share by category"), use "pie".
    5. **Detailed List**: If asking for raw data or multiple columns without aggregation (e.g., "list products and prices"), use "table".
    6. **Top N**: If a ranking is implied (e.g., "top 5 products"), use "bar" and set "top_n".

    Return a JSON object with a "charts" array.
    Each chart must follow this schema:
    {{
      "title": "Title",
      "visual_type": "table | bar | column | line | pie | card",
      "concepts": ["concept1", "concept2"],
      "top_n": null
    }}
    """

    response = client.chat.completions.create(
        model=DASHBOARD_MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    
    try:
        raw_data = json.loads(response.choices[0].message.content)
        # Parse into Pydantic models for strict validation
        return [VisualIntent(**chart) for chart in raw_data.get("charts", [])]
    except Exception as e:
        print(f"[PLANNER ERROR] Failed to parse LLM response: {e}")
        return []