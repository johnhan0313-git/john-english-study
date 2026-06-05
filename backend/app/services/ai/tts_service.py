from __future__ import annotations

import asyncio
from pathlib import Path

import edge_tts

from app.config import Settings
from app.services.ai.openai_provider import AIProviderError, get_tts_provider


async def generate_speech(text: str, output_path: Path, settings: Settings, voice: str = "en-US-AriaNeural") -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if settings.use_edge_tts:
        communicate = edge_tts.Communicate(text[:5000], voice)
        await communicate.save(str(output_path))
        return output_path

    provider = get_tts_provider(settings)
    if not provider:
        raise AIProviderError("TTS API key is not configured")
    audio = await provider.text_to_speech(text)
    output_path.write_bytes(audio)
    return output_path


def generate_speech_sync(text: str, output_path: Path, settings: Settings) -> Path:
    return asyncio.run(generate_speech(text, output_path, settings))
