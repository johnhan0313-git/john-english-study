from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.db.json_type import JSONField


class Scenario(Base):
    __tablename__ = "scenarios"
    __table_args__ = (
        UniqueConstraint("user_id", "daily_date", "daily_kind", name="uq_scenarios_user_daily_kind"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(256))
    theme: Mapped[str] = mapped_column(String(128), index=True)
    level: Mapped[str] = mapped_column(String(16), index=True)
    scenario_type: Mapped[str] = mapped_column(String(32), default="narrative")
    content: Mapped[Any] = mapped_column(JSONField)
    dialogue: Mapped[Any] = mapped_column(JSONField, default=list)
    audio_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    device_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, index=True, nullable=True)
    is_daily: Mapped[bool] = mapped_column(Boolean, default=False)
    daily_date: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, index=True)
    daily_kind: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    words: Mapped[list["ScenarioWord"]] = relationship(
        back_populates="scenario",
        cascade="all, delete-orphan",
        foreign_keys="ScenarioWord.scenario_id",
        primaryjoin="Scenario.id==ScenarioWord.scenario_id",
    )
    exercises: Mapped[list["Exercise"]] = relationship(
        back_populates="scenario",
        cascade="all, delete-orphan",
        foreign_keys="Exercise.scenario_id",
        primaryjoin="Scenario.id==Exercise.scenario_id",
    )
    attempts: Mapped[list["ScenarioAttempt"]] = relationship(
        back_populates="scenario",
        foreign_keys="ScenarioAttempt.scenario_id",
        primaryjoin="Scenario.id==ScenarioAttempt.scenario_id",
    )


class ScenarioWord(Base):
    __tablename__ = "scenario_words"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scenario_id: Mapped[int] = mapped_column(Integer, index=True)
    word_id: Mapped[int] = mapped_column(Integer, index=True)

    scenario: Mapped["Scenario"] = relationship(
        back_populates="words",
        foreign_keys=[scenario_id],
        primaryjoin="ScenarioWord.scenario_id==Scenario.id",
    )
    word: Mapped["Word"] = relationship(
        back_populates="scenario_words",
        foreign_keys=[word_id],
        primaryjoin="ScenarioWord.word_id==Word.id",
    )


from app.models.exercise import Exercise  # noqa: E402
from app.models.progress import ScenarioAttempt  # noqa: E402
from app.models.word import Word  # noqa: E402
