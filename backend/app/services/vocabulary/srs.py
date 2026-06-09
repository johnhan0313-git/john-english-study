from __future__ import annotations

from datetime import timedelta

from sqlalchemy.orm import Session

from app.models.progress import UserWordProgress
from app.utils.time import utc_now

SRS_INTERVALS_DAYS = [1, 3, 7, 14, 30]


def get_or_create_progress(db: Session, device_id: str, word_id: int) -> UserWordProgress:
    progress = (
        db.query(UserWordProgress)
        .filter(UserWordProgress.device_id == device_id, UserWordProgress.word_id == word_id)
        .first()
    )
    if not progress:
        progress = UserWordProgress(device_id=device_id, word_id=word_id, familiarity=0)
        db.add(progress)
        db.flush()
    return progress


def record_answer(db: Session, device_id: str, word_id: int, correct: bool) -> UserWordProgress:
    progress = get_or_create_progress(db, device_id, word_id)
    now = utc_now()
    progress.last_reviewed = now

    if correct:
        progress.correct_count += 1
        progress.familiarity = min(5, progress.familiarity + 1)
        interval_idx = min(progress.familiarity - 1, len(SRS_INTERVALS_DAYS) - 1)
        if progress.familiarity > 0:
            progress.next_review = now + timedelta(days=SRS_INTERVALS_DAYS[interval_idx])
    else:
        progress.wrong_count += 1
        progress.familiarity = 0
        progress.next_review = now + timedelta(days=1)

    return progress


def get_due_word_ids(db: Session, device_id: str, limit: int = 12) -> list[int]:
    now = utc_now()
    rows = (
        db.query(UserWordProgress.word_id)
        .filter(
            UserWordProgress.device_id == device_id,
            UserWordProgress.next_review.isnot(None),
            UserWordProgress.next_review <= now,
        )
        .order_by(UserWordProgress.next_review)
        .limit(limit)
        .all()
    )
    return [r[0] for r in rows]
