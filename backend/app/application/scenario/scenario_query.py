from __future__ import annotations

from typing import Any

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
            briefs = self._enrich_briefs(repo, inp.user_id, items)
            return ScenarioListOutput(items=briefs, total=total)

    def _enrich_briefs(self, repo: ScenarioRepository, user_id: int, scenarios: list) -> list:
        if not scenarios:
            return []
        scenario_ids = [s.id for s in scenarios if s.id is not None]
        enrichment = repo.list_enrichment(user_id, scenario_ids)
        result = []
        for scenario in scenarios:
            stats = enrichment.get(scenario.id)
            best_score = stats.best_score if stats else None
            is_completed = bool(stats and stats.attempt_count > 0)
            conversation_count = stats.conversation_count if stats else 0
            result.append(
                aggregate_to_brief(
                    scenario,
                    best_score=best_score,
                    is_completed=is_completed,
                    conversation_count=conversation_count,
                )
            )
        return result
