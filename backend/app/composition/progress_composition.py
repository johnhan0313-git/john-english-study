from __future__ import annotations

from dataclasses import dataclass

from app.application.exercise.exercise_command import SubmitBatchCommand, SubmitExerciseCommand
from app.application.progress.ability_command import (
    EvaluateSpeakingCommand,
    EvaluateWritingCommand,
    GenerateWritingSampleCommand,
)
from app.application.progress.progress_command import RecordAnswerCommand, RecordScenarioAttemptCommand
from app.application.progress.progress_query import (
    GetProgressOverviewQuery,
    GetReviewWordsQuery,
    ListExercisesQuery,
)
from app.config import Settings, get_settings
from app.database import SessionLocal
from app.infrastructure.persistence.exercise.exercise_repository_impl import SqlAlchemyExerciseRepository
from app.infrastructure.persistence.progress.progress_repository_impl import SqlAlchemyProgressRepository
from app.infrastructure.unit_of_work import SqlAlchemyUnitOfWork


def _uow_factory() -> SqlAlchemyUnitOfWork:
    return SqlAlchemyUnitOfWork(_session=SessionLocal())


@dataclass
class ProgressApplication:
    record_answer: RecordAnswerCommand
    record_scenario_attempt: RecordScenarioAttemptCommand
    overview: GetProgressOverviewQuery
    review_words: GetReviewWordsQuery
    evaluate_writing: EvaluateWritingCommand
    generate_writing_sample: GenerateWritingSampleCommand
    evaluate_speaking: EvaluateSpeakingCommand


@dataclass
class ExerciseApplication:
    submit: SubmitExerciseCommand
    submit_batch: SubmitBatchCommand
    list_for_scenario: ListExercisesQuery


def build_progress_application(settings: Settings | None = None) -> ProgressApplication:
    cfg = settings or get_settings()
    record_answer = RecordAnswerCommand(_uow_factory, SqlAlchemyProgressRepository)
    record_attempt = RecordScenarioAttemptCommand(_uow_factory, SqlAlchemyProgressRepository)
    return ProgressApplication(
        record_answer=record_answer,
        record_scenario_attempt=record_attempt,
        overview=GetProgressOverviewQuery(_uow_factory, SqlAlchemyProgressRepository),
        review_words=GetReviewWordsQuery(_uow_factory, SqlAlchemyProgressRepository),
        evaluate_writing=EvaluateWritingCommand(cfg),
        generate_writing_sample=GenerateWritingSampleCommand(cfg),
        evaluate_speaking=EvaluateSpeakingCommand(),
    )


def build_exercise_application(progress: ProgressApplication) -> ExerciseApplication:
    submit = SubmitExerciseCommand(
        _uow_factory, SqlAlchemyExerciseRepository, progress.record_answer
    )
    batch = SubmitBatchCommand(
        _uow_factory,
        SqlAlchemyExerciseRepository,
        submit,
        progress.record_scenario_attempt,
    )
    return ExerciseApplication(
        submit=submit,
        submit_batch=batch,
        list_for_scenario=ListExercisesQuery(_uow_factory, SqlAlchemyExerciseRepository),
    )
