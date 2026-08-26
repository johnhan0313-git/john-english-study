from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.application.progress.progress_command import RecordAnswerCommand, RecordAnswerInput, RecordScenarioAttemptCommand, RecordScenarioAttemptInput
from app.infrastructure.unit_of_work import UnitOfWorkFactory
from app.models.exercise import Exercise
from app.models.scenario import Scenario, ScenarioWord
from app.services.exercise.generator import check_exercise_answer
from app.utils.json_helpers import parse_json_field


@dataclass(frozen=True)
class SubmitExerciseInput:
    user_id: int
    exercise_id: int
    answer: str | list[str]


@dataclass(frozen=True)
class SubmitBatchInput:
    user_id: int
    scenario_id: int
    answers: dict[int, str | list[str]]
    timezone: str = "Asia/Shanghai"


class SubmitExerciseCommand:
    def __init__(
        self,
        uow_factory: UnitOfWorkFactory,
        record_answer: RecordAnswerCommand,
    ):
        self._uow_factory = uow_factory
        self._record_answer = record_answer

    def execute(self, inp: SubmitExerciseInput) -> dict:
        with self._uow_factory() as uow:
            exercise = (
                uow.session.query(Exercise)
                .join(Scenario, Scenario.id == Exercise.scenario_id)
                .filter(Exercise.id == inp.exercise_id, Scenario.user_id == inp.user_id)
                .first()
            )
            if not exercise:
                raise ValueError("Exercise not found")
            result = self._grade(uow.session, exercise, inp.answer, inp.user_id)
            uow.commit()
            return result

    def _grade(self, session: Session, exercise: Exercise, answer: str | list[str], user_id: int) -> dict:
        correct, correct_answer = check_exercise_answer(exercise, answer)
        payload = parse_json_field(exercise.payload, {})
        word_ids = [
            sw.word_id
            for sw in session.query(ScenarioWord).filter(ScenarioWord.scenario_id == exercise.scenario_id).all()
        ]
        familiarity_updates = []
        for word_id in word_ids[:3]:
            progress = self._record_answer.execute_in_session(
                session,
                RecordAnswerInput(user_id=user_id, word_id=word_id, correct=correct),
            )
            familiarity_updates.append({"word_id": word_id, "familiarity": progress.familiarity})
        return {
            "correct": correct,
            "correct_answer": correct_answer,
            "explanation": payload.get("explanation"),
            "familiarity_updates": familiarity_updates,
        }


class SubmitBatchCommand:
    def __init__(
        self,
        uow_factory: UnitOfWorkFactory,
        submit_one: SubmitExerciseCommand,
        record_attempt: RecordScenarioAttemptCommand,
    ):
        self._uow_factory = uow_factory
        self._submit_one = submit_one
        self._record_attempt = record_attempt

    def execute(self, inp: SubmitBatchInput) -> dict:
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
            results = []
            correct_count = 0
            for ex in exercises:
                answer = inp.answers.get(ex.id, "")
                result = self._submit_one._grade(uow.session, ex, answer, inp.user_id)
                if result["correct"]:
                    correct_count += 1
                results.append(result)
            total = len(exercises)
            self._record_attempt.execute_in_session(
                uow.session,
                RecordScenarioAttemptInput(
                    user_id=inp.user_id,
                    scenario_id=inp.scenario_id,
                    total=total,
                    correct=correct_count,
                    timezone=inp.timezone,
                ),
            )
            uow.commit()
            return {
                "score": round(correct_count / total * 100, 1) if total else 0,
                "total": total,
                "correct": correct_count,
                "results": results,
            }
