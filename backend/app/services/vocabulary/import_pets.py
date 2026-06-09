from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.word import Word, WordTag
from app.services.vocabulary.definition_lookup import enrich_definitions
from app.services.vocabulary.definitions import normalize_definitions
from app.services.vocabulary.exam_tags import count_words_for_exam_level
from app.services.vocabulary.levels import PETS_INHERIT_FROM_CET, PETS_LEVELS
from app.utils.json_helpers import dump_json_field, parse_json_field

DATA_DIR = Path(__file__).resolve().parents[3] / "data"
PETS_DATA_FILE = DATA_DIR / "pets_words.json"


def _load_pets_data() -> dict:
    if not PETS_DATA_FILE.exists():
        return {"inherit_from_cet": PETS_INHERIT_FROM_CET, "levels": {}}
    return json.loads(PETS_DATA_FILE.read_text(encoding="utf-8"))


def _ensure_tag(db: Session, word_id: int, tag: str) -> bool:
    exists = (
        db.query(WordTag)
        .filter(WordTag.word_id == word_id, WordTag.tag == tag)
        .first()
    )
    if exists:
        return False
    db.add(WordTag(word_id=word_id, tag=tag))
    return True


def _upsert_pets_word(db: Session, level: str, entry: dict | str) -> tuple[str, int | None]:
    if isinstance(entry, str):
        lemma = entry
        pos = "n."
        definitions: list[str] = []
    else:
        lemma = entry["lemma"]
        pos = entry.get("pos") or "n."
        definition = entry.get("definition") or entry.get("definitions", [""])[0]
        definitions = enrich_definitions(lemma, normalize_definitions(lemma, [definition] if definition else []))

    word = db.query(Word).filter(Word.lemma == lemma).first()
    if word:
        tagged = _ensure_tag(db, word.id, level)
        if definitions and not normalize_definitions(word.lemma, parse_json_field(word.definitions, [])):
            word.definitions = dump_json_field(definitions)
        return ("tagged" if tagged else "skipped", word.id)

    word = Word(
        lemma=lemma,
        phonetic=entry.get("phonetic") if isinstance(entry, dict) else None,
        level=level,
        pos=pos,
        definitions=dump_json_field(definitions),
        examples=dump_json_field([f"Example with {lemma}."]),
    )
    db.add(word)
    db.flush()
    _ensure_tag(db, word.id, level)
    return ("added", word.id)


def import_pets_words(db: Session) -> dict[str, int | bool]:
    data = _load_pets_data()
    stats: dict[str, int] = {
        "added": 0,
        "tagged": 0,
        "skipped": 0,
    }
    per_level: dict[str, int] = {level: count_words_for_exam_level(db, level) for level in PETS_LEVELS}

    for level in PETS_LEVELS:
        entries = data.get("levels", {}).get(level, [])
        for entry in entries:
            action, _word_id = _upsert_pets_word(db, level, entry)
            if action == "added":
                stats["added"] += 1
            elif action == "tagged":
                stats["tagged"] += 1
            else:
                stats["skipped"] += 1

    inherit = data.get("inherit_from_cet", PETS_INHERIT_FROM_CET)
    for pets_level, cet_levels in inherit.items():
        if pets_level not in PETS_LEVELS:
            continue
        words = db.query(Word).filter(Word.level.in_(cet_levels)).all()
        for word in words:
            if _ensure_tag(db, word.id, pets_level):
                stats["tagged"] += 1

    db.commit()
    per_level = {level: count_words_for_exam_level(db, level) for level in PETS_LEVELS}
    return {
        **stats,
        "per_level": per_level,
        "completed": True,
    }


def count_words_for_pets_level(db: Session, level: str) -> int:
    return count_words_for_exam_level(db, level)
