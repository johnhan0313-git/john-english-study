from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from sqlalchemy.orm import Session

from app.data_paths import get_data_dir
from app.models.word import Word
from app.services.vocabulary.definitions import normalize_definitions
from app.utils.json_helpers import dump_json_field, parse_json_field

def _dict_lookup_file() -> Path:
    return get_data_dir() / "dict_lookup.json"


def _overrides_file() -> Path:
    return get_data_dir() / "dict_lookup_overrides.json"

# 美式拼写 -> 英式（词库中更常见）
SPELLING_ALIASES: dict[str, str] = {
    "rumor": "rumour",
    "behavior": "behaviour",
    "color": "colour",
    "honor": "honour",
    "labor": "labour",
    "center": "centre",
    "theater": "theatre",
    "analyze": "analyse",
    "organize": "organise",
}


def _lemma_keys(lemma: str) -> list[str]:
    keys: list[str] = []
    for candidate in (lemma, lemma.lower(), lemma.replace("'", "'")):
        if candidate and candidate not in keys:
            keys.append(candidate)
    alias = SPELLING_ALIASES.get(lemma.lower())
    if alias and alias not in keys:
        keys.append(alias)
    return keys


def _fallback_lemma_keys(lemma: str) -> list[str]:
    """Try base forms when inflected spellings are absent from the lookup table."""
    lower = lemma.lower()
    keys: list[str] = []

    if lower.endswith("ies") and len(lower) > 4:
        keys.append(lower[:-3] + "y")
    if lower.endswith("ied") and len(lower) > 4:
        keys.append(lower[:-3] + "y")
    if lower.endswith("es") and len(lower) > 3:
        keys.append(lower[:-2])
        keys.append(lower[:-1])
    if lower.endswith("s") and len(lower) > 2 and not lower.endswith("ss"):
        keys.append(lower[:-1])
    if lower.endswith("ed") and len(lower) > 3:
        stem = lower[:-2]
        keys.extend([stem, stem + "e", lower[:-1]])
    if lower.endswith("ing") and len(lower) > 4:
        stem = lower[:-3]
        keys.extend([stem, stem + "e"])
        if len(stem) > 2 and stem[-1] == stem[-2]:
            keys.append(stem[:-1])
            keys.append(stem[:-1] + "e")

    deduped: list[str] = []
    for key in keys:
        if key and key not in deduped:
            deduped.append(key)
    return deduped


def clear_lookup_cache() -> None:
    _load_lookup.cache_clear()


@lru_cache(maxsize=1)
def _load_lookup() -> dict[str, dict]:
    merged: dict[str, dict] = {}
    if _dict_lookup_file().exists():
        data = json.loads(_dict_lookup_file().read_text(encoding="utf-8"))
        merged.update(data.get("entries", {}))
    if _overrides_file().exists():
        data = json.loads(_overrides_file().read_text(encoding="utf-8"))
        merged.update(data.get("entries", {}))
    return merged


def lookup_definition(lemma: str) -> tuple[str | None, str | None]:
    """Return (definition, pos_hint) from bundled dictionary."""
    entries = _load_lookup()
    search_keys = _lemma_keys(lemma) + _fallback_lemma_keys(lemma)
    for key in search_keys:
        hit = entries.get(key) or entries.get(key.lower())
        if hit:
            definition = hit.get("definition") or hit.get("translation")
            pos = hit.get("pos")
            if definition:
                text = str(definition).strip()
                if key != lemma.lower() and key in _fallback_lemma_keys(lemma):
                    return f"（{lemma}）{text}", pos
                return text, pos
    return None, None


def enrich_definitions(lemma: str, definitions: list[str] | None) -> list[str]:
    existing = normalize_definitions(lemma, definitions)
    if existing:
        return existing
    found, _ = lookup_definition(lemma)
    if found:
        return normalize_definitions(lemma, [found])
    return []


def fill_missing_definitions(db: Session) -> int:
    updated = 0
    for word in db.query(Word).all():
        current = normalize_definitions(word.lemma, parse_json_field(word.definitions, []))
        if current:
            continue
        enriched = enrich_definitions(word.lemma, current)
        if not enriched:
            continue
        word.definitions = dump_json_field(enriched)
        found, pos_hint = lookup_definition(word.lemma)
        if pos_hint and not word.pos:
            word.pos = pos_hint
        updated += 1
    if updated:
        db.commit()
    return updated
