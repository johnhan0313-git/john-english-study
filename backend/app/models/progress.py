from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserWordProgress(Base):
    __tablename__ = "user_word_progress"
    __table_args__ = (UniqueConstraint("user_id", "word_id", name="uq_user_word"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, index=True, nullable=True)
    device_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    word_id: Mapped[int] = mapped_column(Integer, index=True)
    familiarity: Mapped[int] = mapped_column(Integer, default=0)
    next_review: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    correct_count: Mapped[int] = mapped_column(Integer, default=0)
    wrong_count: Mapped[int] = mapped_column(Integer, default=0)
    last_reviewed: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    word: Mapped["Word"] = relationship(
        back_populates="progress_records",
        foreign_keys=[word_id],
        primaryjoin="UserWordProgress.word_id==Word.id",
    )


class ScenarioAttempt(Base):
    __tablename__ = "scenario_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scenario_id: Mapped[int] = mapped_column(Integer, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, index=True, nullable=True)
    device_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    total_questions: Mapped[int] = mapped_column(Integer, default=0)
    correct_questions: Mapped[int] = mapped_column(Integer, default=0)
    completed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    details: Mapped[str] = mapped_column(Text, default="{}")

    scenario: Mapped["Scenario"] = relationship(
        back_populates="attempts",
        foreign_keys=[scenario_id],
        primaryjoin="ScenarioAttempt.scenario_id==Scenario.id",
    )


class LearningStreak(Base):
    __tablename__ = "learning_streaks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, unique=True, nullable=True, index=True)
    device_id: Mapped[Optional[str]] = mapped_column(String(64), unique=True, nullable=True, index=True)
    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0)
    last_active_date: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)


from app.models.scenario import Scenario  # noqa: E402
from app.models.word import Word  # noqa: E402
