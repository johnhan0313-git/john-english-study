from app.services.storage.factory import get_storage
from app.services.storage.protocol import StorageBackend

__all__ = ["StorageBackend", "get_storage"]
