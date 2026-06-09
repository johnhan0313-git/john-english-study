from __future__ import annotations

from fastapi.testclient import TestClient

from tests.auth_helpers import auth_headers, login_user


def test_email_login_and_me(client: TestClient):
    reg = login_user(client, email="alice@example.com")
    assert reg["token_type"] == "bearer"
    assert reg["user"]["email"] == "alice@example.com"

    me = client.get("/api/auth/me", headers=auth_headers(reg["access_token"]))
    assert me.status_code == 200
    assert me.json()["email"] == "alice@example.com"

    again = login_user(client, email="alice@example.com")
    assert again["user"]["id"] == reg["user"]["id"]


def test_email_login_auto_register(client: TestClient):
    first = login_user(client, email="bob@example.com")
    assert first["user"]["email"] == "bob@example.com"


def test_login_invalid_captcha(client: TestClient):
    send = client.post("/api/auth/email/send-code", json={"email": "bad@example.com"})
    assert send.status_code == 200
    code = send.json()["dev_code"]

    cap = client.get("/api/auth/captcha")
    assert cap.status_code == 200
    resp = client.post(
        "/api/auth/email/login",
        json={
            "email": "bad@example.com",
            "code": code,
            "captcha_id": cap.json()["captcha_id"],
            "captcha_x": 0,
        },
    )
    assert resp.status_code == 400

    # 拼图失败不应消耗邮箱验证码
    cap2 = client.get("/api/auth/captcha")
    resp2 = client.post(
        "/api/auth/email/login",
        json={
            "email": "bad@example.com",
            "code": code,
            "captcha_id": cap2.json()["captcha_id"],
            "captcha_x": int(cap2.json()["dev_answer"]),
        },
    )
    assert resp2.status_code == 200, resp2.text


def test_wrong_email_code_not_consumed(client: TestClient):
    from app.auth.email_codes import create_email_code

    email = "reuse@example.com"
    create_email_code(email, ttl_seconds=600)

    cap = client.get("/api/auth/captcha")
    cap_data = cap.json()
    resp = client.post(
        "/api/auth/email/login",
        json={
            "email": email,
            "code": "000000",
            "captcha_id": cap_data["captcha_id"],
            "captcha_x": int(cap_data["dev_answer"]),
        },
    )
    assert resp.status_code == 401

    cap2 = client.get("/api/auth/captcha")
    cap_data2 = cap2.json()
    send = client.post("/api/auth/email/send-code", json={"email": email})
    code = send.json()["dev_code"]
    resp2 = client.post(
        "/api/auth/email/login",
        json={
            "email": email,
            "code": code,
            "captcha_id": cap_data2["captcha_id"],
            "captcha_x": int(cap_data2["dev_answer"]),
        },
    )
    assert resp2.status_code == 200, resp2.text


def test_progress_requires_auth(client: TestClient):
    resp = client.get("/api/progress/overview")
    assert resp.status_code == 401


def test_words_public_without_familiarity(client: TestClient):
    resp = client.get("/api/words?page=1&page_size=5")
    assert resp.status_code == 200
    for item in resp.json()["items"]:
        assert item["familiarity"] is None


def test_words_familiarity_with_auth(client: TestClient):
    data = login_user(client, email="words@example.com")
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

    data = login_user(client, email="merge@example.com")
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
