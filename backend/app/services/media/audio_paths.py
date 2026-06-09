from __future__ import annotations

from pathlib import Path

from app.config import Settings, get_settings


def conversation_message_audio_path(session_id: int, message_id: int, settings: Settings | None = None) -> Path:
    cfg = settings or get_settings()
    return cfg.media_dir / "conversations" / f"conversation_{session_id}_{message_id}.mp3"


def scenario_audio_path(scenario_id: int, settings: Settings | None = None) -> Path:
    cfg = settings or get_settings()
    return cfg.media_dir / "scenarios" / f"scenario_{scenario_id}.mp3"
