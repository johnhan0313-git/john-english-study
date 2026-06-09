from __future__ import annotations

from fastapi import APIRouter

from app.config import ENV_FILE, get_settings
from app.schemas.common import AIConfigResponse, AIEndpointStatus, HealthResponse

router = APIRouter(tags=["common"])


@router.get("/health", response_model=HealthResponse)
def health():
    settings = get_settings()
    return HealthResponse(status="ok", app=settings.app_name)


def _endpoint_status(config) -> AIEndpointStatus:
    return AIEndpointStatus(
        base_url=config.base_url,
        model=config.model,
        has_api_key=bool(config.api_key),
        configured=config.is_configured,
    )


@router.get("/config/ai", response_model=AIConfigResponse)
def get_ai_config():
    settings = get_settings()
    llm = settings.llm_config()
    return AIConfigResponse(
        llm=_endpoint_status(llm),
        stt=_endpoint_status(settings.stt_config()),
        tts=_endpoint_status(settings.tts_config()),
        use_edge_tts=settings.use_edge_tts,
        using_mock=not llm.is_configured,
        env_files_loaded=[str(ENV_FILE)],
    )
