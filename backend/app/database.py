from __future__ import annotations

import logging
from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, event, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings

logger = logging.getLogger(__name__)

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


class Base(DeclarativeBase):
    pass


def _sqlite_on_connect(dbapi_connection, _connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA busy_timeout=30000")
    cursor.close()


def ensure_engine() -> Engine:
    global _engine, _SessionLocal
    settings = get_settings()
    url = settings.database_url
    if _engine is not None and str(_engine.url) == url:
        return _engine

    if _engine is not None:
        _engine.dispose()
        _engine = None
        _SessionLocal = None

    connect_args: dict[str, object] = {}
    engine_kwargs: dict[str, object] = {}
    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        connect_args["timeout"] = 30
        if url.endswith(":memory:") or url.rstrip("/").endswith(":memory:"):
            engine_kwargs["poolclass"] = StaticPool

    _engine = create_engine(url, connect_args=connect_args, **engine_kwargs)
    if url.startswith("sqlite"):
        event.listen(_engine, "connect", _sqlite_on_connect)
    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    return _engine


def get_engine() -> Engine:
    return ensure_engine()


def SessionLocal() -> Session:
    ensure_engine()
    assert _SessionLocal is not None
    return _SessionLocal()


def reset_engine_for_tests() -> None:
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionLocal = None


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def run_migrations() -> None:
    from alembic import command
    from alembic.config import Config

    backend_dir = Path(__file__).resolve().parents[1]
    cfg = Config(str(backend_dir / "alembic.ini"))
    command.upgrade(cfg, "head")
    logger.info("Database migrations applied (alembic upgrade head)")


def _column_not_null(engine: Engine, table: str, column: str) -> bool:
    insp = inspect(engine)
    if not insp.has_table(table):
        return False
    cols = {c["name"]: c for c in insp.get_columns(table)}
    col = cols.get(column)
    if not col:
        return False
    return not col.get("nullable", True)


_DEVICE_ID_NULLABLE_TABLES = (
    "conversation_sessions",
    "scenario_attempts",
    "scenarios",
    "user_word_progress",
    "learning_streaks",
)


def _needs_auth_migration(engine: Engine) -> bool:
    insp = inspect(engine)
    if not insp.has_table("users"):
        return False
    user_cols = {c["name"]: c for c in insp.get_columns("users")}
    if "display_name" not in user_cols:
        return True
    password_col = user_cols.get("hashed_password")
    if password_col and not password_col.get("nullable", True):
        return True
    if insp.has_table("user_word_progress"):
        progress_cols = {c["name"] for c in insp.get_columns("user_word_progress")}
        if "user_id" not in progress_cols:
            return True
    for table in _DEVICE_ID_NULLABLE_TABLES:
        if _column_not_null(engine, table, "device_id"):
            return True
    return False


def init_db() -> None:
    settings = get_settings()
    settings.media_dir.mkdir(parents=True, exist_ok=True)
    db_path = settings.database_url.replace("sqlite:///", "")
    if db_path and not db_path.startswith(":"):
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    from app import models  # noqa: F401

    engine = get_engine()

    if settings.testing:
        Base.metadata.create_all(bind=engine)
        return

    insp = inspect(engine)
    has_alembic = insp.has_table("alembic_version")
    if settings.use_migrations or has_alembic or _needs_auth_migration(engine):
        run_migrations()
        return

    Base.metadata.create_all(bind=engine)
