from __future__ import annotations

from pathlib import Path

from app.config import Settings, get_settings


def get_data_dir(settings: Settings | None = None) -> Path:
    return (settings or get_settings()).data_dir
