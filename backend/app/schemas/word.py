from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WordBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lemma: str
    phonetic: str | None = None
    level: str
    pos: str | None = None
    definitions: list[str] = Field(default_factory=list)
    familiarity: int | None = None


class WordDetail(WordBrief):
    examples: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    groups: list[str] = Field(default_factory=list)
    scenario_count: int = 0


class WordListResponse(BaseModel):
    items: list[WordBrief]
    total: int
    page: int
    page_size: int


class WordStatsResponse(BaseModel):
    total: int
    cet4_count: int
    cet6_count: int
    learned: int
    mastered: int
    due_review: int
    mastery_rate: float


class WordGroupResponse(BaseModel):
    id: int
    slug: str
    name_zh: str
    name_en: str
    description: str | None = None
    word_count: int = 0
