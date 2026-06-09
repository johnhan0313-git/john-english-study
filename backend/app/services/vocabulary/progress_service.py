from __future__ import annotations

from datetime import timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.progress import LearningStreak, ScenarioAttempt, UserWordProgress
from app.models.word import Word
from app.utils.json_helpers import parse_json_field
from app.utils.time import local_today, utc_now


def get_progress_overview(db: Session, user_id: int) -> dict:
    total = db.query(Word).count()
    learned = (
        db.query(UserWordProgress)
        .filter(UserWordProgress.user_id == user_id, UserWordProgress.familiarity > 0)
        .count()
    )
    mastered = (
        db.query(UserWordProgress)
        .filter(UserWordProgress.user_id == user_id, UserWordProgress.familiarity >= 5)
        .count()
    )
    now = utc_now()
    due_review = (
        db.query(UserWordProgress)
        .filter(
            UserWordProgress.user_id == user_id,
            UserWordProgress.next_review.isnot(None),
            UserWordProgress.next_review <= now,
        )
        .count()
    )
    scenarios_completed = (
        db.query(ScenarioAttempt).filter(ScenarioAttempt.user_id == user_id).count()
    )
    exercises_completed = db.query(func.sum(ScenarioAttempt.correct_questions)).filter(
        ScenarioAttempt.user_id == user_id
    ).scalar() or 0

    streak = db.query(LearningStreak).filter(LearningStreak.user_id == user_id).first()
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


def get_review_words(db: Session, user_id: int, limit: int = 20) -> list[dict]:
    now = utc_now()
    rows = (
        db.query(UserWordProgress, Word)
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


def record_scenario_attempt(
    db: Session,
    scenario_id: int,
    user_id: int,
    total: int,
    correct: int,
    details: dict | None = None,
) -> ScenarioAttempt:
    attempt = ScenarioAttempt(
        scenario_id=scenario_id,
        user_id=user_id,
        total_questions=total,
        correct_questions=correct,
        score=round(correct / total * 100, 1) if total else 0,
        details=str(details or {}),
    )
    db.add(attempt)
    update_streak(db, user_id)
    db.commit()
    return attempt


def update_streak(db: Session, user_id: int, tz_name: str = "Asia/Shanghai") -> LearningStreak:
    today = local_today(tz_name).isoformat()
    streak = db.query(LearningStreak).filter(LearningStreak.user_id == user_id).first()
    if not streak:
        streak = LearningStreak(user_id=user_id, current_streak=1, longest_streak=1, last_active_date=today)
        db.add(streak)
        return streak

    if streak.last_active_date == today:
        return streak

    yesterday_str = (local_today(tz_name) - timedelta(days=1)).isoformat()
    if streak.last_active_date == yesterday_str:
        streak.current_streak += 1
    else:
        streak.current_streak = 1
    streak.longest_streak = max(streak.longest_streak, streak.current_streak)
    streak.last_active_date = today
    return streak
