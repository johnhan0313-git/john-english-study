from __future__ import annotations

import logging
from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings

logger = logging.getLogger(__name__)

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


class Base(DeclarativeBase):
    pass


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
        if url.endswith(":memory:") or url.rstrip("/").endswith(":memory:"):
            engine_kwargs["poolclass"] = StaticPool

    _engine = create_engine(url, connect_args=connect_args, **engine_kwargs)
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

    if settings.use_migrations:
        run_migrations()
        return

    if _needs_auth_migration(engine):
        logger.info("Legacy database detected; applying auth schema migration...")
        run_migrations()
        return

    Base.metadata.create_all(bind=engine)
