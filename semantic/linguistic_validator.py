# semantic/linguistic_validator.py

class LinguisticValidationError(Exception):
    pass


def validate_linguistic_metadata(linguistic: dict, semantic_index: dict):
    if "entities" not in linguistic:
        raise LinguisticValidationError("Missing entities section")

    for entity_id, entity in linguistic["entities"].items():
        kind = entity.get("kind")
        binding = entity.get("binding")

        if kind == "table":
            if not binding or "table" not in binding:
                raise LinguisticValidationError(
                    f"{entity_id} table entity missing binding"
                )
            continue

        if kind == "column":
            if not binding:
                raise LinguisticValidationError(
                    f"{entity_id} column missing binding"
                )

            if "table" not in binding or "column" not in binding:
                raise LinguisticValidationError(
                    f"{entity_id} column binding incomplete"
                )

        if not entity.get("terms"):
            raise LinguisticValidationError(
                f"{entity_id} has no linguistic terms"
            )
