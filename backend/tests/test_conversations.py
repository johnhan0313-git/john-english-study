from __future__ import annotations

from fastapi.testclient import TestClient


def test_create_standalone_conversation(client: TestClient):
    resp = client.post("/api/conversations", json={"device_id": "test-chat", "level": "cet4", "theme": "travel"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] > 0
    assert data["status"] == "active"
    assert len(data["messages"]) >= 1
    assert data["messages"][0]["role"] == "assistant"


def test_send_message_non_stream(client):
    create = client.post("/api/conversations", json={"device_id": "test-chat-2", "level": "cet4"})
    session_id = create.json()["id"]
    resp = client.post(
        f"/api/conversations/{session_id}/messages?device_id=test-chat-2",
        json={"content": "I want to check my reservation please."},
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "assistant"


def test_stream_message(client):
    create = client.post("/api/conversations", json={"device_id": "test-chat-3", "level": "cet4"})
    session_id = create.json()["id"]
    with client.stream(
        "POST",
        f"/api/conversations/{session_id}/messages/stream?device_id=test-chat-3",
        json={"content": "Hello, I need help with my schedule."},
    ) as resp:
        assert resp.status_code == 200
        body = "".join(resp.iter_text())
        assert "data:" in body
        assert "token" in body or "done" in body


def test_list_conversations(client):
    client.post("/api/conversations", json={"device_id": "list-device", "level": "cet4"})
    resp = client.get("/api/conversations?device_id=list-device")
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


def test_end_conversation(client):
    create = client.post("/api/conversations", json={"device_id": "end-device", "level": "cet4"})
    session_id = create.json()["id"]
    client.post(
        f"/api/conversations/{session_id}/messages?device_id=end-device",
        json={"content": "Could you help me with my luggage?"},
    )
    resp = client.post(f"/api/conversations/{session_id}/end", json={"device_id": "end-device"})
    assert resp.status_code == 200
    assert resp.json()["summary"]
