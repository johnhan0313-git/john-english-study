from __future__ import annotations

from app.config import Settings, get_settings
from app.services.ai.openai_provider import AIProviderError
from app.services.ai.tts_service import generate_speech_bytes
from app.services.media.audio_paths import (
    conversation_message_audio_key,
    normalize_stored_audio_key,
    scenario_audio_key,
    word_audio_key,
)
from app.services.storage.factory import get_storage


async def materialize_conversation_message_audio(
    session_id: int,
    message_id: int,
    text: str,
    settings: Settings | None = None,
) -> str:
    """Generate and store TTS audio if missing; return storage key."""
    cfg = settings or get_settings()
    key = conversation_message_audio_key(session_id, message_id)
    storage = get_storage(cfg)
    try:
        if not storage.exists(key):
            audio = await generate_speech_bytes(text[:500], cfg)
            storage.put_bytes(key, audio, "audio/mpeg")
    except AIProviderError:
        raise
    except Exception as exc:
        raise AIProviderError(f"Conversation audio failed: {exc}") from exc
    return key


async def materialize_scenario_audio(
    scenario_id: int,
    text: str,
    settings: Settings | None = None,
    stored_path: str | None = None,
) -> str:
    cfg = settings or get_settings()
    default_key = scenario_audio_key(scenario_id)
    key = normalize_stored_audio_key(stored_path, default_key)
    storage = get_storage(cfg)
    if not storage.exists(key):
        audio = await generate_speech_bytes(text, cfg)
        storage.put_bytes(key, audio, "audio/mpeg")
        return default_key
    return key


async def materialize_word_audio(
    word_id: int,
    lemma: str,
    settings: Settings | None = None,
) -> str:
    cfg = settings or get_settings()
    key = word_audio_key(word_id)
    storage = get_storage(cfg)
    if not storage.exists(key):
        audio = await generate_speech_bytes(lemma, cfg)
        storage.put_bytes(key, audio, "audio/mpeg")
    return key
