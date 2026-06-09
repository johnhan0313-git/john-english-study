from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.conversation import ConversationSession
from app.models.progress import LearningStreak, ScenarioAttempt, UserWordProgress
from app.models.scenario import Scenario
from app.models.user import User


def _merge_word_progress(db: Session, user_id: int, device_id: str) -> int:
    merged = 0
    legacy_rows = (
        db.query(UserWordProgress)
        .filter(UserWordProgress.device_id == device_id, UserWordProgress.user_id.is_(None))
        .all()
    )
    for row in legacy_rows:
        existing = (
            db.query(UserWordProgress)
            .filter(UserWordProgress.user_id == user_id, UserWordProgress.word_id == row.word_id)
            .first()
        )
        if existing:
            if row.familiarity > existing.familiarity:
                existing.familiarity = row.familiarity
                existing.correct_count = max(existing.correct_count, row.correct_count)
                existing.wrong_count = max(existing.wrong_count, row.wrong_count)
                if row.next_review:
                    existing.next_review = row.next_review
                if row.last_reviewed:
                    existing.last_reviewed = row.last_reviewed
            db.delete(row)
        else:
            row.user_id = user_id
            row.device_id = None
            merged += 1
    db.flush()
    return merged


def _reassign_rows(db: Session, model, user_id: int, device_id: str) -> int:
    rows = (
        db.query(model)
        .filter(model.device_id == device_id, model.user_id.is_(None))
        .all()
    )
    for row in rows:
        row.user_id = user_id
        row.device_id = None
    db.flush()
    return len(rows)


def _merge_streak(db: Session, user_id: int, device_id: str) -> int:
    legacy = db.query(LearningStreak).filter(LearningStreak.device_id == device_id).first()
    if not legacy:
        return 0
    existing = db.query(LearningStreak).filter(LearningStreak.user_id == user_id).first()
    if existing:
        existing.current_streak = max(existing.current_streak, legacy.current_streak)
        existing.longest_streak = max(existing.longest_streak, legacy.longest_streak)
        if legacy.last_active_date and (
            not existing.last_active_date or legacy.last_active_date > existing.last_active_date
        ):
            existing.last_active_date = legacy.last_active_date
        db.delete(legacy)
    else:
        legacy.user_id = user_id
        legacy.device_id = None
    return 1


def merge_device_to_user(db: Session, user: User, device_id: str) -> dict:
    if not device_id or device_id == "default":
        return {"word_progress": 0, "scenarios": 0, "attempts": 0, "conversations": 0, "streak": 0}

    result = {
        "word_progress": _merge_word_progress(db, user.id, device_id),
        "scenarios": _reassign_rows(db, Scenario, user.id, device_id),
        "attempts": _reassign_rows(db, ScenarioAttempt, user.id, device_id),
        "conversations": _reassign_rows(db, ConversationSession, user.id, device_id),
        "streak": _merge_streak(db, user.id, device_id),
    }
    user.legacy_device_id = device_id
    db.commit()
    return result
