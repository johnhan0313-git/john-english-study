from __future__ import annotations

from dataclasses import dataclass

from app.application.exercise.exercise_command import SubmitBatchCommand, SubmitExerciseCommand
from app.application.progress.progress_command import RecordAnswerCommand, RecordScenarioAttemptCommand
from app.database import SessionLocal
from app.infrastructure.persistence.progress.progress_repository_impl import SqlAlchemyProgressRepository
from app.infrastructure.unit_of_work import SqlAlchemyUnitOfWork


def _uow_factory() -> SqlAlchemyUnitOfWork:
    return SqlAlchemyUnitOfWork(_session=SessionLocal())


@dataclass
class ProgressApplication:
    record_answer: RecordAnswerCommand
    record_scenario_attempt: RecordScenarioAttemptCommand


@dataclass
class ExerciseApplication:
    submit: SubmitExerciseCommand
    submit_batch: SubmitBatchCommand


def build_progress_application() -> ProgressApplication:
    record_answer = RecordAnswerCommand(_uow_factory, SqlAlchemyProgressRepository)
    record_attempt = RecordScenarioAttemptCommand(_uow_factory, SqlAlchemyProgressRepository)
    return ProgressApplication(record_answer=record_answer, record_scenario_attempt=record_attempt)


def build_exercise_application(progress: ProgressApplication) -> ExerciseApplication:
    submit = SubmitExerciseCommand(_uow_factory, progress.record_answer)
    batch = SubmitBatchCommand(_uow_factory, submit, progress.record_scenario_attempt)
    return ExerciseApplication(submit=submit, submit_batch=batch)
