from __future__ import annotations


def conversation_message_audio_key(session_id: int, message_id: int) -> str:
    return f"conversations/conversation_{session_id}_{message_id}.mp3"


def scenario_audio_key(scenario_id: int) -> str:
    return f"scenarios/scenario_{scenario_id}.mp3"


def word_audio_key(word_id: int) -> str:
    return f"words/word_{word_id}.mp3"


def normalize_stored_audio_key(stored_path: str | None, default_key: str) -> str:
    if not stored_path:
        return default_key
    normalized = stored_path.replace("\\", "/")
    if normalized.startswith(("/", "./")) or ":/" in normalized:
        return default_key
    return normalized.lstrip("/")
