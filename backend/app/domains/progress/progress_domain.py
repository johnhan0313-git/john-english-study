from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta


SRS_INTERVALS_DAYS = [1, 3, 7, 14, 30]


@dataclass
class WordProgressState:
    user_id: int
    word_id: int
    familiarity: int = 0
    correct_count: int = 0
    wrong_count: int = 0
    last_reviewed: datetime | None = None
    next_review: datetime | None = None
    id: int | None = None


def apply_answer(progress: WordProgressState, correct: bool, now: datetime) -> WordProgressState:
    """Pure SRS transition — no persistence."""
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
