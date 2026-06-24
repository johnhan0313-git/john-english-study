from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

import edge_tts

from app.config import Settings
from app.services.ai.openai_provider import AIProviderError, get_tts_provider


async def generate_speech_bytes(
    text: str,
    settings: Settings,
    voice: str = "en-US-AriaNeural",
    rate: str | None = None,
) -> bytes:
    if settings.use_edge_tts:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            output_path = Path(tmp.name)
        try:
            kwargs: dict[str, str] = {"text": text[:5000], "voice": voice}
            if rate:
                kwargs["rate"] = rate
            communicate = edge_tts.Communicate(**kwargs)
            await communicate.save(str(output_path))
            return output_path.read_bytes()
        except Exception as exc:
            raise AIProviderError(f"Edge TTS failed: {exc}") from exc
        finally:
            output_path.unlink(missing_ok=True)

    provider = get_tts_provider(settings)
    if not provider:
        raise AIProviderError("TTS API key is not configured")
    return await provider.text_to_speech(text)


def generate_speech_bytes_sync(text: str, settings: Settings) -> bytes:
    return asyncio.run(generate_speech_bytes(text, settings))
