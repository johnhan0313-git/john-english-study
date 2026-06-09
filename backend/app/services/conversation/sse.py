from __future__ import annotations

import json
from collections.abc import AsyncIterator


def encode_sse_token(token: str) -> str:
    payload = json.dumps({"type": "token", "content": token})
    return f"data: {payload}\n\n"


def encode_sse_done(message_id: int) -> str:
    payload = json.dumps({"type": "done", "message_id": message_id})
    return f"data: {payload}\n\n"


def encode_sse_error(message: str) -> str:
    payload = json.dumps({"type": "error", "message": message})
    return f"data: {payload}\n\n"


async def stream_conversation_sse(
    token_stream: AsyncIterator[str],
) -> AsyncIterator[str]:
    message_id = 0
    async for token in token_stream:
        if token.startswith("\n__DONE__:"):
            message_id = int(token.split(":")[1])
            yield encode_sse_done(message_id)
        else:
            yield encode_sse_token(token)
