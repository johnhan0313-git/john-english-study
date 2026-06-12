from __future__ import annotations

import string

from sqlalchemy import func
from sqlalchemy.orm import Query, Session

from app.models.word import Word, WordTag
from app.services.vocabulary.levels import ALL_EXAM_LEVELS, exam_level_filter


def words_base_query(
    db: Session,
    *,
    level: str | None = None,
    theme: str | None = None,
    search: str | None = None,
) -> Query:
    query = db.query(Word)
    if level:
        if level in ALL_EXAM_LEVELS:
            query = query.filter(exam_level_filter(db, level))
        else:
            query = query.filter(Word.level == level)
    if search:
        query = query.filter(Word.lemma.ilike(f"%{search}%"))
    if theme:
        query = query.join(WordTag, WordTag.word_id == Word.id).filter(WordTag.tag == theme)
    return query


def apply_letter_filter(query: Query, letter: str | None) -> Query:
    if not letter:
        return query
    if letter == "#":
        first_char = func.lower(func.substr(Word.lemma, 1, 1))
        return query.filter(~first_char.in_(list(string.ascii_lowercase)))
    if len(letter) == 1 and letter.isalpha():
        return query.filter(Word.lemma.ilike(f"{letter}%"))
    return query


def index_letter(lemma: str) -> str:
    ch = lemma.strip()[:1].upper()
    return ch if ch.isalpha() else "#"


def collect_index_letters(lemmas: list[str]) -> list[str]:
    letters = {index_letter(lemma) for lemma in lemmas if lemma and lemma.strip()}
    return sorted(letters, key=lambda value: (value == "#", value))
