from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.word import Word, WordTag
from app.services.vocabulary.levels import ALL_EXAM_LEVELS, is_exam_tag, levels_from_word_field


def apply_exam_tag(db: Session, word_id: int, tag: str) -> bool:
    if not is_exam_tag(tag):
        return False
    exists = (
        db.query(WordTag)
        .filter(WordTag.word_id == word_id, WordTag.tag == tag)
        .first()
    )
    if exists:
        return False
    db.add(WordTag(word_id=word_id, tag=tag))
    return True


def sync_exam_tags_for_word(db: Session, word: Word) -> int:
    """Apply WordTag exam labels to match word.level (CET primary levels)."""
    added = 0
    for tag in levels_from_word_field(word.level):
        if apply_exam_tag(db, word.id, tag):
            added += 1
    return added


def sync_all_exam_tags(db: Session) -> int:
    words = db.query(Word).all()
    if not words:
        return 0

    word_ids = [word.id for word in words]
    existing = {
        (row[0], row[1])
        for row in db.query(WordTag.word_id, WordTag.tag)
        .filter(WordTag.word_id.in_(word_ids), WordTag.tag.in_(ALL_EXAM_LEVELS))
        .all()
    }

    added = 0
    for word in words:
        for tag in levels_from_word_field(word.level):
            if not is_exam_tag(tag):
                continue
            key = (word.id, tag)
            if key in existing:
                continue
            db.add(WordTag(word_id=word.id, tag=tag))
            existing.add(key)
            added += 1
    if added:
        db.commit()
    return added


def count_words_for_exam_level(db: Session, exam_level: str) -> int:
    from app.services.vocabulary.levels import exam_level_filter

    return db.query(Word).filter(exam_level_filter(db, exam_level)).count()
