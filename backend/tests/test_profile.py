from __future__ import annotations

import io

from fastapi.testclient import TestClient

from app.auth.email_codes import create_email_code
from tests.auth_helpers import auth_headers, login_user


def test_get_and_update_display_name(client: TestClient):
    data = login_user(client, email="profile@example.com")
    headers = auth_headers(data["access_token"])

    me = client.get("/api/profile", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == "profile@example.com"

    patch = client.patch(
        "/api/profile",
        headers=headers,
        json={"display_name": "  新昵称  "},
    )
    assert patch.status_code == 200, patch.text
    assert patch.json()["display_name"] == "新昵称"

    auth_me = client.get("/api/auth/me", headers=headers)
    assert auth_me.status_code == 200
    assert auth_me.json()["display_name"] == "新昵称"


def test_change_email_success(client: TestClient):
    data = login_user(client, email="old@example.com")
    headers = auth_headers(data["access_token"])

    send = client.post(
        "/api/profile/email/send-code",
        headers=headers,
        json={"new_email": "new@example.com"},
    )
    assert send.status_code == 200, send.text
    code = send.json()["dev_code"]
    assert code

    change = client.patch(
        "/api/profile/email",
        headers=headers,
        json={"new_email": "new@example.com", "code": code},
    )
    assert change.status_code == 200, change.text
    assert change.json()["email"] == "new@example.com"


def test_change_email_taken(client: TestClient):
    login_user(client, email="taken@example.com")
    data = login_user(client, email="other@example.com")
    headers = auth_headers(data["access_token"])

    send = client.post(
        "/api/profile/email/send-code",
        headers=headers,
        json={"new_email": "taken@example.com"},
    )
    assert send.status_code == 400, send.text
    assert "已被" in send.json()["detail"]


def test_wrong_email_change_code_not_consumed(client: TestClient):
    data = login_user(client, email="retry@example.com")
    headers = auth_headers(data["access_token"])
    new_email = "retry-new@example.com"

    create_email_code(new_email, ttl_seconds=600)

    bad = client.patch(
        "/api/profile/email",
        headers=headers,
        json={"new_email": new_email, "code": "000000"},
    )
    assert bad.status_code == 400

    send = client.post(
        "/api/profile/email/send-code",
        headers=headers,
        json={"new_email": new_email},
    )
    assert send.status_code == 200, send.text
    code = send.json()["dev_code"]
    assert code

    ok = client.patch(
        "/api/profile/email",
        headers=headers,
        json={"new_email": new_email, "code": code},
    )
    assert ok.status_code == 200, ok.text
    assert ok.json()["email"] == new_email


def test_avatar_upload_and_get(client: TestClient):
    data = login_user(client, email="avatar@example.com")
    headers = auth_headers(data["access_token"])
    user_id = data["user"]["id"]

    png = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDAT"
        b"\x08\xd7c\xf8\xcf\xc0\x00\x00\x00\x03\x00\x01\x00\x05\xfe\xd4"
        b"\xef\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    upload = client.post(
        "/api/profile/avatar",
        headers=headers,
        files={"file": ("avatar.png", io.BytesIO(png), "image/png")},
    )
    assert upload.status_code == 200, upload.text
    avatar_url = upload.json()["avatar_url"]
    assert avatar_url and str(user_id) in avatar_url

    get_avatar = client.get(f"/api/profile/avatar/{user_id}")
    assert get_avatar.status_code == 200
    assert get_avatar.headers["content-type"].startswith("image/")
