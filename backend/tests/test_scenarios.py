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
