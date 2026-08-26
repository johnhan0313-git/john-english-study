from __future__ import annotations

import os

from tests.env_helpers import assert_test_resource_isolation, load_backend_env

load_backend_env()

os.environ["TESTING"] = "1"
os.environ.setdefault("AUTH_EXPOSE_CODES", "true")
os.environ.setdefault("SMTP_HOST", "")
os.environ.setdefault("SMTP_FROM", "")
os.environ.setdefault("AI_LLM_API_KEY", "")
os.environ.setdefault("AI_STT_API_KEY", "")
os.environ.setdefault("AI_TTS_API_KEY", "")
os.environ.setdefault("ENABLE_SCHEDULER", "false")
os.environ.setdefault("SKIP_STARTUP_SEED", "true")

assert_test_resource_isolation()

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.composition.shared_composition import init_container, reset_container
from app.database import (
    SessionLocal,
    prepare_test_database,
    reset_engine_for_tests,
    reset_test_database,
)
from app.main import app
from app.models.dictionary import DictionaryEntry
from app.models.word import Word
from app.services.storage.factory import get_storage, reset_storage_for_tests
from app.services.storage.s3 import S3StorageBackend
from app.services.vocabulary.import_words import import_words
from app.services.vocabulary.seed_dictionary import seed_dictionary_entries


def _clear_test_storage() -> None:
    settings = get_settings()
    if settings.storage_backend != "s3":
        return
    storage = get_storage()
    if isinstance(storage, S3StorageBackend):
        storage.clear_bucket()


@pytest.fixture(scope="session", autouse=True)
def _session_test_seed():
    get_settings.cache_clear()
    reset_engine_for_tests()
    prepare_test_database()
    db = SessionLocal()
    try:
        if db.query(DictionaryEntry).count() == 0:
            seed_dictionary_entries(db)
        if db.query(Word).count() == 0:
            import_words(db)
            db.commit()
    finally:
        db.close()
    yield
    reset_engine_for_tests()
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def _fresh_test_database():
    get_settings.cache_clear()
    reset_engine_for_tests()
    reset_storage_for_tests()
    reset_container()
    reset_test_database()
    init_container(get_settings())
    _clear_test_storage()
    yield
    reset_engine_for_tests()
    reset_storage_for_tests()
    reset_container()
    get_settings.cache_clear()


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client
