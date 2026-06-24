from __future__ import annotations

from app.database import SessionLocal
from app.models.progress import UserWordProgress
from app.models.scenario import Scenario, ScenarioWord
from app.models.user import User
from app.models.word import Word, WordTag
from app.services.scenario.word_picker import pick_words
from app.services.vocabulary.import_words import sync_word_groups
from app.services.vocabulary.theme_tags import sync_all_theme_tags


def _create_user(db) -> User:
    user = User(username="picker-user", email="picker@example.com", hashed_password="x")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_pick_words_uses_full_level_pool_with_theme_soft_bias():
    db = SessionLocal()
    try:
        sync_word_groups(db)
        sync_all_theme_tags(db)
        user = _create_user(db)

        business_ids = {row[0] for row in db.query(WordTag.word_id).filter(WordTag.tag == "business").all()}
        assert business_ids

        picked = pick_words(
            db,
            level="cet4",
            theme="business",
            word_ids=[],
            word_count=10,
            user_id=user.id,
            word_strategy="smart",
            exclude_recent=False,
        )
        picked_ids = {word.id for word in picked}
        assert len(picked) == 10
        assert len(picked_ids - business_ids) > 0
    finally:
        db.close()


def test_pick_words_excludes_recent_scenario_words():
    db = SessionLocal()
    try:
        sync_word_groups(db)
        sync_all_theme_tags(db)
        user = _create_user(db)
        first = pick_words(
            db,
            level="cet4",
            theme=None,
            word_ids=[],
            word_count=8,
            user_id=user.id,
            word_strategy="smart",
            exclude_recent=False,
        )
        scenario = Scenario(
            title="Recent",
            theme="daily",
            level="cet4",
            scenario_type="narrative",
            content="{}",
            dialogue="[]",
            user_id=user.id,
        )
        db.add(scenario)
        db.flush()
        for word in first:
            db.add(ScenarioWord(scenario_id=scenario.id, word_id=word.id))
        db.commit()

        second = pick_words(
            db,
            level="cet4",
            theme=None,
            word_ids=[],
            word_count=8,
            user_id=user.id,
            word_strategy="smart",
            exclude_recent=True,
        )
        overlap = {word.id for word in second} & {word.id for word in first}
        assert len(overlap) < len(first)
    finally:
        db.close()


def test_pick_words_new_strategy_prefers_unseen_words():
    db = SessionLocal()
    try:
        sync_word_groups(db)
        sync_all_theme_tags(db)
        user = _create_user(db)
        seen_word = db.query(Word).filter(Word.level.in_(["cet4", "both"])).first()
        db.add(UserWordProgress(user_id=user.id, word_id=seen_word.id, familiarity=3))
        db.commit()

        picked = pick_words(
            db,
            level="cet4",
            theme=None,
            word_ids=[],
            word_count=10,
            user_id=user.id,
            word_strategy="new",
            exclude_recent=False,
        )
        assert all(word.id != seen_word.id for word in picked)
    finally:
        db.close()
