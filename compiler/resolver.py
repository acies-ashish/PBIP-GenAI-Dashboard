# compiler/resolver.py
import re
from difflib import SequenceMatcher

class SemanticResolutionError(Exception):
    pass

def resolve_concept(concept: str, linguistic_metadata: dict) -> dict:
    """
    Resolves a semantic concept (e.g. 'region', 'sales') into a concrete 
    schema binding using linguistic metadata.
    """
    if not concept:
        return {}

    # Normalize input
    concept_norm = re.sub(r"[^a-z0-9]", "", concept.lower())
    
    # Handle qualified concepts (e.g. "data.product" -> "product")
    if "." in concept_norm:
        concept_norm = concept_norm.split(".")[-1]

    best_match = None
    best_score = 0.0

    entities = linguistic_metadata.get("entities", {})

    for entity_id, entity in entities.items():
        binding = entity.get("binding", {})
        terms = entity.get("terms", [])

        for term in terms:
            # Handle both string terms and dict terms (with weights)
            term_text = term.get("term") if isinstance(term, dict) else term
            weight = term.get("weight", 1.0) if isinstance(term, dict) else 1.0
            
            if not term_text: continue

            term_norm = re.sub(r"[^a-z0-9]", "", term_text.lower())
            
            # Calculate Similarity
            score = SequenceMatcher(None, concept_norm, term_norm).ratio()

            # Boost for exact substring matches
            if concept_norm in term_norm or term_norm in concept_norm:
                score += 0.25

            final_score = score * weight

            if final_score > best_score:
                best_score = final_score
                best_match = {
                    "entity": binding.get("table"),
                    "column": binding.get("column"),
                    "measure": binding.get("measure", False),
                    "dataType": binding.get("dataType"),
                    "score": round(final_score, 3)
                }

    # Hard Threshold to prevent hallucinations
    if not best_match or best_score < 0.45:
        # Fallback: Check if it's a known generic term like "count" or "total"
        # and ignore it, or raise error.
        print(f"[RESOLVER WARNING] Low confidence for '{concept}' (Score: {best_score})")
        # For now, we return the best guess but you might want to raise SemanticResolutionError
        if best_match: return best_match
        raise SemanticResolutionError(f"Unresolvable concept: '{concept}'")

    return best_match