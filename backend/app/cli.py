from __future__ import annotations

import argparse
import asyncio
import sys

from app.config import get_settings
from app.database import SessionLocal, init_db
from app.logging_config import configure_logging
from app.services.vocabulary.ensure_data import ensure_data_files
from app.services.vocabulary.import_words import import_words


def cmd_ensure_data() -> int:
    result = ensure_data_files()
    print(f"Data files: {result}")
    return 0


def cmd_seed() -> int:
    init_db()
    db = SessionLocal()
    try:
        result = import_words(db)
        from app.services.reference.import_reference import import_reference

        ref = import_reference(db)
        print(f"Seed complete: {result}, reference: {ref}")
    finally:
        db.close()
    return 0


async def cmd_daily_scenarios() -> int:
    settings = get_settings()
    db = SessionLocal()
    try:
        from app.models.user import User
        from app.services.scenario.service import ScenarioService

        service = ScenarioService(db, settings)
        users = db.query(User).filter(User.is_active.is_(True)).all()
        for user in users:
            await service.ensure_daily_scenarios(user.id)
        print(f"Daily scenarios ensured for {len(users)} user(s).")
    finally:
        db.close()
    return 0


def main(argv: list[str] | None = None) -> int:
    configure_logging(debug=get_settings().debug)
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("ensure-data", help="Ensure backend/data files exist (downloads dict_lookup if missing)")
    sub.add_parser("seed", help="Import vocabulary and reference data")
    sub.add_parser("daily-scenarios", help="Run daily scenario generation once")
    args = parser.parse_args(argv)

    if args.command == "ensure-data":
        return cmd_ensure_data()
    if args.command == "seed":
        return cmd_seed()
    if args.command == "daily-scenarios":
        return asyncio.run(cmd_daily_scenarios())
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
