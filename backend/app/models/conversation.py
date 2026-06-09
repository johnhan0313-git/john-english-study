from __future__ import annotations

from typing import Any, Optional

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.db.json_type import JSONField


class ConversationSession(Base):
    __tablename__ = "conversation_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=True)
    device_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    scenario_id: Mapped[Optional[int]] = mapped_column(ForeignKey("scenarios.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(256))
    theme: Mapped[str] = mapped_column(String(128), default="general")
    level: Mapped[str] = mapped_column(String(16), default="cet4")
    role_ai: Mapped[str] = mapped_column(String(64), default="Assistant")
    role_user: Mapped[str] = mapped_column(String(64), default="Learner")
    scene_brief: Mapped[Any] = mapped_column(JSONField, default=dict)
    target_words: Mapped[Any] = mapped_column(JSONField, default=list)
    mode: Mapped[str] = mapped_column(String(16), default="text")
    status: Mapped[str] = mapped_column(String(16), default="active")
    turn_count: Mapped[int] = mapped_column(Integer, default=0)
    words_used: Mapped[Any] = mapped_column(JSONField, default=list)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    messages: Mapped[list["ConversationMessage"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ConversationMessage.id",
    )


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("conversation_sessions.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(Text)
    meta: Mapped[Any] = mapped_column(JSONField, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    session: Mapped["ConversationSession"] = relationship(back_populates="messages")
