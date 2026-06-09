from __future__ import annotations

from fastapi.testclient import TestClient

from tests.auth_helpers import auth_headers, register_user


def test_register_and_login(client: TestClient):
    reg = register_user(client, username="alice", password="password123")
    assert reg["token_type"] == "bearer"
    assert reg["user"]["username"] == "alice"

    me = client.get("/api/auth/me", headers=auth_headers(reg["access_token"]))
    assert me.status_code == 200
    assert me.json()["username"] == "alice"

    login = client.post("/api/auth/login", json={"username": "alice", "password": "password123"})
    assert login.status_code == 200
    assert login.json()["user"]["id"] == reg["user"]["id"]


def test_register_duplicate_username(client: TestClient):
    register_user(client, username="bob")
    resp = client.post("/api/auth/register", json={"username": "bob", "password": "password123"})
    assert resp.status_code == 400


def test_progress_requires_auth(client: TestClient):
    resp = client.get("/api/progress/overview")
    assert resp.status_code == 401


def test_words_public_without_familiarity(client: TestClient):
    resp = client.get("/api/words?page=1&page_size=5")
    assert resp.status_code == 200
    for item in resp.json()["items"]:
        assert item["familiarity"] is None


def test_words_familiarity_with_auth(client: TestClient):
    data = register_user(client, username="words_user")
    resp = client.get("/api/words?page=1&page_size=5", headers=auth_headers(data["access_token"]))
    assert resp.status_code == 200
    assert "items" in resp.json()


def test_merge_device(client: TestClient):
    from app.database import SessionLocal
    from app.models.progress import UserWordProgress
    from app.models.word import Word

    db = SessionLocal()
    try:
        word = db.query(Word).first()
        assert word is not None
        db.add(UserWordProgress(device_id="merge-test-device", word_id=word.id, familiarity=3))
        db.commit()
    finally:
        db.close()

    data = register_user(client, username="merge_user")
    resp = client.post(
        "/api/auth/merge-device",
        json={"device_id": "merge-test-device"},
        headers=auth_headers(data["access_token"]),
    )
    assert resp.status_code == 200
    assert resp.json()["word_progress"] >= 1

    resp2 = client.post(
        "/api/auth/merge-device",
        json={"device_id": "merge-test-device"},
        headers=auth_headers(data["access_token"]),
    )
    assert resp2.status_code == 200
    assert resp2.json()["word_progress"] == 0
