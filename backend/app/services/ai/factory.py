from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends

from app.config import Settings, get_settings
from app.services.ai.openai_provider import (
    MockAIProvider,
    OpenAICompatibleProvider,
    get_llm_provider,
    get_stt_provider,
    get_tts_provider,
)


@dataclass(frozen=True)
class AIProviders:
    llm: OpenAICompatibleProvider | MockAIProvider
    stt: OpenAICompatibleProvider | None
    tts: OpenAICompatibleProvider | None


def build_providers(settings: Settings | None = None) -> AIProviders:
    cfg = settings or get_settings()
    return AIProviders(
        llm=get_llm_provider(cfg),
        stt=get_stt_provider(cfg),
        tts=get_tts_provider(cfg),
    )


def get_providers(settings: Settings = Depends(get_settings)) -> AIProviders:
    return build_providers(settings)
