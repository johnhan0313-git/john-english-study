from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


def register_user(
    client: TestClient,
    username: str = "testuser",
    password: str = "password123",
) -> dict:
    resp = client.post(
        "/api/auth/register",
        json={"username": username, "password": password},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_client(client: TestClient) -> tuple[TestClient, str, dict]:
    data = register_user(client, username="fixture_user")
    token = data["access_token"]
    return client, token, auth_headers(token)
