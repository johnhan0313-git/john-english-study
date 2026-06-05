from __future__ import annotations

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str = "0.1.0"


class AIEndpointStatus(BaseModel):
    base_url: str
    model: str
    has_api_key: bool
    configured: bool


class AIConfigUpdate(BaseModel):
    base_url: str | None = None
    api_key: str | None = None
    model: str | None = None
    use_edge_tts: bool | None = None


class AIConfigResponse(BaseModel):
    llm: AIEndpointStatus
    stt: AIEndpointStatus
    tts: AIEndpointStatus
    use_edge_tts: bool
    using_mock: bool = False
    env_files_loaded: list[str] = []
