from __future__ import annotations

import asyncio

import httpx
import pytest

from app.config import AIEndpointConfig
from app.services.ai.openai_provider import AIProviderError, OpenAICompatibleProvider


def _provider(*, retries: int = 2, timeout: float = 1.0) -> OpenAICompatibleProvider:
    return OpenAICompatibleProvider(
        AIEndpointConfig(
            base_url="https://ai.test/v1",
            api_key="test-key",
            model="test-model",
            max_retries=retries,
            timeout_seconds=timeout,
        )
    )


def test_post_retries_temporary_upstream_errors():
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        status = 503 if calls < 3 else 200
        return httpx.Response(status, request=request, json={"ok": status == 200})

    async def run():
        provider = _provider(retries=2)
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await provider._post(client, "https://ai.test/v1/chat/completions")

    response = asyncio.run(run())
    assert response.status_code == 200
    assert calls == 3


def test_post_does_not_retry_authentication_errors():
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(401, request=request)

    async def run():
        provider = _provider(retries=2)
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await provider._post(client, "https://ai.test/v1/chat/completions")

    response = asyncio.run(run())
    assert response.status_code == 401
    assert calls == 1


def test_post_converts_timeout_to_provider_error():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("too slow", request=request)

    async def run():
        provider = _provider(retries=0, timeout=0.25)
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            await provider._post(client, "https://ai.test/v1/chat/completions")

    with pytest.raises(AIProviderError, match="timed out after 0.25s"):
        asyncio.run(run())
