from __future__ import annotations

from app.config import get_settings
from app.database import SessionLocal, reset_engine_for_tests
from app.models.dictionary import DictionaryEntry
from app.services.vocabulary.definition_lookup import clear_lookup_cache, lookup_definition


def test_lookup_definition_from_postgresql():
    get_settings.cache_clear()
    reset_engine_for_tests()
    clear_lookup_cache()

    db = SessionLocal()
    try:
        db.merge(
            DictionaryEntry(
                lemma="testlemma",
                definition="测试释义",
                pos="n.",
                source="override",
            )
        )
        db.commit()
    finally:
        db.close()

    clear_lookup_cache()
    definition, pos = lookup_definition("testlemma")
    assert definition == "测试释义"
    assert pos == "n."
