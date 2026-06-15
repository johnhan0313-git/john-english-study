from __future__ import annotations

from app.config import Settings, get_settings
from app.services.storage.factory import get_storage

ALLOWED_AVATAR_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

MAX_AVATAR_BYTES = 2 * 1024 * 1024


def avatar_key(user_id: int, ext: str) -> str:
    return f"avatars/{user_id}{ext}"


def find_avatar_key(user_id: int, settings: Settings | None = None) -> tuple[str, str] | None:
    storage = get_storage(settings)
    for ext, content_type in {
        ".jpg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }.items():
        key = avatar_key(user_id, ext)
        if storage.exists(key):
            return key, content_type
    return None


def remove_avatar_files(user_id: int, settings: Settings | None = None) -> None:
    storage = get_storage(settings)
    for ext in ALLOWED_AVATAR_CONTENT_TYPES.values():
        key = avatar_key(user_id, ext)
        if storage.exists(key):
            storage.delete(key)


def avatar_api_url(user_id: int, *, version: int | None = None) -> str:
    suffix = f"?v={version}" if version is not None else ""
    return f"/profile/avatar/{user_id}{suffix}"
