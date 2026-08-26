from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class ScenarioContent:
    passage: str
    summary_zh: str = ""
    fun_fact: str | None = None
    word_usage: list[dict[str, Any]] = field(default_factory=list)
    passage_zh: str | None = None
    dialogue_zh: list[dict[str, Any]] | None = None


@dataclass
class DialogueLine:
    speaker: str
    text: str


@dataclass
class ScenarioWordRef:
    word_id: int
    lemma: str = ""


@dataclass
class ScenarioAggregate:
    """Scenario learning aggregate root (persistence-independent)."""

    id: int | None
    title: str
    theme: str
    level: str
    scenario_type: str
    content: ScenarioContent
    dialogue: list[DialogueLine]
    user_id: int
    is_daily: bool = False
    daily_date: str | None = None
    daily_kind: str | None = None
    audio_path: str | None = None
    created_at: datetime | None = None
    words: list[ScenarioWordRef] = field(default_factory=list)
    exercise_count: int = 0

    @staticmethod
    def create_generated(
        *,
        title: str,
        theme: str,
        level: str,
        scenario_type: str,
        content: ScenarioContent,
        dialogue: list[DialogueLine],
        user_id: int,
        word_ids: list[int],
        is_daily: bool = False,
        daily_date: str | None = None,
        daily_kind: str | None = None,
    ) -> ScenarioAggregate:
        if len(word_ids) < 3:
            raise ValueError("Not enough words available for scenario generation")
        return ScenarioAggregate(
            id=None,
            title=title or f"Scenario: {theme}",
            theme=theme,
            level=level,
            scenario_type=scenario_type,
            content=content,
            dialogue=dialogue,
            user_id=user_id,
            is_daily=is_daily,
            daily_date=daily_date,
            daily_kind=daily_kind,
            words=[ScenarioWordRef(word_id=wid) for wid in word_ids],
        )


DAILY_SLOT_KINDS: tuple[tuple[str, str, str], ...] = (
    ("review", "cet4", "review"),
    ("new", "cet4", "new"),
    ("challenge", "cet6", "smart"),
)
