from __future__ import annotations

from datetime import timedelta
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.domains.progress.progress_domain import WordProgressState
from app.models.progress import LearningStreak, ScenarioAttempt, UserWordProgress
from app.models.word import Word
from app.utils.json_helpers import parse_json_field
from app.utils.time import local_today, utc_now


class SqlAlchemyProgressRepository:
    def __init__(self, session: Session):
        self._session = session

    def get_word_progress(self, user_id: int, word_id: int) -> WordProgressState | None:
        row = (
            self._session.query(UserWordProgress)
            .filter(UserWordProgress.user_id == user_id, UserWordProgress.word_id == word_id)
            .first()
        )
        if not row:
            return None
        return WordProgressState(
            id=row.id,
            user_id=row.user_id,
            word_id=row.word_id,
            familiarity=row.familiarity,
            correct_count=row.correct_count,
            wrong_count=row.wrong_count,
            last_reviewed=row.last_reviewed,
            next_review=row.next_review,
        )

    def add_word_progress(self, state: WordProgressState) -> WordProgressState:
        row = UserWordProgress(
            user_id=state.user_id,
            word_id=state.word_id,
            familiarity=state.familiarity,
            correct_count=state.correct_count,
            wrong_count=state.wrong_count,
            last_reviewed=state.last_reviewed,
            next_review=state.next_review,
        )
        self._session.add(row)
        self._session.flush()
        state.id = row.id
        return state

    def save_word_progress(self, state: WordProgressState) -> None:
        if state.id is None:
            self.add_word_progress(state)
            return
        row = self._session.query(UserWordProgress).filter(UserWordProgress.id == state.id).first()
        if not row:
            self.add_word_progress(state)
            return
        row.familiarity = state.familiarity
        row.correct_count = state.correct_count
        row.wrong_count = state.wrong_count
        row.last_reviewed = state.last_reviewed
        row.next_review = state.next_review

    def add_scenario_attempt(
        self,
        *,
        scenario_id: int,
        user_id: int,
        total: int,
        correct: int,
        details: dict | None = None,
    ) -> None:
        attempt = ScenarioAttempt(
            scenario_id=scenario_id,
            user_id=user_id,
            total_questions=total,
            correct_questions=correct,
            score=round(correct / total * 100, 1) if total else 0,
            details=str(details or {}),
        )
        self._session.add(attempt)

    def touch_streak(self, user_id: int, tz_name: str) -> None:
        today = local_today(tz_name).isoformat()
        streak = self._session.query(LearningStreak).filter(LearningStreak.user_id == user_id).first()
        if not streak:
            self._session.add(
                LearningStreak(
                    user_id=user_id,
                    current_streak=1,
                    longest_streak=1,
                    last_active_date=today,
                )
            )
            return
        if streak.last_active_date == today:
            return
        yesterday_str = (local_today(tz_name) - timedelta(days=1)).isoformat()
        if streak.last_active_date == yesterday_str:
            streak.current_streak += 1
        else:
            streak.current_streak = 1
        streak.longest_streak = max(streak.longest_streak, streak.current_streak)
        streak.last_active_date = today

    def get_overview(self, user_id: int) -> dict[str, Any]:
        total = self._session.query(Word).count()
        learned = (
            self._session.query(UserWordProgress)
            .filter(UserWordProgress.user_id == user_id, UserWordProgress.familiarity > 0)
            .count()
        )
        mastered = (
            self._session.query(UserWordProgress)
            .filter(UserWordProgress.user_id == user_id, UserWordProgress.familiarity >= 5)
            .count()
        )
        now = utc_now()
        due_review = (
            self._session.query(UserWordProgress)
            .filter(
                UserWordProgress.user_id == user_id,
                UserWordProgress.next_review.isnot(None),
                UserWordProgress.next_review <= now,
            )
            .count()
        )
        scenarios_completed = (
            self._session.query(ScenarioAttempt).filter(ScenarioAttempt.user_id == user_id).count()
        )
        exercises_completed = (
            self._session.query(func.sum(ScenarioAttempt.correct_questions))
            .filter(ScenarioAttempt.user_id == user_id)
            .scalar()
            or 0
        )

        streak = self._session.query(LearningStreak).filter(LearningStreak.user_id == user_id).first()
        current_streak = streak.current_streak if streak else 0
        longest_streak = streak.longest_streak if streak else 0

        mastery_rate = round(mastered / total * 100, 1) if total else 0.0
        return {
            "total_words": total,
            "learned_words": learned,
            "mastered_words": mastered,
            "due_review": due_review,
            "mastery_rate": mastery_rate,
            "scenarios_completed": scenarios_completed,
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "exercises_completed": int(exercises_completed),
        }

    def get_review_words(self, user_id: int, limit: int = 20) -> list[dict[str, Any]]:
        now = utc_now()
        rows = (
            self._session.query(UserWordProgress, Word)
            .join(Word, Word.id == UserWordProgress.word_id)
            .filter(
                UserWordProgress.user_id == user_id,
                UserWordProgress.next_review.isnot(None),
                UserWordProgress.next_review <= now,
            )
            .order_by(UserWordProgress.next_review)
            .limit(limit)
            .all()
        )
        return [
            {
                "id": word.id,
                "lemma": word.lemma,
                "level": word.level,
                "familiarity": progress.familiarity,
                "definitions": parse_json_field(word.definitions, []),
                "next_review": progress.next_review.isoformat() if progress.next_review else None,
            }
            for progress, word in rows
        ]
