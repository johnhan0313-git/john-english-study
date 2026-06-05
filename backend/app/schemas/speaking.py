from __future__ import annotations

from pydantic import BaseModel


class SpeakingEvaluateResponse(BaseModel):
    transcript: str
    expected: str
    match_rate: float
    missing_words: list[str]
    extra_words: list[str]
    feedback: str
