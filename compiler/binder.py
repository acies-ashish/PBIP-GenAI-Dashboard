# compiler/binder.py

from typing import List
from core.models import VisualIntent, BoundVisual, PhysicalBinding
from compiler.resolver import resolve_concept


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

        physical_bindings: List[PhysicalBinding] = []

        print(f"\n[BINDER] Binding visual: '{intent.title}'")

        for concept in intent.concepts:
            # --------------------------------------------
            # Step 5.1: Semantic Resolution
            # --------------------------------------------
            res = resolve_concept(concept, self.linguistic)

            # --------------------------------------------
            # Step 5.2: Create Physical Binding
            # --------------------------------------------
            if not res.get("column"):
                print(f"[BINDER SKIP] Concept '{concept}' resolved to entity '{res.get('entity')}' with no column. Skipping.")
                continue

            binding = PhysicalBinding(
                concept_name=concept,
                table=res["entity"],
                column=res["column"],
                kind="measure" if res.get("measure") else "dimension",
                data_type=res.get("dataType"),
                aggregation="sum" if res.get("measure") else None
            )

            # --------------------------------------------
            # Step 5.3: HARD INVARIANTS
            # --------------------------------------------
            if binding.kind == "measure" and not binding.aggregation:
                raise RuntimeError(
                    f"[BINDER ERROR] Measure '{binding.column}' has no aggregation"
                )

            if binding.kind == "dimension" and binding.aggregation is not None:
                raise RuntimeError(
                    f"[BINDER ERROR] Dimension '{binding.column}' has aggregation"
                )

            # --------------------------------------------
            # Step 5.4: Canonical Debug Output
            # --------------------------------------------
            print("[BINDER OUTPUT]", binding.model_dump())

            physical_bindings.append(binding)

        # --------------------------------------------
        # Step 5.5: Return Bound Visual
        # --------------------------------------------
        return BoundVisual(
            visual_name=intent.title.lower().replace(" ", "_"),
            visual_type=intent.visual_type,
            bindings=physical_bindings,
            title=intent.title,
            top_n=intent.top_n
        )
