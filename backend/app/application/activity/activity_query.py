from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domains.activity.activity_repository import ActivityReadRepository
from app.infrastructure.unit_of_work import UnitOfWorkFactory


@dataclass(frozen=True)
class GetActivityOverviewInput:
    user_id: int
    timezone: str


@dataclass(frozen=True)
class GetActivityTimelineInput:
    user_id: int
    timezone: str
    skip: int = 0
    limit: int = 30


class GetActivityOverviewQuery:
    def __init__(self, uow_factory: UnitOfWorkFactory, repository_factory: Any):
        self._uow_factory = uow_factory
        self._repository_factory = repository_factory

    def execute(self, inp: GetActivityOverviewInput) -> dict[str, Any]:
        with self._uow_factory() as uow:
            repo: ActivityReadRepository = self._repository_factory(
                uow.session, timezone=inp.timezone
            )
            return repo.get_overview(inp.user_id)


class GetActivityTimelineQuery:
    def __init__(self, uow_factory: UnitOfWorkFactory, repository_factory: Any):
        self._uow_factory = uow_factory
        self._repository_factory = repository_factory

    def execute(self, inp: GetActivityTimelineInput) -> tuple[list[dict], int]:
        with self._uow_factory() as uow:
            repo: ActivityReadRepository = self._repository_factory(
                uow.session, timezone=inp.timezone
            )
            return repo.get_timeline(inp.user_id, skip=inp.skip, limit=inp.limit)


@dataclass
class ActivityApplication:
    overview: GetActivityOverviewQuery
    timeline: GetActivityTimelineQuery
