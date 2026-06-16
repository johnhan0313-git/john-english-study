from __future__ import annotations

from pathlib import Path


def seed_dir() -> Path:
    return Path(__file__).resolve().parent / "seed"
