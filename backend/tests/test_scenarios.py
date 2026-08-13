from __future__ import annotations

import asyncio

from fastapi.testclient import TestClient

from app.services.ai.openai_provider import MockAIProvider
from app.services.ai.prompts import build_scenario_prompt
from tests.auth_helpers import auth_headers, register_user


def test_mock_scenario_respects_selected_theme():
    provider = MockAIProvider()
    words = [{"lemma": "contract", "pos": "n.", "definitions": ["合同"]}]
    messages = build_scenario_prompt(words, "cet4", "business", "narrative")

    result = asyncio.run(provider.chat_json(messages, schema_hint="", task="scenario"))

    assert result["theme"] == "business"
    assert result["title"] == "The Quarterly Business Review"
    assert "contract" in result["passage"]


def test_generate_scenario_uses_requested_theme(client: TestClient):
    data = register_user(client, email="scenario-business@example.com")
    headers = auth_headers(data["access_token"])
    resp = client.post(
        "/api/scenarios/generate",
        json={
            "level": "cet4",
            "theme": "business",
            "scenario_type": "narrative",
            "word_count": 8,
        },
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["theme"] == "business"
    assert body["title"] == "The Quarterly Business Review"
    assert any(word in body["content"]["passage"].lower() for word in ("contract", "negotiate", "client", "meeting"))


def test_scenario_resources_are_scoped_to_owner(client: TestClient):
    owner = register_user(client, email="scenario-owner@example.com")
    owner_headers = auth_headers(owner["access_token"])
    created = client.post(
        "/api/scenarios/generate",
        json={"level": "cet4", "theme": "business", "word_count": 8},
        headers=owner_headers,
    )
    assert created.status_code == 200, created.text
    scenario_id = created.json()["id"]

    other = register_user(client, email="scenario-other@example.com")
    other_headers = auth_headers(other["access_token"])
    for path in (
        f"/api/scenarios/{scenario_id}",
        f"/api/scenarios/{scenario_id}/translation",
        f"/api/scenarios/{scenario_id}/audio",
    ):
        response = client.get(path, headers=other_headers)
        assert response.status_code == 404, (path, response.text)

    completed = client.post(
        f"/api/scenarios/{scenario_id}/complete",
        json={"total": 1, "correct": 1},
        headers=other_headers,
    )
    assert completed.status_code == 404, completed.text


def test_exercises_are_scoped_to_scenario_owner(client: TestClient):
    owner = register_user(client, email="exercise-owner@example.com")
    owner_headers = auth_headers(owner["access_token"])
    created = client.post(
        "/api/scenarios/generate",
        json={"level": "cet4", "theme": "business", "word_count": 8},
        headers=owner_headers,
    )
    assert created.status_code == 200, created.text
    scenario_id = created.json()["id"]
    other = register_user(client, email="exercise-other@example.com")
    other_headers = auth_headers(other["access_token"])

    for method, path, payload in (
        ("get", f"/api/exercises/scenario/{scenario_id}", None),
        ("post", f"/api/exercises/scenario/{scenario_id}/submit", {"answers": {}}),
    ):
        response = getattr(client, method)(path, json=payload, headers=other_headers) if payload is not None else getattr(client, method)(path, headers=other_headers)
        assert response.status_code == 404, (path, response.text)
