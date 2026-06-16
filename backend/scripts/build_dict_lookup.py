"""Fetch open vocabulary sources into dictionary_entries (PostgreSQL)."""

from __future__ import annotations

import sys

from app.cli import cmd_seed_dictionary


def main() -> int:
    force = "--force" in sys.argv
    return cmd_seed_dictionary(force=force)


if __name__ == "__main__":
    raise SystemExit(main())
