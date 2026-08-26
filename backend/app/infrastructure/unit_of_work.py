from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Protocol

from sqlalchemy.orm import Session


class UnitOfWork(Protocol):
    """Application-owned transaction boundary. Infrastructure owns the Session."""

    @property
    def session(self) -> Session: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...


@dataclass
class SqlAlchemyUnitOfWork(AbstractContextManager["SqlAlchemyUnitOfWork"]):
    """Request/operation-scoped UoW wrapping a SQLAlchemy Session."""

    _session: Session
    _committed: bool = False

    @property
    def session(self) -> Session:
        return self._session

    def commit(self) -> None:
        self._session.commit()
        self._committed = True

    def rollback(self) -> None:
        self._session.rollback()

    def __enter__(self) -> SqlAlchemyUnitOfWork:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            if exc_type is not None and not self._committed:
                self._session.rollback()
        finally:
            self._session.close()


class UnitOfWorkFactory(Protocol):
    def __call__(self) -> SqlAlchemyUnitOfWork: ...
