from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.word import Word, WordTag
from app.services.vocabulary.levels import ALL_EXAM_LEVELS, is_exam_tag, levels_from_word_field


def ensure_exam_tag(db: Session, word_id: int, tag: str) -> bool:
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
    """Ensure WordTag exam labels match word.level (CET primary levels)."""
    added = 0
    for tag in levels_from_word_field(word.level):
        if ensure_exam_tag(db, word.id, tag):
            added += 1
    return added


def sync_all_exam_tags(db: Session) -> int:
    total = 0
    for word in db.query(Word).all():
        total += sync_exam_tags_for_word(db, word)
    if total:
        db.commit()
    return total


def count_words_for_exam_level(db: Session, exam_level: str) -> int:
    from app.services.vocabulary.levels import exam_level_filter

    return db.query(Word).filter(exam_level_filter(db, exam_level)).count()
