from __future__ import annotations

from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import common, exercises, progress, scenario_complete, scenarios, words
from app.config import get_settings
from app.database import SessionLocal, init_db
from app.services.vocabulary.import_words import import_words


scheduler = AsyncIOScheduler()


async def daily_scenario_job():
    settings = get_settings()
    db = SessionLocal()
    try:
        from app.services.scenario.service import ScenarioService

        service = ScenarioService(db, settings)
        await service.ensure_daily_scenarios(settings.default_device_id)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    init_db()
    if not settings.ai_api_key:
        print(
            "[WARN] AI_API_KEY 未加载，场景生成将使用 Mock 固定内容（A Day at the Airport）。"
            " 请在 backend/.env 中配置 AI_API_KEY 后重启后端。"
        )
    else:
        print(f"[INFO] AI 已配置: {settings.ai_base_url} model={settings.ai_model}")
    db = SessionLocal()
    try:
        import_words(db)
    finally:
        db.close()

    scheduler.add_job(
        daily_scenario_job,
        "cron",
        hour=settings.daily_scenario_hour,
        minute=0,
        id="daily_scenarios",
    )
    scheduler.start()
    yield
    scheduler.shutdown()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(common.router, prefix="/api")
    app.include_router(words.router, prefix="/api")
    app.include_router(scenarios.router, prefix="/api")
    app.include_router(scenario_complete.router, prefix="/api")
    app.include_router(exercises.router, prefix="/api")
    app.include_router(progress.router, prefix="/api")
    return app


app = create_app()
