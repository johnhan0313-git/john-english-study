from __future__ import annotations

from fastapi.testclient import TestClient

from tests.auth_helpers import auth_headers, register_user


def test_create_conversation(client: TestClient):
    data = register_user(client, username="chat_user1")
    headers = auth_headers(data["access_token"])
    resp = client.post("/api/conversations", json={"level": "cet4", "theme": "travel"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["id"] > 0


def test_send_message(client: TestClient):
    data = register_user(client, username="chat_user2")
    headers = auth_headers(data["access_token"])
    create = client.post("/api/conversations", json={"level": "cet4"}, headers=headers)
    session_id = create.json()["id"]
    resp = client.post(
        f"/api/conversations/{session_id}/messages",
        json={"content": "Hello, I need help with my reservation."},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "assistant"


def test_stream_message(client: TestClient):
    data = register_user(client, username="chat_user3")
    headers = auth_headers(data["access_token"])
    create = client.post("/api/conversations", json={"level": "cet4"}, headers=headers)
    session_id = create.json()["id"]
    resp = client.post(
        f"/api/conversations/{session_id}/messages/stream",
        json={"content": "Hi there"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers.get("content-type", "")


def test_list_conversations(client: TestClient):
    data = register_user(client, username="list_user")
    headers = auth_headers(data["access_token"])
    client.post("/api/conversations", json={"level": "cet4"}, headers=headers)
    resp = client.get("/api/conversations", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


def test_end_conversation(client: TestClient):
    data = register_user(client, username="end_user")
    headers = auth_headers(data["access_token"])
    create = client.post("/api/conversations", json={"level": "cet4"}, headers=headers)
    session_id = create.json()["id"]
    client.post(
        f"/api/conversations/{session_id}/messages",
        json={"content": "Let's practice vocabulary."},
        headers=headers,
    )
    resp = client.post(f"/api/conversations/{session_id}/end", json={}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["session_id"] == session_id
