from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.config import Settings
from app.services.speaking.evaluator import (
    evaluate_speaking,
    evaluate_writing,
    generate_writing_sample,
)


@dataclass(frozen=True)
class EvaluateWritingInput:
    prompt: str
    content: str
    target_words: list[str]


@dataclass(frozen=True)
class GenerateWritingSampleInput:
    prompt: str
    target_words: list[str]
    level: str = "cet4"
    theme: str | None = None
    regenerate: bool = False


@dataclass(frozen=True)
class EvaluateSpeakingInput:
    expected: str
    transcript: str


class EvaluateWritingCommand:
    def __init__(self, settings: Settings):
        self._settings = settings

    async def execute(self, inp: EvaluateWritingInput) -> dict[str, Any]:
        return await evaluate_writing(
            self._settings, inp.prompt, inp.content, inp.target_words
        )


class GenerateWritingSampleCommand:
    def __init__(self, settings: Settings):
        self._settings = settings

    async def execute(self, inp: GenerateWritingSampleInput) -> dict[str, Any]:
        return await generate_writing_sample(
            self._settings,
            inp.prompt,
            inp.target_words,
            level=inp.level,
            theme=inp.theme,
            regenerate=inp.regenerate,
        )


class EvaluateSpeakingCommand:
    def execute(self, inp: EvaluateSpeakingInput) -> dict[str, Any]:
        return evaluate_speaking(inp.expected, inp.transcript)
