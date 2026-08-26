from __future__ import annotations

from typing import Protocol

from app.domains.progress.progress_domain import WordProgressState


class ProgressRepository(Protocol):
    def get_word_progress(self, user_id: int, word_id: int) -> WordProgressState | None: ...

    def add_word_progress(self, state: WordProgressState) -> WordProgressState: ...

    def save_word_progress(self, state: WordProgressState) -> None: ...

    def add_scenario_attempt(
        self,
        *,
        scenario_id: int,
        user_id: int,
        total: int,
        correct: int,
        details: dict | None = None,
    ) -> None: ...

    def touch_streak(self, user_id: int, tz_name: str) -> None: ...
