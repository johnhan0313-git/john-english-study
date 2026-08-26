from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class ExerciseRecord:
    id: int
    scenario_id: int
    type: str
    payload: dict[str, Any]
    answer_key: dict[str, Any]
    sort_order: int


class ExerciseRepository(Protocol):
    def get_owned_by_id(self, user_id: int, exercise_id: int) -> ExerciseRecord | None: ...

    def list_owned_scenario_exercises(
        self, user_id: int, scenario_id: int
    ) -> list[ExerciseRecord] | None:
        """Return exercises ordered by sort_order, or None if scenario is not owned."""
        ...

    def list_scenario_word_ids(self, scenario_id: int) -> list[int]: ...
