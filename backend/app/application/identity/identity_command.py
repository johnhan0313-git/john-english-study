from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.auth.jwt import create_access_token
from app.auth.users import normalize_email
from app.infrastructure.unit_of_work import UnitOfWorkFactory
from app.models.user import User
from app.utils.time import utc_now
import re
import secrets


def _username_from_email(email: str) -> str:
    local = email.split("@", 1)[0]
    base = re.sub(r"[^a-zA-Z0-9_]", "_", local).strip("_")[:24] or "user"
    return f"{base}_{secrets.token_hex(3)}"


def _unique_username(session: Session, email: str) -> str:
    for _ in range(8):
        candidate = _username_from_email(email)
        exists = session.query(User.id).filter(User.username == candidate).first()
        if not exists:
            return candidate
    return f"user_{secrets.token_hex(4)}"


@dataclass(frozen=True)
class LoginOrRegisterByEmailInput:
    email: str


@dataclass(frozen=True)
class LoginOrRegisterByWechatInput:
    openid: str
    nickname: str | None = None
    avatar_url: str | None = None


@dataclass
class AuthTokenResult:
    access_token: str
    user: User
    created: bool


class LoginOrRegisterByEmailCommand:
    """Explicit login-or-register for email OTP (replaces get_or_create_user_by_email)."""

    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

    def execute(self, inp: LoginOrRegisterByEmailInput) -> AuthTokenResult:
        email = normalize_email(inp.email)
        with self._uow_factory() as uow:
            user = uow.session.query(User).filter(User.email == email).first()
            created = False
            if not user:
                display = email.split("@", 1)[0]
                user = User(
                    username=_unique_username(uow.session, email),
                    email=email,
                    hashed_password=None,
                    display_name=display,
                )
                uow.session.add(user)
                created = True
            user.last_login_at = utc_now()
            uow.commit()
            uow.session.refresh(user)
            return AuthTokenResult(
                access_token=create_access_token(user.id),
                user=user,
                created=created,
            )


class LoginOrRegisterByWechatCommand:
    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

    def execute(self, inp: LoginOrRegisterByWechatInput) -> AuthTokenResult:
        with self._uow_factory() as uow:
            user = (
                uow.session.query(User)
                .filter(User.oauth_provider == "wechat", User.oauth_subject == inp.openid)
                .first()
            )
            created = False
            if not user:
                username = f"wx_{secrets.token_hex(4)}"
                user = User(
                    username=username,
                    email=None,
                    hashed_password=None,
                    display_name=inp.nickname or username,
                    avatar_url=inp.avatar_url,
                    oauth_provider="wechat",
                    oauth_subject=inp.openid,
                )
                uow.session.add(user)
                created = True
            else:
                if inp.nickname and not user.display_name:
                    user.display_name = inp.nickname
                if inp.avatar_url and not user.avatar_url:
                    user.avatar_url = inp.avatar_url
            user.last_login_at = utc_now()
            uow.commit()
            uow.session.refresh(user)
            return AuthTokenResult(
                access_token=create_access_token(user.id),
                user=user,
                created=created,
            )
