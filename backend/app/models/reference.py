from __future__ import annotations

from typing import Optional

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PhoneticSymbol(Base):
    __tablename__ = "phonetic_symbols"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(32), index=True)
    subcategory: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    name_zh: Mapped[str] = mapped_column(String(64))
    name_en: Mapped[str] = mapped_column(String(64))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    examples: Mapped[str] = mapped_column(Text, default="[]")  # JSON: [{word, ipa, meaning_zh}]
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class GrammarPoint(Base):
    __tablename__ = "grammar_points"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(32), index=True)
    title: Mapped[str] = mapped_column(String(128))
    level: Mapped[str] = mapped_column(String(16), index=True)  # cet4 | cet6 | both
    summary: Mapped[str] = mapped_column(Text)
    structure: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rules: Mapped[str] = mapped_column(Text, default="[]")  # JSON string array
    examples: Mapped[str] = mapped_column(Text, default="[]")  # JSON
    tips: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
