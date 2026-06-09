from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.db.json_type import JSONField


class Scenario(Base):
    __tablename__ = "scenarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(256))
    theme: Mapped[str] = mapped_column(String(128), index=True)
    level: Mapped[str] = mapped_column(String(16), index=True)
    scenario_type: Mapped[str] = mapped_column(String(32), default="narrative")
    content: Mapped[Any] = mapped_column(JSONField)
    dialogue: Mapped[Any] = mapped_column(JSONField, default=list)
    audio_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    device_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=True)
    is_daily: Mapped[bool] = mapped_column(Boolean, default=False)
    daily_date: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, index=True)
    daily_kind: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    words: Mapped[list["ScenarioWord"]] = relationship(back_populates="scenario", cascade="all, delete-orphan")
    exercises: Mapped[list["Exercise"]] = relationship(back_populates="scenario", cascade="all, delete-orphan")
    attempts: Mapped[list["ScenarioAttempt"]] = relationship(back_populates="scenario")


class ScenarioWord(Base):
    __tablename__ = "scenario_words"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scenario_id: Mapped[int] = mapped_column(ForeignKey("scenarios.id", ondelete="CASCADE"), index=True)
    word_id: Mapped[int] = mapped_column(ForeignKey("words.id", ondelete="CASCADE"), index=True)

    scenario: Mapped["Scenario"] = relationship(back_populates="words")
    word: Mapped["Word"] = relationship(back_populates="scenario_words")


from app.models.exercise import Exercise  # noqa: E402
from app.models.progress import ScenarioAttempt  # noqa: E402
from app.models.word import Word  # noqa: E402
