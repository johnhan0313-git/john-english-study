from __future__ import annotations

from pydantic import BaseModel, Field


class PhoneticExample(BaseModel):
    word: str
    ipa: str
    meaning_zh: str


class PhoneticBrief(BaseModel):
    id: int
    symbol: str
    category: str
    subcategory: str | None = None
    name_zh: str
    name_en: str
    preview_word: str | None = None


class PhoneticDetail(PhoneticBrief):
    description: str | None = None
    examples: list[PhoneticExample] = Field(default_factory=list)
    sound_cue: str | None = None


class PhoneticCategoryGroup(BaseModel):
    category: str
    category_zh: str
    items: list[PhoneticBrief]
    count: int


class PhoneticListResponse(BaseModel):
    items: list[PhoneticBrief]
    groups: list[PhoneticCategoryGroup]
    total: int


class GrammarExample(BaseModel):
    en: str
    zh: str
    note: str | None = None


class GrammarBrief(BaseModel):
    id: int
    slug: str
    category: str
    title: str
    level: str
    summary: str


class GrammarDetail(GrammarBrief):
    structure: str | None = None
    rules: list[str] = Field(default_factory=list)
    examples: list[GrammarExample] = Field(default_factory=list)
    tips: str | None = None


class GrammarCategoryGroup(BaseModel):
    category: str
    category_zh: str
    items: list[GrammarBrief]
    count: int


class GrammarListResponse(BaseModel):
    items: list[GrammarBrief]
    groups: list[GrammarCategoryGroup]
    total: int
