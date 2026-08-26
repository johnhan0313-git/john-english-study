from __future__ import annotations

"""Legacy SRS helpers used by conversation until Conversation Application owns Progress writes.

Prefer Progress Application RecordAnswerCommand for new call sites.
"""

from sqlalchemy.orm import Session

from app.domains.progress.progress_domain import WordProgressState, apply_answer
from app.infrastructure.persistence.progress.progress_repository_impl import SqlAlchemyProgressRepository
from app.models.progress import UserWordProgress
from app.utils.time import utc_now


def record_answer(db: Session, user_id: int, word_id: int, correct: bool) -> UserWordProgress:
    repo = SqlAlchemyProgressRepository(db)
    state = repo.get_word_progress(user_id, word_id)
    if state is None:
        state = WordProgressState(user_id=user_id, word_id=word_id)
        state = apply_answer(state, correct, utc_now())
        repo.add_word_progress(state)
    else:
        state = apply_answer(state, correct, utc_now())
        repo.save_word_progress(state)
    row = (
        db.query(UserWordProgress)
        .filter(UserWordProgress.user_id == user_id, UserWordProgress.word_id == word_id)
        .first()
    )
    assert row is not None
    return row


def get_due_word_ids(db: Session, user_id: int, limit: int = 12) -> list[int]:
    now = utc_now()
    rows = (
        db.query(UserWordProgress.word_id)
        .filter(
            UserWordProgress.user_id == user_id,
            UserWordProgress.next_review.isnot(None),
            UserWordProgress.next_review <= now,
        )
        .order_by(UserWordProgress.next_review)
        .limit(limit)
        .all()
    )
    return [r[0] for r in rows]
