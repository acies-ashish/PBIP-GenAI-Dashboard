# semantic/semantic_resolver.py

import re
from difflib import SequenceMatcher


class SemanticResolutionError(Exception):
    pass


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()

def resolve_concept(concept: str, linguistic: dict) -> dict:
    """
    Resolves a semantic concept using linguistic metadata.
    """

    if not concept:
        return None

    # ---- HANDLE QUALIFIED CONCEPTS ----
    # e.g. "data.product" → "product"
    if "." in concept:
        concept = concept.split(".")[-1]


def resolve_concept(concept: str, linguistic_metadata: dict) -> dict:
    """
    Resolves a semantic concept (e.g. 'region', 'product category', 'sales')
    into a concrete schema binding using linguistic metadata.

    Supports BOTH:
    - terms as strings
    - terms as {term, weight} objects
    """

    concept_norm = _normalize(concept)

    best_match = None
    best_score = 0.0

    entities = linguistic_metadata.get("entities", {})

    for entity_id, entity in entities.items():
        binding = entity.get("binding", {})
        terms = entity.get("terms", [])

        for term in terms:
            # ----------------------------
            # Normalize term format
            # ----------------------------
            if isinstance(term, str):
                term_text = term
                weight = 1.0
            elif isinstance(term, dict):
                term_text = term.get("term")
                weight = term.get("weight", 1.0)
            else:
                continue

            if not term_text:
                continue

            term_norm = _normalize(term_text)
            score = _similarity(concept_norm, term_norm)

            # Strong containment bias
            if concept_norm in term_norm or term_norm in concept_norm:
                score += 0.25

            score *= weight

            if score > best_score:
                best_score = score
                best_match = {
                    "entity": binding.get("table"),
                    "column": binding.get("column"),
                    "measure": binding.get("measure"),
                    "matched_term": term_text,
                    "score": round(score, 3)
                }

    # ----------------------------
    # Hard failure (no guessing)
    # ----------------------------
    if not best_match or best_score < 0.45:
        raise SemanticResolutionError(
            f"Unresolvable semantic concept: '{concept}'"
        )

    return best_match
