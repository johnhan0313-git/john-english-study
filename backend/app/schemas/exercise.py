from __future__ import annotations

from pydantic import BaseModel, Field


class ExerciseOption(BaseModel):
    label: str
    text: str


class ExercisePayload(BaseModel):
    question: str
    options: list[ExerciseOption] = Field(default_factory=list)
    passage_with_blanks: str | None = None
    blanks: list[dict] = Field(default_factory=list)
    explanation: str | None = None


class ExerciseResponse(BaseModel):
    id: int
    scenario_id: int
    type: str
    payload: ExercisePayload
    sort_order: int


class ExerciseSubmitRequest(BaseModel):
    answer: str | list[str]
    device_id: str = "default"


class ExerciseSubmitResponse(BaseModel):
    correct: bool
    correct_answer: str | list[str]
    explanation: str | None = None
    familiarity_updates: list[dict] = Field(default_factory=list)


class BatchSubmitRequest(BaseModel):
    answers: dict[int, str | list[str]]
    device_id: str = "default"


class BatchSubmitResponse(BaseModel):
    score: float
    total: int
    correct: int
    results: list[ExerciseSubmitResponse]
