# compiler/resolver.py
import re
from difflib import SequenceMatcher


class SemanticResolutionError(Exception):
    pass


# -------------------------------
# Semantic rules
# -------------------------------
NUMERIC_TYPES = {
    "int", "int32", "int64",
    "integer", "bigint",
    "decimal", "double", "float",
    "number"
}

NUMERIC_CONCEPTS = {
    "amount", "revenue", "sales", "value", "total", "cost", "price",
    "quantity", "qty", "count", "volume", "forecast", "demand" # NEW
}


def resolve_concept(concept: str, linguistic_metadata: dict) -> dict:
    """
    Resolves a semantic concept (e.g. 'amount', 'product')
    into a concrete schema binding using linguistic metadata.

    Enforces HARD semantic constraints:
    - Numeric concepts must map to numeric MEASURES
    """

    if not concept:
        raise SemanticResolutionError("Empty concept provided")

    # ----------------------------------
    # Normalize concept
    # ----------------------------------
    concept_norm = re.sub(r"[^a-z0-9]", "", concept.lower())
    if "." in concept_norm:
        concept_norm = concept_norm.split(".")[-1]

    print(f"\n[RESOLVER] Resolving concept: '{concept_norm}'")

    best_match = None
    best_score = 0.0

    entities = linguistic_metadata.get("entities", {})

    for entity_id, entity in entities.items():
        binding = entity.get("binding", {})
        terms = entity.get("terms", [])

        for term in terms:
            term_text = term.get("term") if isinstance(term, dict) else term
            weight = term.get("weight", 1.0) if isinstance(term, dict) else 1.0

            if not term_text:
                continue

            term_norm = re.sub(r"[^a-z0-9]", "", term_text.lower())

            # ----------------------------------
            # Linguistic similarity
            # ----------------------------------
            score = SequenceMatcher(None, concept_norm, term_norm).ratio()

            if concept_norm in term_norm or term_norm in concept_norm:
                score += 0.25

            final_score = score * weight

            is_measure = binding.get("measure", False)
            data_type = binding.get("dataType")

            print(
                f"[RESOLVER TRY] concept='{concept_norm}' "
                f"→ column='{binding.get('column')}' "
                f"(measure={is_measure}, dataType={data_type}) "
                f"score={round(final_score, 3)}"
            )

            # ----------------------------------
            # HARD semantic constraints
            # ----------------------------------
            if concept_norm in NUMERIC_CONCEPTS:
                if not is_measure:
                    print("  └─ REJECTED: numeric concept mapped to dimension")
                    continue
                if data_type not in NUMERIC_TYPES:
                    print("  └─ REJECTED: non-numeric datatype")
                    continue

            # ----------------------------------
            # Best match tracking
            # ----------------------------------
            if final_score > best_score:
                best_score = final_score
                best_match = {
                    "entity": binding.get("table"),
                    "column": binding.get("column"),
                    "measure": is_measure,
                    "dataType": data_type,
                    "score": round(final_score, 3)
                }

    # ----------------------------------
    # Final validation
    # ----------------------------------
    if not best_match or best_score < 0.45:
        raise SemanticResolutionError(
            f"Unresolvable or invalid concept: '{concept_norm}' (score={best_score})"
        )

    print(f"[RESOLVER ACCEPT] '{concept_norm}' → {best_match}")
    return best_match