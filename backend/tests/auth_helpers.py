from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


def login_user(
    client: TestClient,
    email: str = "test@example.com",
) -> dict:
    send = client.post("/api/auth/email/send-code", json={"email": email})
    assert send.status_code == 200, send.text
    code = send.json().get("dev_code")
    assert code, "dev_code required in test mode"

    cap = client.get("/api/auth/captcha")
    assert cap.status_code == 200, cap.text
    cap_data = cap.json()
    captcha_x = cap_data.get("dev_answer")
    assert captcha_x is not None, "dev_answer required in test mode"

    login = client.post(
        "/api/auth/email/login",
        json={
            "email": email,
            "code": code,
            "captcha_id": cap_data["captcha_id"],
            "captcha_x": int(captcha_x),
        },
    )
    assert login.status_code == 200, login.text
    return login.json()


register_user = login_user


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_client(client: TestClient) -> tuple[TestClient, str, dict]:
    data = login_user(client, email="fixture@example.com")
    token = data["access_token"]
    return client, token, auth_headers(token)
