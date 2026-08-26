from __future__ import annotations

from app.application.activity.activity_query import ActivityApplication, GetActivityOverviewQuery, GetActivityTimelineQuery
from app.database import SessionLocal
from app.infrastructure.persistence.activity.activity_repository_impl import (
    SqlAlchemyActivityReadRepository,
)
from app.infrastructure.unit_of_work import SqlAlchemyUnitOfWork


def build_activity_application() -> ActivityApplication:
    def uow_factory() -> SqlAlchemyUnitOfWork:
        return SqlAlchemyUnitOfWork(_session=SessionLocal())

    return ActivityApplication(
        overview=GetActivityOverviewQuery(uow_factory, SqlAlchemyActivityReadRepository),
        timeline=GetActivityTimelineQuery(uow_factory, SqlAlchemyActivityReadRepository),
    )
