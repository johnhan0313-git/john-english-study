from __future__ import annotations

import re
import secrets
from dataclasses import dataclass
from typing import Any

from app.auth.jwt import create_access_token
from app.auth.users import normalize_email
from app.domains.identity.identity_domain import UserRecord
from app.domains.identity.user_repository import UserRepository
from app.infrastructure.unit_of_work import UnitOfWorkFactory
from app.utils.time import utc_now


def _username_from_email(email: str) -> str:
    local = email.split("@", 1)[0]
    base = re.sub(r"[^a-zA-Z0-9_]", "_", local).strip("_")[:24] or "user"
    return f"{base}_{secrets.token_hex(3)}"


def _unique_username(repo: UserRepository, email: str) -> str:
    for _ in range(8):
        candidate = _username_from_email(email)
        if not repo.username_exists(candidate):
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
    user: UserRecord
    created: bool


class LoginOrRegisterByEmailCommand:
    """Explicit login-or-register for email OTP (replaces get_or_create_user_by_email)."""

    def __init__(self, uow_factory: UnitOfWorkFactory, repository_factory: Any):
        self._uow_factory = uow_factory
        self._repository_factory = repository_factory

    def execute(self, inp: LoginOrRegisterByEmailInput) -> AuthTokenResult:
        email = normalize_email(inp.email)
        with self._uow_factory() as uow:
            repo: UserRepository = self._repository_factory(uow.session)
            user = repo.get_by_email(email)
            created = False
            if not user:
                display = email.split("@", 1)[0]
                user = repo.add(
                    UserRecord(
                        id=None,
                        username=_unique_username(repo, email),
                        email=email,
                        hashed_password=None,
                        display_name=display,
                        last_login_at=utc_now(),
                    )
                )
                created = True
            else:
                user.last_login_at = utc_now()
                repo.save(user)
            uow.commit()
            return AuthTokenResult(
                access_token=create_access_token(user.id),  # type: ignore[arg-type]
                user=user,
                created=created,
            )


class LoginOrRegisterByWechatCommand:
    def __init__(self, uow_factory: UnitOfWorkFactory, repository_factory: Any):
        self._uow_factory = uow_factory
        self._repository_factory = repository_factory

    def execute(self, inp: LoginOrRegisterByWechatInput) -> AuthTokenResult:
        with self._uow_factory() as uow:
            repo: UserRepository = self._repository_factory(uow.session)
            user = repo.get_by_wechat(inp.openid)
            created = False
            if not user:
                username = f"wx_{secrets.token_hex(4)}"
                user = repo.add(
                    UserRecord(
                        id=None,
                        username=username,
                        email=None,
                        hashed_password=None,
                        display_name=inp.nickname or username,
                        avatar_url=inp.avatar_url,
                        oauth_provider="wechat",
                        oauth_subject=inp.openid,
                        last_login_at=utc_now(),
                    )
                )
                created = True
            else:
                if inp.nickname and not user.display_name:
                    user.display_name = inp.nickname
                if inp.avatar_url and not user.avatar_url:
                    user.avatar_url = inp.avatar_url
                user.last_login_at = utc_now()
                repo.save(user)
            uow.commit()
            return AuthTokenResult(
                access_token=create_access_token(user.id),  # type: ignore[arg-type]
                user=user,
                created=created,
            )


@dataclass(frozen=True)
class MergeDeviceInput:
    user_id: int
    device_id: str


class MergeDeviceCommand:
    def __init__(self, uow_factory: UnitOfWorkFactory, repository_factory: Any):
        self._uow_factory = uow_factory
        self._repository_factory = repository_factory

    def execute(self, inp: MergeDeviceInput) -> dict[str, int]:
        if not inp.device_id or inp.device_id == "default":
            return {
                "word_progress": 0,
                "scenarios": 0,
                "attempts": 0,
                "conversations": 0,
                "streak": 0,
            }

        with self._uow_factory() as uow:
            repo: UserRepository = self._repository_factory(uow.session)
            user = repo.get_by_id(inp.user_id)
            if not user:
                raise LookupError("User not found")

            result = {
                "word_progress": repo.merge_word_progress(user.id, inp.device_id),  # type: ignore[arg-type]
                "scenarios": repo.reassign_scenarios(user.id, inp.device_id),  # type: ignore[arg-type]
                "attempts": repo.reassign_attempts(user.id, inp.device_id),  # type: ignore[arg-type]
                "conversations": repo.reassign_conversations(user.id, inp.device_id),  # type: ignore[arg-type]
                "streak": repo.merge_streak(user.id, inp.device_id),  # type: ignore[arg-type]
            }
            user.legacy_device_id = inp.device_id
            repo.save(user)
            uow.commit()
            return result
