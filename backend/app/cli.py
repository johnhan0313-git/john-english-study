from __future__ import annotations

import argparse
import asyncio
import sys

from app.config import get_settings
from app.database import SessionLocal, init_db
from app.logging_config import configure_logging
from app.services.vocabulary.import_words import import_words
from app.services.vocabulary.theme_tags import sync_all_theme_tags
from app.services.vocabulary.seed_dictionary import seed_dictionary_entries


def cmd_seed_dictionary(force: bool = False) -> int:
    init_db()
    db = SessionLocal()
    try:
        result = seed_dictionary_entries(db, force=force)
        print(f"Dictionary seed: {result}")
    finally:
        db.close()
    return 0


def cmd_sync_theme_tags() -> int:
    init_db()
    db = SessionLocal()
    try:
        result = sync_all_theme_tags(db)
        print(f"Theme tags synced: {result}")
    finally:
        db.close()
    return 0


def cmd_seed() -> int:
    init_db()
    db = SessionLocal()
    try:
        seed_dictionary_entries(db)
        result = import_words(db)
        from app.services.reference.import_reference import import_reference

        ref = import_reference(db)
        print(f"Seed complete: {result}, reference: {ref}")
    finally:
        db.close()
    return 0


async def cmd_daily_scenarios() -> int:
    settings = get_settings()
    init_db()
    from app.application.scenario.scenario_input import CreateMissingDailySlotsInput
    from app.composition.shared_composition import init_container
    from app.models.user import User
    from app.utils.time import local_today

    container = init_container(settings)
    db = SessionLocal()
    try:
        users = db.query(User).filter(User.is_active.is_(True)).all()
        today = local_today(settings.app_timezone).isoformat()
        for user in users:
            await container.scenario.create_missing_daily_slots.execute(
                CreateMissingDailySlotsInput(
                    user_id=user.id,
                    daily_date=today,
                    target_count=settings.daily_scenario_count,
                )
            )
        print(f"Daily scenarios created for {len(users)} user(s).")
    finally:
        db.close()
    return 0


def main(argv: list[str] | None = None) -> int:
    configure_logging(debug=get_settings().debug)
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    sub = parser.add_subparsers(dest="command", required=True)

    dict_parser = sub.add_parser(
        "seed-dictionary",
        help="Import dictionary_entries from open vocabulary sources (skips if table non-empty)",
    )
    dict_parser.add_argument(
        "--force",
        action="store_true",
        help="Re-fetch and upsert all dictionary entries",
    )

    sub.add_parser("seed", help="Import dictionary, vocabulary and reference data")
    sub.add_parser("sync-theme-tags", help="Infer and apply theme WordTags for the full vocabulary")
    sub.add_parser("daily-scenarios", help="Run daily scenario generation once")
    args = parser.parse_args(argv)

    if args.command == "seed-dictionary":
        return cmd_seed_dictionary(force=args.force)
    if args.command == "seed":
        return cmd_seed()
    if args.command == "sync-theme-tags":
        return cmd_sync_theme_tags()
    if args.command == "daily-scenarios":
        return asyncio.run(cmd_daily_scenarios())
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
