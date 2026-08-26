from __future__ import annotations

from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parents[1]
_SEED_DIR = _BACKEND_DIR / "data"


def seed_dir() -> Path:
    """Canonical seed directory under backend/data."""
    return _SEED_DIR


def resolve_seed_path(filename: str) -> Path:
    return seed_dir() / filename
