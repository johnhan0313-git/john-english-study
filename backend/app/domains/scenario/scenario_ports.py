from __future__ import annotations

from typing import Any, AsyncIterator, Protocol


class LlmPort(Protocol):
    async def chat_json(
        self,
        messages: list[dict[str, str]],
        schema_hint: str,
        *,
        task: str = "generic",
    ) -> dict[str, Any]: ...

    async def chat_text(self, messages: list[dict[str, str]]) -> str: ...

    async def chat_stream(self, messages: list[dict[str, str]]) -> AsyncIterator[str]: ...


class WordSelectionPort(Protocol):
    def pick_words(
        self,
        *,
        user_id: int,
        level: str,
        theme: str | None,
        word_ids: list[int],
        word_count: int,
        word_strategy: str,
        exclude_recent: bool,
    ) -> list[dict[str, Any]]:
        """Return word dicts with at least id, lemma, pos, definitions."""
        ...


class ExerciseDraftPort(Protocol):
    def save_from_ai(self, scenario_id: int, exercises: list[dict]) -> int:
        """Persist AI exercise drafts; return count saved. No commit."""
        ...
