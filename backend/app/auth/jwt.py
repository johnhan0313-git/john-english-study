from __future__ import annotations

from datetime import timedelta

from jose import JWTError, jwt

from app.config import get_settings
from app.utils.time import utc_now


def create_access_token(user_id: int) -> str:
    settings = get_settings()
    expire = utc_now() + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": str(user_id), "type": "access", "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> int | None:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        if payload.get("type") != "access":
            return None
        sub = payload.get("sub")
        return int(sub) if sub is not None else None
    except (JWTError, ValueError, TypeError):
        return None
