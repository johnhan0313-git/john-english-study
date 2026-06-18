from __future__ import annotations

from pydantic import BaseModel, Field


class ProgressOverview(BaseModel):
    total_words: int
    learned_words: int
    mastered_words: int
    due_review: int
    mastery_rate: float
    scenarios_completed: int
    current_streak: int
    longest_streak: int
    exercises_completed: int


class ReviewWordItem(BaseModel):
    id: int
    lemma: str
    level: str
    familiarity: int
    definitions: list[str] = Field(default_factory=list)
    next_review: str | None = None


class WritingEvaluateRequest(BaseModel):
    prompt: str
    content: str
    target_words: list[str] = Field(default_factory=list)


class WritingEvaluateResponse(BaseModel):
    score: float
    grammar_feedback: str
    vocabulary_feedback: str
    used_target_words: list[str]
    missing_target_words: list[str]
    suggestions: list[str]


class WritingSampleRequest(BaseModel):
    prompt: str
    target_words: list[str] = Field(default_factory=list)
    level: str = "cet4"
    theme: str | None = None
    regenerate: bool = False


class WritingSampleResponse(BaseModel):
    sample_en: str
    sample_zh: str
