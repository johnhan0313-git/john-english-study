from __future__ import annotations

from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parents[1]
_SEED_DIRS = (_BACKEND_DIR / "data", _BACKEND_DIR / "app" / "seed")


def seed_dir() -> Path:
    """Primary seed directory (app/seed); use resolve_seed_path for file lookup."""
    return _BACKEND_DIR / "app" / "seed"


def resolve_seed_path(filename: str) -> Path:
    for directory in _SEED_DIRS:
        path = directory / filename
        if path.is_file():
            return path
    return seed_dir() / filename
