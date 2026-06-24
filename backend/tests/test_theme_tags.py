from __future__ import annotations

from app.services.vocabulary.theme_tags import infer_theme_tags, sync_all_theme_tags


def test_infer_theme_tags_from_lemma_and_definition():
    assert "travel" in infer_theme_tags("airport", ["机场"])
    assert "science" in infer_theme_tags("hypothesis", ["假设"])
    assert "psychology" in infer_theme_tags("anxiety", ["焦虑"])


def test_sync_all_theme_tags_expands_beyond_seed_words():
    from app.database import SessionLocal
    from app.models.word import WordTag
    from app.services.vocabulary.import_words import import_words

    db = SessionLocal()
    try:
        import_words(db)
        result = sync_all_theme_tags(db)
        assert result["words_tagged"] > 200
        assert result["per_theme"]["travel"] > 15
        assert result["per_theme"]["science"] > 15
        assert db.query(WordTag).filter(WordTag.tag == "business").count() > 15
    finally:
        db.close()
