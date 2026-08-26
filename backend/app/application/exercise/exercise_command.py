from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.application.progress.progress_command import (
    RecordAnswerCommand,
    RecordAnswerInput,
    RecordScenarioAttemptCommand,
    RecordScenarioAttemptInput,
)
from app.domains.exercise.exercise_repository import ExerciseRecord, ExerciseRepository
from app.infrastructure.unit_of_work import UnitOfWorkFactory


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


def _normalize_answer(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def grade_exercise(exercise: ExerciseRecord, answer: str | list[str]) -> tuple[bool, str | list[str]]:
    """Pure grading over plain exercise data (no ORM)."""
    payload = exercise.payload or {}
    answer_key = exercise.answer_key or {}

    if exercise.type == "single_choice":
        correct = answer_key.get("correct_label", "A")
        user = str(answer).strip().upper()
        return user == correct.upper(), correct

    if exercise.type == "fill_blank":
        blanks = answer_key.get("blanks", payload.get("blanks", []))
        if isinstance(answer, str):
            user_answers = [answer]
        else:
            user_answers = answer

        if len(blanks) == 1 and len(user_answers) == 1:
            accept = blanks[0].get("accept", [blanks[0].get("answer", "")])
            normalized = _normalize_answer(user_answers[0])
            correct = any(normalized == _normalize_answer(a) for a in accept)
            return correct, blanks[0].get("answer", "")

        correct_answers = []
        all_correct = True
        for i, blank in enumerate(blanks):
            accept = blank.get("accept", [blank.get("answer", "")])
            user_val = user_answers[i] if i < len(user_answers) else ""
            normalized = _normalize_answer(user_val)
            match = any(normalized == _normalize_answer(a) for a in accept)
            if not match:
                all_correct = False
            correct_answers.append(blank.get("answer", ""))
        return all_correct, correct_answers

    return False, ""


class SubmitExerciseCommand:
    def __init__(
        self,
        uow_factory: UnitOfWorkFactory,
        exercise_repository_factory: Any,
        record_answer: RecordAnswerCommand,
    ):
        self._uow_factory = uow_factory
        self._exercise_repository_factory = exercise_repository_factory
        self._record_answer = record_answer

    def execute(self, inp: SubmitExerciseInput) -> dict:
        with self._uow_factory() as uow:
            exercise_repo: ExerciseRepository = self._exercise_repository_factory(uow.session)
            exercise = exercise_repo.get_owned_by_id(inp.user_id, inp.exercise_id)
            if not exercise:
                raise ValueError("Exercise not found")
            result = self._grade(uow.session, exercise_repo, exercise, inp.answer, inp.user_id)
            uow.commit()
            return result

    def _grade(
        self,
        session,
        exercise_repo: ExerciseRepository,
        exercise: ExerciseRecord,
        answer: str | list[str],
        user_id: int,
    ) -> dict:
        correct, correct_answer = grade_exercise(exercise, answer)
        word_ids = exercise_repo.list_scenario_word_ids(exercise.scenario_id)
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
            "explanation": (exercise.payload or {}).get("explanation"),
            "familiarity_updates": familiarity_updates,
        }


class SubmitBatchCommand:
    def __init__(
        self,
        uow_factory: UnitOfWorkFactory,
        exercise_repository_factory: Any,
        submit_one: SubmitExerciseCommand,
        record_attempt: RecordScenarioAttemptCommand,
    ):
        self._uow_factory = uow_factory
        self._exercise_repository_factory = exercise_repository_factory
        self._submit_one = submit_one
        self._record_attempt = record_attempt

    def execute(self, inp: SubmitBatchInput) -> dict:
        with self._uow_factory() as uow:
            exercise_repo: ExerciseRepository = self._exercise_repository_factory(uow.session)
            exercises = exercise_repo.list_owned_scenario_exercises(inp.user_id, inp.scenario_id)
            if exercises is None:
                raise ValueError("Scenario not found")
            results = []
            correct_count = 0
            for ex in exercises:
                answer = inp.answers.get(ex.id, "")
                result = self._submit_one._grade(
                    uow.session, exercise_repo, ex, answer, inp.user_id
                )
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
