from __future__ import annotations

from pathlib import Path

from app.config import Settings, get_settings
from app.services.ai.tts_service import generate_speech
from app.services.media.audio_paths import conversation_message_audio_path, scenario_audio_path


async def ensure_conversation_message_audio(
    session_id: int,
    message_id: int,
    text: str,
    settings: Settings | None = None,
) -> Path:
    cfg = settings or get_settings()
    audio_path = conversation_message_audio_path(session_id, message_id, cfg)
    if not audio_path.exists():
        audio_path.parent.mkdir(parents=True, exist_ok=True)
        await generate_speech(text[:500], audio_path, cfg)
    return audio_path


async def ensure_scenario_audio(
    scenario_id: int,
    text: str,
    settings: Settings | None = None,
    stored_path: str | None = None,
) -> Path:
    cfg = settings or get_settings()
    if stored_path:
        path = Path(stored_path)
        if path.exists():
            return path
    audio_path = scenario_audio_path(scenario_id, cfg)
    if not audio_path.exists():
        audio_path.parent.mkdir(parents=True, exist_ok=True)
        await generate_speech(text, audio_path, cfg)
    return audio_path
