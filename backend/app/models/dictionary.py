from __future__ import annotations

from typing import Optional

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DictionaryEntry(Base):
    __tablename__ = "dictionary_entries"

    lemma: Mapped[str] = mapped_column(String(128), primary_key=True)
    definition: Mapped[str] = mapped_column(Text, nullable=False)
    pos: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    source: Mapped[str] = mapped_column(String(32), default="cet4")
