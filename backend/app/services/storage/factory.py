from __future__ import annotations

from app.config import Settings, get_settings
from app.services.storage.local import LocalStorageBackend
from app.services.storage.protocol import StorageBackend

_backend: StorageBackend | None = None


def get_storage(settings: Settings | None = None) -> StorageBackend:
    global _backend
    if _backend is not None and settings is None:
        return _backend

    cfg = settings or get_settings()
    if cfg.storage_backend == "s3":
        from app.services.storage.s3 import S3StorageBackend

        backend: StorageBackend = S3StorageBackend(cfg)
    else:
        backend = LocalStorageBackend(cfg)

    if settings is None:
        _backend = backend
    return backend


def reset_storage_for_tests() -> None:
    global _backend
    _backend = None
