from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal


@dataclass(frozen=True)
class GenerateScenarioInput:
    user_id: int
    level: str = "cet4"
    theme: str | None = None
    word_ids: tuple[int, ...] = ()
    scenario_type: str = "narrative"
    word_count: int = 10
    word_strategy: Literal["smart", "new", "review"] = "smart"
    exclude_recent: bool = True
    is_daily: bool = False
    daily_kind: str | None = None
    prefer_review: bool = False


@dataclass(frozen=True)
class CreateMissingDailySlotsInput:
    user_id: int
    daily_date: str
    target_count: int


@dataclass(frozen=True)
class GetDailyScenariosInput:
    user_id: int
    daily_date: str


@dataclass(frozen=True)
class GetScenarioInput:
    scenario_id: int
    user_id: int


@dataclass(frozen=True)
class ListScenariosInput:
    user_id: int
    skip: int = 0
    limit: int = 20


@dataclass
class ScenarioBriefOutput:
    id: int
    title: str
    theme: str
    level: str
    scenario_type: str
    is_daily: bool
    daily_kind: str | None
    word_count: int
    created_at: datetime
    summary_preview: str | None = None
    is_completed: bool = False
    best_score: float | None = None
    conversation_count: int = 0
    exercise_count: int = 0


@dataclass
class ScenarioDetailOutput(ScenarioBriefOutput):
    content: dict[str, Any] | None = None
    dialogue: list[dict[str, str]] | None = None
    words: list[str] | None = None
    has_audio: bool = False


@dataclass
class DailyScenariosOutput:
    date: str
    items: list[ScenarioBriefOutput]
    generated: bool = False


@dataclass
class ScenarioListOutput:
    items: list[ScenarioBriefOutput]
    total: int


@dataclass
class ScenarioTranslationOutput:
    passage_zh: str
    dialogue_zh: list[dict[str, str]]
