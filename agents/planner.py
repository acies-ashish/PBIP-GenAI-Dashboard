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

    prompt = f"""
    You are a Power BI Architect. 
    Analyze the user query and plan the visuals using ONLY the provided concepts.
    
    User Query: "{user_query}"
    Available Concepts: {available_concepts}
    
    Return a JSON object with a "charts" array.
    Each chart must follow this schema:
    {{
      "title": "Title",
      "visual_type": "table | bar | column",
      "concepts": ["concept1", "concept2"],
      "top_n": null
    }}
    """

    response = client.chat.completions.create(
        model=DASHBOARD_MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    
    raw_data = json.loads(response.choices[0].message.content)
    # Parse into Pydantic models for strict validation
    return [VisualIntent(**chart) for chart in raw_data.get("charts", [])]