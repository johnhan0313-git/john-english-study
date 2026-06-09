from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parents[1]
ENV_FILE = _BACKEND_DIR / ".env"


@dataclass(frozen=True)
class AIEndpointConfig:
    base_url: str
    api_key: str
    model: str
    voice: str = ""

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key.strip())


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "John English Study"
    debug: bool = False
    testing: bool = False
    database_url: str = "sqlite:///./data/app.db"
    media_dir: Path = Path("./data/media")
    use_migrations: bool = False
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    ai_llm_base_url: str = "https://api.openai.com/v1"
    ai_llm_api_key: str = ""
    ai_llm_model: str = "gpt-4o-mini"

    ai_stt_base_url: str = "https://api.openai.com/v1"
    ai_stt_api_key: str = ""
    ai_stt_model: str = "whisper-1"

    ai_tts_base_url: str = "https://api.openai.com/v1"
    ai_tts_api_key: str = ""
    ai_tts_model: str = "tts-1"
    ai_tts_voice: str = "alloy"
    use_edge_tts: bool = True

    # JWT (optional, for future multi-user)
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7

    # Email OTP
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False
    email_code_expire_minutes: int = 10
    email_code_cooldown_seconds: int = 60
    auth_expose_codes: bool = False

    # WeChat OAuth (网站应用扫码登录)
    wechat_app_id: str = ""
    wechat_app_secret: str = ""
    wechat_redirect_uri: str = ""
    frontend_base_url: str = "http://localhost:3000"

    # Scheduler / startup
    daily_scenario_hour: int = 6
    daily_scenario_count: int = 3
    default_device_id: str = "default"
    enable_scheduler: bool = True
    skip_startup_seed: bool = False
    seed_on_startup: bool = True
    app_timezone: str = "Asia/Shanghai"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def smtp_configured(self) -> bool:
        return bool(self.smtp_host and self.smtp_from)

    def llm_config(self) -> AIEndpointConfig:
        return AIEndpointConfig(
            base_url=self.ai_llm_base_url.rstrip("/"),
            api_key=self.ai_llm_api_key,
            model=self.ai_llm_model,
        )

    def stt_config(self) -> AIEndpointConfig:
        return AIEndpointConfig(
            base_url=self.ai_stt_base_url.rstrip("/"),
            api_key=self.ai_stt_api_key,
            model=self.ai_stt_model,
        )

    def tts_config(self) -> AIEndpointConfig:
        return AIEndpointConfig(
            base_url=self.ai_tts_base_url.rstrip("/"),
            api_key=self.ai_tts_api_key,
            model=self.ai_tts_model,
            voice=self.ai_tts_voice,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
