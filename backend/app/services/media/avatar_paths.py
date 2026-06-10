from __future__ import annotations

from pathlib import Path

from app.config import Settings, get_settings

ALLOWED_AVATAR_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

MAX_AVATAR_BYTES = 2 * 1024 * 1024


def avatar_dir(settings: Settings | None = None) -> Path:
    cfg = settings or get_settings()
    path = cfg.media_dir / "avatars"
    path.mkdir(parents=True, exist_ok=True)
    return path


def avatar_path(user_id: int, ext: str, settings: Settings | None = None) -> Path:
    return avatar_dir(settings) / f"{user_id}{ext}"


def find_avatar_path(user_id: int, settings: Settings | None = None) -> Path | None:
    directory = avatar_dir(settings)
    for ext in ALLOWED_AVATAR_CONTENT_TYPES.values():
        candidate = directory / f"{user_id}{ext}"
        if candidate.is_file():
            return candidate
    return None


def remove_avatar_files(user_id: int, settings: Settings | None = None) -> None:
    directory = avatar_dir(settings)
    for ext in ALLOWED_AVATAR_CONTENT_TYPES.values():
        path = directory / f"{user_id}{ext}"
        if path.is_file():
            path.unlink()


def avatar_api_url(user_id: int, *, version: int | None = None) -> str:
    suffix = f"?v={version}" if version is not None else ""
    return f"/profile/avatar/{user_id}{suffix}"
