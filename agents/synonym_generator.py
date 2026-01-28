import json
from typing import List, Optional
from llm.clients import synonym_client
from config.settings import PLANNER_MODEL
from llm.token_tracker import tracker

def agent_generate_synonyms(
    field_name: str,
    is_measure: bool,
    data_type: Optional[str] = None,
    business_context: Optional[str] = None
) -> List[str]:
    """
    Agent 3: Synonym Generator
    Uses LLM to generate contextually relevant synonyms for a field.
    
    Args:
        field_name: Name of the field/column (e.g., "sales", "product_name")
        is_measure: True if numeric measure, False if dimension
        data_type: Optional TMDL data type (e.g., "int64", "string")
        business_context: Optional domain context (e.g., "retail analytics")
    
    Returns:
        List of synonym terms including the original field name variants
    """
    
    # Fallback to basic expansion if LLM fails
    def _fallback_expansion(name: str) -> List[str]:
        clean = name.lower()
        variants = {
            clean,
            clean.replace("_", " "),
            clean.replace("-", " ")
        }
        return sorted(variants)
    
    try:
        client = synonym_client()
        
        # Construct context-aware prompt
        field_type = "numeric measure" if is_measure else "categorical dimension"
        context_info = f"\nDomain Context: {business_context}" if business_context else ""
        data_type_info = f"\nData Type: {data_type}" if data_type else ""
        
        # Different prompts for measures vs dimensions to prevent numeric leakage
        if is_measure:
            prompt = f"""You are a data semantics expert specializing in business intelligence.

Generate relevant synonyms for a {field_type} field named: "{field_name}"{data_type_info}{context_info}

CRITICAL RULES FOR MEASURES:
1. Only include synonyms that represent QUANTITATIVE/NUMERIC concepts
2. Include business terms users might use when asking about this metric
3. Include aggregation terms (e.g., "total", "sum", "count", "amount")
4. DO NOT include non-numeric or categorical terms
5. Keep synonyms concise (1-3 words each)
6. Include 3-8 high-quality synonyms (quality over quantity)

Examples:
- "sales" → ["sales", "revenue", "turnover", "income", "total sales"]
- "unit_cost" → ["unit cost", "cost per unit", "item cost", "unit price"]
- "order_count" → ["order count", "number of orders", "total orders", "order quantity"]

Return ONLY a JSON object with this structure:
{{
  "synonyms": ["synonym1", "synonym2", ...]
}}"""
        else:
            prompt = f"""You are a data semantics expert specializing in business intelligence.

Generate relevant synonyms for a {field_type} field named: "{field_name}"{data_type_info}{context_info}

CRITICAL RULES FOR DIMENSIONS:
1. Only include synonyms that represent CATEGORICAL/DESCRIPTIVE concepts
2. Include natural language terms users might use to refer to this attribute
3. DO NOT include numeric, quantitative, or aggregation terms
4. Keep synonyms concise (1-3 words each)
5. Include 2-6 high-quality synonyms (quality over quantity)

Examples:
- "product_name" → ["product", "item", "product name", "sku"]
- "country" → ["country", "nation", "region", "market", "geography"]
- "order_date" → ["order date", "date", "order time", "purchase date"]

Return ONLY a JSON object with this structure:
{{
  "synonyms": ["synonym1", "synonym2", ...]
}}"""

        # Call LLM
        response = client.chat.completions.create(
            model=PLANNER_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3,  # Lower temperature for more consistent results
            max_tokens=500
        )
        
        # Track usage
        tracker.track(response.usage)
        
        # Parse response
        result = json.loads(response.choices[0].message.content)
        synonyms = result.get("synonyms", [])
        
        # Validation
        if not synonyms or not isinstance(synonyms, list):
            print(f"[SYNONYM AGENT WARNING] Invalid response for '{field_name}', using fallback")
            return _fallback_expansion(field_name)
        
        # Convert to lowercase and deduplicate
        synonyms = [s.lower().strip() for s in synonyms if s and isinstance(s, str)]
        synonyms = list(dict.fromkeys(synonyms))  # Preserve order while deduplicating
        
        # Always include basic variants of the original field name
        basic_variants = _fallback_expansion(field_name)
        all_synonyms = list(dict.fromkeys(synonyms + basic_variants))
        
        # Quality check: ensure minimum synonyms
        if len(all_synonyms) < 2:
            print(f"[SYNONYM AGENT WARNING] Too few synonyms for '{field_name}', using fallback")
            return _fallback_expansion(field_name)
        
        print(f"[SYNONYM AGENT] Generated {len(all_synonyms)} synonyms for '{field_name}' ({field_type})")
        return sorted(all_synonyms)
        
    except Exception as e:
        print(f"[SYNONYM AGENT ERROR] Failed to generate synonyms for '{field_name}': {e}")
        print(f"[SYNONYM AGENT] Using fallback expansion")
        return _fallback_expansion(field_name)


def batch_generate_synonyms(fields: List[dict], business_context: Optional[str] = None) -> dict:
    """
    Generate synonyms for multiple fields at once.
    
    Args:
        fields: List of dicts with keys: 'name', 'is_measure', 'data_type'
        business_context: Optional domain context for all fields
    
    Returns:
        Dictionary mapping field names to their synonym lists
    """
    results = {}
    
    for field in fields:
        field_name = field.get("name")
        is_measure = field.get("is_measure", False)
        data_type = field.get("data_type")
        
        if not field_name:
            continue
        
        synonyms = agent_generate_synonyms(
            field_name=field_name,
            is_measure=is_measure,
            data_type=data_type,
            business_context=business_context
        )
        
        results[field_name] = synonyms
    
    return results
