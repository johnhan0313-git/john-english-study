from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domains.exercise.exercise_repository import ExerciseRepository
from app.domains.progress.progress_repository import ProgressRepository
from app.infrastructure.unit_of_work import UnitOfWorkFactory


@dataclass(frozen=True)
class GetProgressOverviewInput:
    user_id: int


@dataclass(frozen=True)
class GetReviewWordsInput:
    user_id: int
    limit: int = 20


class GetProgressOverviewQuery:
    def __init__(self, uow_factory: UnitOfWorkFactory, repository_factory: Any):
        self._uow_factory = uow_factory
        self._repository_factory = repository_factory

    def execute(self, inp: GetProgressOverviewInput) -> dict[str, Any]:
        with self._uow_factory() as uow:
            repo: ProgressRepository = self._repository_factory(uow.session)
            return repo.get_overview(inp.user_id)


class GetReviewWordsQuery:
    def __init__(self, uow_factory: UnitOfWorkFactory, repository_factory: Any):
        self._uow_factory = uow_factory
        self._repository_factory = repository_factory

    def execute(self, inp: GetReviewWordsInput) -> list[dict]:
        with self._uow_factory() as uow:
            repo: ProgressRepository = self._repository_factory(uow.session)
            return repo.get_review_words(inp.user_id, inp.limit)


@dataclass(frozen=True)
class ListExercisesInput:
    user_id: int
    scenario_id: int


class ListExercisesQuery:
    def __init__(self, uow_factory: UnitOfWorkFactory, repository_factory: Any):
        self._uow_factory = uow_factory
        self._repository_factory = repository_factory

    def execute(self, inp: ListExercisesInput) -> list[dict]:
        with self._uow_factory() as uow:
            repo: ExerciseRepository = self._repository_factory(uow.session)
            exercises = repo.list_owned_scenario_exercises(inp.user_id, inp.scenario_id)
            if exercises is None:
                raise ValueError("Scenario not found")
            return [
                {
                    "id": ex.id,
                    "scenario_id": ex.scenario_id,
                    "type": ex.type,
                    "payload": ex.payload,
                    "sort_order": ex.sort_order,
                }
                for ex in exercises
            ]
