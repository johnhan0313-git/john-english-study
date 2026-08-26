from __future__ import annotations

from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.application.scenario.scenario_command import aggregate_to_brief, aggregate_to_detail
from app.application.scenario.scenario_input import (
    DailyScenariosOutput,
    GetDailyScenariosInput,
    GetScenarioInput,
    ListScenariosInput,
    ScenarioDetailOutput,
    ScenarioListOutput,
)
from app.domains.scenario.scenario_repository import ScenarioRepository
from app.infrastructure.unit_of_work import UnitOfWorkFactory
from app.models.conversation import ConversationSession
from app.models.progress import ScenarioAttempt


class GetDailyScenariosQuery:
    """Read-only: list existing daily scenarios for a date. No generation side effects."""

    def __init__(self, uow_factory: UnitOfWorkFactory, repository_factory: Any):
        self._uow_factory = uow_factory
        self._repository_factory = repository_factory

    def execute(self, inp: GetDailyScenariosInput) -> DailyScenariosOutput:
        with self._uow_factory() as uow:
            repo: ScenarioRepository = self._repository_factory(uow.session)
            items = repo.list_daily(inp.user_id, inp.daily_date)
            return DailyScenariosOutput(
                date=inp.daily_date,
                items=[aggregate_to_brief(s) for s in items],
                generated=False,
            )


class GetScenarioQuery:
    def __init__(self, uow_factory: UnitOfWorkFactory, repository_factory: Any):
        self._uow_factory = uow_factory
        self._repository_factory = repository_factory

    def execute(self, inp: GetScenarioInput) -> ScenarioDetailOutput | None:
        with self._uow_factory() as uow:
            repo: ScenarioRepository = self._repository_factory(uow.session)
            scenario = repo.get_by_id(inp.scenario_id, inp.user_id)
            if not scenario:
                return None
            return aggregate_to_detail(scenario)


class ListScenariosQuery:
    def __init__(self, uow_factory: UnitOfWorkFactory, repository_factory: Any):
        self._uow_factory = uow_factory
        self._repository_factory = repository_factory

    def execute(self, inp: ListScenariosInput) -> ScenarioListOutput:
        with self._uow_factory() as uow:
            repo: ScenarioRepository = self._repository_factory(uow.session)
            items, total = repo.list_by_user(inp.user_id, inp.skip, inp.limit)
            briefs = self._enrich_briefs(uow.session, inp.user_id, items)
            return ScenarioListOutput(items=briefs, total=total)

    def _enrich_briefs(self, session: Session, user_id: int, scenarios: list) -> list:
        if not scenarios:
            return []
        scenario_ids = [s.id for s in scenarios if s.id is not None]
        attempt_rows = (
            session.query(
                ScenarioAttempt.scenario_id,
                func.max(
                    ScenarioAttempt.correct_questions
                    * 1.0
                    / func.nullif(ScenarioAttempt.total_questions, 0)
                ).label("best_score"),
                func.count(ScenarioAttempt.id).label("attempt_count"),
            )
            .filter(ScenarioAttempt.user_id == user_id, ScenarioAttempt.scenario_id.in_(scenario_ids))
            .group_by(ScenarioAttempt.scenario_id)
            .all()
        )
        attempt_map = {row.scenario_id: row for row in attempt_rows}
        conv_counts = (
            session.query(ConversationSession.scenario_id, func.count(ConversationSession.id))
            .filter(
                ConversationSession.user_id == user_id,
                ConversationSession.scenario_id.in_(scenario_ids),
            )
            .group_by(ConversationSession.scenario_id)
            .all()
        )
        conv_map = dict(conv_counts)
        result = []
        for scenario in scenarios:
            attempt = attempt_map.get(scenario.id)
            best_score = float(attempt.best_score) if attempt and attempt.best_score is not None else None
            is_completed = attempt is not None and attempt.attempt_count > 0
            result.append(
                aggregate_to_brief(
                    scenario,
                    best_score=best_score,
                    is_completed=is_completed,
                    conversation_count=conv_map.get(scenario.id, 0),
                )
            )
        return result
