from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, common, conversations, exercises, progress, reference, scenario_complete, scenarios, words
from app.config import get_settings
from app.database import SessionLocal, init_db
from app.logging_config import configure_logging
from app.services.vocabulary.import_words import import_words

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


async def daily_scenario_job():
    settings = get_settings()
    db = SessionLocal()
    try:
        from app.models.user import User
        from app.services.scenario.service import ScenarioService

        service = ScenarioService(db, settings)
        users = db.query(User).filter(User.is_active.is_(True)).all()
        for user in users:
            await service.ensure_daily_scenarios(user.id)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(debug=settings.debug)
    init_db()

    llm = settings.llm_config()
    stt = settings.stt_config()
    tts = settings.tts_config()
    if not llm.is_configured:
        logger.warning(
            "LLM 未配置，场景生成将使用 Mock 固定内容。"
            "请在 backend/.env 中配置 AI_LLM_API_KEY 后重启后端。"
        )
    else:
        logger.info("LLM: %s model=%s", llm.base_url, llm.model)
    if stt.is_configured:
        logger.info("STT: %s model=%s", stt.base_url, stt.model)
    else:
        logger.warning("STT 未配置，口语评测将使用期望文本代替识别结果。")
    if settings.use_edge_tts:
        logger.info("TTS: Edge TTS（免费）")
    elif tts.is_configured:
        logger.info("TTS: %s model=%s", tts.base_url, tts.model)
    else:
        logger.warning("TTS 未配置，非 Edge TTS 时将无法生成音频。")

    if not settings.skip_startup_seed and settings.seed_on_startup:
        db = SessionLocal()
        try:
            import_words(db)
            from app.services.reference.import_reference import import_reference

            import_reference(db)
        finally:
            db.close()

    if settings.enable_scheduler:
        scheduler.add_job(
            daily_scenario_job,
            "cron",
            hour=settings.daily_scenario_hour,
            minute=0,
            id="daily_scenarios",
        )
        scheduler.start()
        logger.info("Scheduler started (daily scenarios at hour %s)", settings.daily_scenario_hour)

    yield

    if settings.enable_scheduler:
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
    app.include_router(auth.router, prefix="/api")
    app.include_router(words.router, prefix="/api")
    app.include_router(scenarios.router, prefix="/api")
    app.include_router(scenario_complete.router, prefix="/api")
    app.include_router(exercises.router, prefix="/api")
    app.include_router(progress.router, prefix="/api")
    app.include_router(reference.router, prefix="/api")
    app.include_router(conversations.router, prefix="/api")
    return app


app = create_app()
