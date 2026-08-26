from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class UserRecord:
    """Identity/profile user record (persistence-independent)."""

    id: int | None
    username: str
    email: str | None = None
    display_name: str | None = None
    avatar_url: str | None = None
    is_active: bool = True
    hashed_password: str | None = None
    oauth_provider: str | None = None
    oauth_subject: str | None = None
    legacy_device_id: str | None = None
    last_login_at: datetime | None = None
    created_at: datetime | None = None
