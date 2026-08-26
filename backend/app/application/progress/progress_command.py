from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domains.progress.progress_domain import WordProgressState, apply_answer
from app.domains.progress.progress_repository import ProgressRepository
from app.infrastructure.unit_of_work import UnitOfWorkFactory
from app.utils.time import utc_now


@dataclass(frozen=True)
class RecordAnswerInput:
    user_id: int
    word_id: int
    correct: bool


@dataclass(frozen=True)
class RecordScenarioAttemptInput:
    user_id: int
    scenario_id: int
    total: int
    correct: int
    details: dict | None = None
    timezone: str = "Asia/Shanghai"


class RecordAnswerCommand:
    def __init__(self, uow_factory: UnitOfWorkFactory, repository_factory: Any):
        self._uow_factory = uow_factory
        self._repository_factory = repository_factory

    def execute(self, inp: RecordAnswerInput, *, commit: bool = True) -> WordProgressState:
        with self._uow_factory() as uow:
            repo: ProgressRepository = self._repository_factory(uow.session)
            state = repo.get_word_progress(inp.user_id, inp.word_id)
            if state is None:
                state = WordProgressState(user_id=inp.user_id, word_id=inp.word_id)
                state = apply_answer(state, inp.correct, utc_now())
                repo.add_word_progress(state)
            else:
                state = apply_answer(state, inp.correct, utc_now())
                repo.save_word_progress(state)
            if commit:
                uow.commit()
            return state

    def execute_in_session(self, session, inp: RecordAnswerInput) -> WordProgressState:
        """Apply answer inside an already-open UoW session (no commit)."""
        repo: ProgressRepository = self._repository_factory(session)
        state = repo.get_word_progress(inp.user_id, inp.word_id)
        if state is None:
            state = WordProgressState(user_id=inp.user_id, word_id=inp.word_id)
            state = apply_answer(state, inp.correct, utc_now())
            return repo.add_word_progress(state)
        state = apply_answer(state, inp.correct, utc_now())
        repo.save_word_progress(state)
        return state


class RecordScenarioAttemptCommand:
    def __init__(self, uow_factory: UnitOfWorkFactory, repository_factory: Any):
        self._uow_factory = uow_factory
        self._repository_factory = repository_factory

    def execute(self, inp: RecordScenarioAttemptInput) -> None:
        with self._uow_factory() as uow:
            repo: ProgressRepository = self._repository_factory(uow.session)
            repo.add_scenario_attempt(
                scenario_id=inp.scenario_id,
                user_id=inp.user_id,
                total=inp.total,
                correct=inp.correct,
                details=inp.details,
            )
            repo.touch_streak(inp.user_id, inp.timezone)
            uow.commit()

    def execute_in_session(self, session, inp: RecordScenarioAttemptInput) -> None:
        repo: ProgressRepository = self._repository_factory(session)
        repo.add_scenario_attempt(
            scenario_id=inp.scenario_id,
            user_id=inp.user_id,
            total=inp.total,
            correct=inp.correct,
            details=inp.details,
        )
        repo.touch_streak(inp.user_id, inp.timezone)
