from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.infrastructure.unit_of_work import UnitOfWorkFactory
from app.models.exercise import Exercise
from app.models.scenario import Scenario
from app.services.vocabulary.progress_service import get_progress_overview, get_review_words
from app.utils.json_helpers import parse_json_field


@dataclass(frozen=True)
class GetProgressOverviewInput:
    user_id: int


@dataclass(frozen=True)
class GetReviewWordsInput:
    user_id: int
    limit: int = 20


class GetProgressOverviewQuery:
    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

    def execute(self, inp: GetProgressOverviewInput) -> dict[str, Any]:
        with self._uow_factory() as uow:
            return get_progress_overview(uow.session, inp.user_id)


class GetReviewWordsQuery:
    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

    def execute(self, inp: GetReviewWordsInput) -> list[dict]:
        with self._uow_factory() as uow:
            return get_review_words(uow.session, inp.user_id, inp.limit)


@dataclass(frozen=True)
class ListExercisesInput:
    user_id: int
    scenario_id: int


class ListExercisesQuery:
    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

    def execute(self, inp: ListExercisesInput) -> list[dict]:
        with self._uow_factory() as uow:
            owned = (
                uow.session.query(Scenario.id)
                .filter(Scenario.id == inp.scenario_id, Scenario.user_id == inp.user_id)
                .first()
            )
            if not owned:
                raise ValueError("Scenario not found")
            exercises = (
                uow.session.query(Exercise)
                .filter(Exercise.scenario_id == inp.scenario_id)
                .order_by(Exercise.sort_order)
                .all()
            )
            return [
                {
                    "id": ex.id,
                    "scenario_id": ex.scenario_id,
                    "type": ex.type,
                    "payload": parse_json_field(ex.payload, {}),
                    "sort_order": ex.sort_order,
                }
                for ex in exercises
            ]
