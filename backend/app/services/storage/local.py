from __future__ import annotations

from pathlib import Path

from app.config import Settings, get_settings


class LocalStorageBackend:
    def __init__(self, settings: Settings | None = None) -> None:
        self._root = (settings or get_settings()).media_dir

    def _path(self, key: str) -> Path:
        normalized = key.lstrip("/").replace("\\", "/")
        path = self._root / normalized
        if not path.resolve().is_relative_to(self._root.resolve()):
            raise ValueError(f"Invalid storage key: {key}")
        return path

    def exists(self, key: str) -> bool:
        return self._path(key).is_file()

    def get_bytes(self, key: str) -> bytes:
        path = self._path(key)
        if not path.is_file():
            raise FileNotFoundError(key)
        return path.read_bytes()

    def put_bytes(self, key: str, data: bytes, content_type: str) -> None:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def delete(self, key: str) -> None:
        path = self._path(key)
        if path.is_file():
            path.unlink()
