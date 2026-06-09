from __future__ import annotations

import logging
import random
import secrets
import threading
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_codes: dict[str, "EmailCodeEntry"] = {}
_last_sent: dict[str, float] = {}


@dataclass(frozen=True)
class EmailCodeEntry:
    code: str
    expires_at: float


def _purge_expired(now: float) -> None:
    expired = [email for email, item in _codes.items() if item.expires_at <= now]
    for email in expired:
        _codes.pop(email, None)


def can_send_code(email: str, *, cooldown_seconds: int) -> tuple[bool, int]:
    now = time.time()
    with _lock:
        last = _last_sent.get(email)
        if last and now - last < cooldown_seconds:
            return False, int(cooldown_seconds - (now - last))
    return True, 0


def create_email_code(email: str, *, ttl_seconds: int = 600) -> str:
    code = f"{random.randint(0, 999999):06d}"
    now = time.time()
    with _lock:
        _purge_expired(now)
        _codes[email] = EmailCodeEntry(code=code, expires_at=now + ttl_seconds)
        _last_sent[email] = now
    return code


def verify_email_code(email: str, code: str) -> bool:
    now = time.time()
    with _lock:
        _purge_expired(now)
        entry = _codes.pop(email, None)
    if not entry or entry.expires_at <= now:
        return False
    return entry.code == code.strip()


def debug_token() -> str:
    return secrets.token_hex(8)
