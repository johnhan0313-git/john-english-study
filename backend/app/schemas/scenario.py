from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class DialogueLine(BaseModel):
    speaker: str
    text: str


class WordUsage(BaseModel):
    word: str
    sentence: str
    meaning_zh: str | None = None


class ScenarioContent(BaseModel):
    passage: str
    summary_zh: str
    fun_fact: str | None = None
    word_usage: list[WordUsage] = Field(default_factory=list)


class ScenarioGenerateRequest(BaseModel):
    theme: str | None = None
    level: str = "cet4"
    word_ids: list[int] = Field(default_factory=list)
    scenario_type: str = "narrative"  # narrative | dialogue
    word_count: int = Field(default=10, ge=5, le=15)


class ScenarioBrief(BaseModel):
    id: int
    title: str
    theme: str
    level: str
    scenario_type: str
    is_daily: bool = False
    daily_kind: str | None = None
    word_count: int = 0
    created_at: datetime


class ScenarioDetail(ScenarioBrief):
    content: ScenarioContent
    dialogue: list[DialogueLine] = Field(default_factory=list)
    words: list[str] = Field(default_factory=list)
    has_audio: bool = False
    exercise_count: int = 0


class ScenarioListResponse(BaseModel):
    items: list[ScenarioBrief]
    total: int


class DailyScenariosResponse(BaseModel):
    date: str
    items: list[ScenarioBrief]
    generated: bool = False
