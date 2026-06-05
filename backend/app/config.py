from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "John English Study"
    debug: bool = False
    database_url: str = "sqlite:///./data/app.db"
    media_dir: Path = Path("./data/media")
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # OpenAI-compatible API
    ai_base_url: str = "https://api.openai.com/v1"
    ai_api_key: str = ""
    ai_model: str = "gpt-4o-mini"
    ai_tts_model: str = "tts-1"
    ai_tts_voice: str = "alloy"
    ai_stt_model: str = "whisper-1"
    use_edge_tts: bool = True

    # JWT (optional, for future multi-user)
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7

    # Scheduler
    daily_scenario_hour: int = 6
    daily_scenario_count: int = 3
    default_device_id: str = "default"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
