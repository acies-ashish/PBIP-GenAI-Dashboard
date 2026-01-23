from typing import List
from core.models import VisualIntent, BoundVisual, PhysicalBinding
from semantic.semantic_resolver import resolve_concept

class VisualBinder:
    """
    Step 5: The Leak-Proof Wall.
    Converts Abstract Concepts into Physical Bindings using Linguistic Metadata.
    """
    def __init__(self, linguistic_metadata: dict):
        self.linguistic = linguistic_metadata

    def bind(self, intent: VisualIntent) -> BoundVisual:
        """
        Translates Abstract Intent into a Physical Bound Visual.
        Uses the semantic resolver to map concept names to table/column entities.
        """
        physical_bindings = []
        
        for concept in intent.concepts:
            # Step 3/5: Semantic Resolution
            # This calls the fuzzy matcher to find the actual TMDL column/table
            res = resolve_concept(concept, self.linguistic)
            
            # Map resolved metadata to our Physical IR (Intermediate Representation)
            # This ensures the backend (pbip_writer) has all necessary schema info
binding = PhysicalBinding(
    concept_name=concept,
    table=res["entity"],
    column=res["column"],
    kind="measure" if res.get("measure") else "dimension",
    data_type=res.get("dataType"),
    aggregation="sum" if res.get("measure") else None
)

print(
    f"[BINDER] Concept='{concept}' → "
    f"Table='{binding.table}', "
    f"Column='{binding.column}', "
    f"Type='{binding.kind}', "
    f"DataType='{binding.data_type}'"
)

            physical_bindings.append(binding)

        # Return a fully validated BoundVisual model
        return BoundVisual(
            visual_name=intent.title.lower().replace(" ", "_"),
            visual_type=intent.visual_type,
            bindings=physical_bindings,
            title=intent.title,
            top_n=intent.top_n
        )