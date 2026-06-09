from __future__ import annotations

import os

# Must run before any app imports so Settings and engine use test configuration.
os.environ["TESTING"] = "1"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["AI_LLM_API_KEY"] = ""
os.environ["AI_STT_API_KEY"] = ""
os.environ["AI_TTS_API_KEY"] = ""
os.environ["ENABLE_SCHEDULER"] = "false"
os.environ["SKIP_STARTUP_SEED"] = "true"

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.database import SessionLocal, init_db, reset_engine_for_tests
from app.main import app
from app.services.vocabulary.import_words import import_words


@pytest.fixture(autouse=True)
def _fresh_test_database():
    get_settings.cache_clear()
    reset_engine_for_tests()
    init_db()
    db = SessionLocal()
    try:
        import_words(db)
    finally:
        db.close()
    yield
    reset_engine_for_tests()
    get_settings.cache_clear()


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client
