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

    login = client.post(
        "/api/auth/email/login",
        json={
            "email": email,
            "code": code,
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
