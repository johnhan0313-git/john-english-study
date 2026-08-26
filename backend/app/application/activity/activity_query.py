from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.database import SessionLocal
from app.infrastructure.unit_of_work import SqlAlchemyUnitOfWork, UnitOfWorkFactory
from app.services.activity.service import ActivityService


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
    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

    def execute(self, inp: GetActivityOverviewInput) -> dict[str, Any]:
        with self._uow_factory() as uow:
            service = ActivityService(uow.session, timezone=inp.timezone)
            return service.get_overview(inp.user_id)


class GetActivityTimelineQuery:
    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

    def execute(self, inp: GetActivityTimelineInput) -> tuple[list[dict], int]:
        with self._uow_factory() as uow:
            service = ActivityService(uow.session, timezone=inp.timezone)
            return service.get_timeline(inp.user_id, skip=inp.skip, limit=inp.limit)


@dataclass
class ActivityApplication:
    overview: GetActivityOverviewQuery
    timeline: GetActivityTimelineQuery


def build_activity_application() -> ActivityApplication:
    def uow_factory() -> SqlAlchemyUnitOfWork:
        return SqlAlchemyUnitOfWork(_session=SessionLocal())

    return ActivityApplication(
        overview=GetActivityOverviewQuery(uow_factory),
        timeline=GetActivityTimelineQuery(uow_factory),
    )
