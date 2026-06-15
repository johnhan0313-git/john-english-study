from __future__ import annotations

import io

from fastapi.responses import StreamingResponse

from app.services.storage.factory import get_storage


def storage_stream_response(
    key: str,
    *,
    media_type: str,
    filename: str,
) -> StreamingResponse:
    storage = get_storage()
    data = storage.get_bytes(key)
    return StreamingResponse(
        io.BytesIO(data),
        media_type=media_type,
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )
