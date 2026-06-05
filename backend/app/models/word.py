from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Word(Base):
    __tablename__ = "words"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lemma: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    phonetic: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    level: Mapped[str] = mapped_column(String(16), index=True)  # cet4 | cet6 | both
    pos: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    definitions: Mapped[str] = mapped_column(Text, default="[]")  # JSON array
    examples: Mapped[str] = mapped_column(Text, default="[]")  # JSON array
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    tags: Mapped[list["WordTag"]] = relationship(back_populates="word", cascade="all, delete-orphan")
    group_memberships: Mapped[list["WordGroupMember"]] = relationship(back_populates="word")
    scenario_words: Mapped[list["ScenarioWord"]] = relationship(back_populates="word")
    progress_records: Mapped[list["UserWordProgress"]] = relationship(back_populates="word")


class WordTag(Base):
    __tablename__ = "word_tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    word_id: Mapped[int] = mapped_column(ForeignKey("words.id", ondelete="CASCADE"), index=True)
    tag: Mapped[str] = mapped_column(String(64), index=True)

    word: Mapped["Word"] = relationship(back_populates="tags")


class WordGroup(Base):
    __tablename__ = "word_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name_zh: Mapped[str] = mapped_column(String(128))
    name_en: Mapped[str] = mapped_column(String(128))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    members: Mapped[list["WordGroupMember"]] = relationship(back_populates="group", cascade="all, delete-orphan")


class WordGroupMember(Base):
    __tablename__ = "word_group_members"
    __table_args__ = (UniqueConstraint("group_id", "word_id", name="uq_group_word"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("word_groups.id", ondelete="CASCADE"), index=True)
    word_id: Mapped[int] = mapped_column(ForeignKey("words.id", ondelete="CASCADE"), index=True)

    group: Mapped["WordGroup"] = relationship(back_populates="members")
    word: Mapped["Word"] = relationship(back_populates="group_memberships")
