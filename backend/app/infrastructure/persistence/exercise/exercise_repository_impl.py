from __future__ import annotations

from sqlalchemy.orm import Session

from app.domains.exercise.exercise_repository import ExerciseRecord
from app.models.exercise import Exercise
from app.models.scenario import Scenario, ScenarioWord
from app.utils.json_helpers import parse_json_field


class SqlAlchemyExerciseRepository:
    def __init__(self, session: Session):
        self._session = session

    def get_owned_by_id(self, user_id: int, exercise_id: int) -> ExerciseRecord | None:
        row = (
            self._session.query(Exercise)
            .join(Scenario, Scenario.id == Exercise.scenario_id)
            .filter(Exercise.id == exercise_id, Scenario.user_id == user_id)
            .first()
        )
        if not row:
            return None
        return self._to_record(row)

    def list_owned_scenario_exercises(
        self, user_id: int, scenario_id: int
    ) -> list[ExerciseRecord] | None:
        owned = (
            self._session.query(Scenario.id)
            .filter(Scenario.id == scenario_id, Scenario.user_id == user_id)
            .first()
        )
        if not owned:
            return None
        rows = (
            self._session.query(Exercise)
            .filter(Exercise.scenario_id == scenario_id)
            .order_by(Exercise.sort_order)
            .all()
        )
        return [self._to_record(row) for row in rows]

    def list_scenario_word_ids(self, scenario_id: int) -> list[int]:
        return [
            sw.word_id
            for sw in self._session.query(ScenarioWord)
            .filter(ScenarioWord.scenario_id == scenario_id)
            .all()
        ]

    @staticmethod
    def _to_record(row: Exercise) -> ExerciseRecord:
        return ExerciseRecord(
            id=row.id,
            scenario_id=row.scenario_id,
            type=row.type,
            payload=parse_json_field(row.payload, {}),
            answer_key=parse_json_field(row.answer_key, {}),
            sort_order=row.sort_order,
        )
