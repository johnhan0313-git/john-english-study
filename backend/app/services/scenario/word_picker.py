from __future__ import annotations

import random
from typing import Literal

from sqlalchemy.orm import Session

from app.models.progress import UserWordProgress
from app.models.scenario import Scenario, ScenarioWord
from app.models.word import Word, WordTag
from app.services.vocabulary.srs import get_due_word_ids

WordStrategy = Literal["smart", "new", "review"]

THEME_SOFT_RATIO = 0.7
RECENT_SCENARIO_LIMIT = 5


def _level_filter(query, level: str):
    if level == "cet4":
        return query.filter(Word.level.in_(["cet4", "both"]))
    if level == "cet6":
        return query.filter(Word.level.in_(["cet6", "both"]))
    return query


def _theme_word_ids(db: Session, theme: str | None) -> set[int]:
    if not theme:
        return set()
    rows = db.query(WordTag.word_id).filter(WordTag.tag == theme).all()
    return {row[0] for row in rows}


def _recent_scenario_word_ids(db: Session, user_id: int, limit: int = RECENT_SCENARIO_LIMIT) -> set[int]:
    scenario_ids = [
        row[0]
        for row in (
            db.query(Scenario.id)
            .filter(Scenario.user_id == user_id)
            .order_by(Scenario.created_at.desc())
            .limit(limit)
            .all()
        )
    ]
    if not scenario_ids:
        return set()
    rows = db.query(ScenarioWord.word_id).filter(ScenarioWord.scenario_id.in_(scenario_ids)).all()
    return {row[0] for row in rows}


def _progress_maps(db: Session, user_id: int, word_ids: list[int]) -> tuple[set[int], set[int]]:
    if not word_ids:
        return set(), set()
    rows = (
        db.query(UserWordProgress.word_id, UserWordProgress.familiarity)
        .filter(UserWordProgress.user_id == user_id, UserWordProgress.word_id.in_(word_ids))
        .all()
    )
    seen = {row[0] for row in rows}
    new_ids = {row[0] for row in rows if row[1] == 0}
    return seen, new_ids


def _sample_words(pool: list[Word], count: int, picked_ids: set[int]) -> list[Word]:
    available = [word for word in pool if word.id not in picked_ids]
    if not available or count <= 0:
        return []
    chosen = random.sample(available, min(count, len(available)))
    return chosen


def _pick_with_buckets(
    candidates: list[Word],
    word_count: int,
    buckets: list[list[Word]],
) -> list[Word]:
    picked: list[Word] = []
    picked_ids: set[int] = set()

    for bucket in buckets:
        if len(picked) >= word_count:
            break
        for word in _sample_words(bucket, word_count - len(picked), picked_ids):
            picked.append(word)
            picked_ids.add(word.id)

    if len(picked) < word_count:
        for word in _sample_words(candidates, word_count - len(picked), picked_ids):
            picked.append(word)
            picked_ids.add(word.id)

    return picked


def pick_words(
    db: Session,
    *,
    level: str,
    theme: str | None,
    word_ids: list[int],
    word_count: int,
    user_id: int,
    word_strategy: WordStrategy = "smart",
    exclude_recent: bool = True,
) -> list[Word]:
    if word_ids:
        words = db.query(Word).filter(Word.id.in_(word_ids)).all()
        if words:
            return words[:word_count]

    level_words = _level_filter(db.query(Word), level).all()
    if not level_words:
        return []

    theme_ids = _theme_word_ids(db, theme)
    recent_ids = _recent_scenario_word_ids(db, user_id) if exclude_recent else set()
    candidates = [word for word in level_words if word.id not in recent_ids]
    if len(candidates) < word_count:
        candidates = level_words

    candidate_ids = [word.id for word in candidates]
    progress_seen, new_ids = _progress_maps(db, user_id, candidate_ids)
    due_ids = set(get_due_word_ids(db, user_id, word_count * 3))

    new_words = [word for word in candidates if word.id not in progress_seen or word.id in new_ids]
    review_words = [word for word in candidates if word.id in due_ids]
    theme_words = [word for word in candidates if word.id in theme_ids]

    if word_strategy == "review":
        return _pick_with_buckets(candidates, word_count, [review_words, new_words, theme_words])

    if word_strategy == "new":
        return _pick_with_buckets(candidates, word_count, [new_words, theme_words, review_words])

    theme_quota = round(word_count * THEME_SOFT_RATIO) if theme and theme_ids else 0
    remainder = max(word_count - theme_quota, 0)
    new_quota = round(remainder * 0.6)
    review_quota = max(remainder - new_quota, 0)

    theme_new = [word for word in theme_words if word.id not in progress_seen or word.id in new_ids]
    theme_review = [word for word in theme_words if word.id in due_ids]
    theme_new_ids = {word.id for word in theme_new}
    theme_review_ids = {word.id for word in theme_review}
    theme_other = [
        word for word in theme_words if word.id not in theme_new_ids and word.id not in theme_review_ids
    ]

    picked: list[Word] = []
    picked_ids: set[int] = set()

    for word in _sample_words(theme_new, min(new_quota, theme_quota), picked_ids):
        picked.append(word)
        picked_ids.add(word.id)
    theme_slots_left = max(theme_quota - len(picked), 0)
    for word in _sample_words(theme_review, min(review_quota, theme_slots_left), picked_ids):
        picked.append(word)
        picked_ids.add(word.id)
    theme_slots_left = max(theme_quota - len(picked), 0)
    for word in _sample_words(theme_other, theme_slots_left, picked_ids):
        picked.append(word)
        picked_ids.add(word.id)

    if len(picked) < word_count:
        extra = _pick_with_buckets(
            candidates,
            word_count - len(picked),
            [new_words, review_words, theme_words],
        )
        for word in extra:
            if word.id not in picked_ids:
                picked.append(word)
                picked_ids.add(word.id)

    return picked[:word_count]
