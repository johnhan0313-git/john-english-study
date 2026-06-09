from __future__ import annotations


def is_placeholder_definition(lemma: str, definition: str) -> bool:
    text = definition.strip()
    if not text:
        return True
    return text == lemma or text == f"{lemma} 释义"


def normalize_definitions(lemma: str, definitions: list | None) -> list[str]:
    if not definitions:
        return []
    return [
        d.strip()
        for d in definitions
        if isinstance(d, str) and d.strip() and not is_placeholder_definition(lemma, d.strip())
    ]
