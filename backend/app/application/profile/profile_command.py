from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.auth.email_codes import can_send_code, create_email_code, rollback_email_code, verify_email_code
from app.auth.email_service import EmailDeliveryError, send_email_change_code
from app.auth.users import normalize_email
from app.config import Settings, get_settings
from app.domains.identity.identity_domain import UserRecord
from app.domains.identity.user_repository import UserRepository
from app.infrastructure.unit_of_work import UnitOfWorkFactory
from app.services.media.avatar_paths import (
    ALLOWED_AVATAR_CONTENT_TYPES,
    avatar_api_url,
    avatar_key,
    remove_avatar_files,
)
from app.services.storage.factory import get_storage


@dataclass(frozen=True)
class GetProfileInput:
    user_id: int


@dataclass(frozen=True)
class UpdateProfileInput:
    user_id: int
    display_name: str


@dataclass(frozen=True)
class SendEmailChangeCodeInput:
    user_id: int
    new_email: str


@dataclass(frozen=True)
class ChangeEmailInput:
    user_id: int
    new_email: str
    code: str


@dataclass(frozen=True)
class UploadAvatarInput:
    user_id: int
    content_type: str
    data: bytes


@dataclass
class ProfileResult:
    id: int
    username: str
    email: str | None
    display_name: str | None
    avatar_url: str | None
    oauth_provider: str | None
    created_at: datetime


@dataclass
class SendEmailChangeCodeResult:
    cooldown_seconds: int
    dev_code: str | None


def _profile_from_user(user: UserRecord) -> ProfileResult:
    display = user.display_name or user.username
    return ProfileResult(
        id=user.id,  # type: ignore[arg-type]
        username=user.username,
        email=user.email,
        display_name=display,
        avatar_url=user.avatar_url,
        oauth_provider=user.oauth_provider,
        created_at=user.created_at,  # type: ignore[arg-type]
    )


def _should_expose_dev_secrets(settings: Settings) -> bool:
    return settings.testing or settings.debug or settings.auth_expose_codes


def _require_user(repo: UserRepository, user_id: int) -> UserRecord:
    user = repo.get_by_id(user_id)
    if not user:
        raise LookupError("User not found")
    return user


class GetProfileQuery:
    def __init__(self, uow_factory: UnitOfWorkFactory, repository_factory: Any):
        self._uow_factory = uow_factory
        self._repository_factory = repository_factory

    def execute(self, inp: GetProfileInput) -> ProfileResult:
        with self._uow_factory() as uow:
            repo: UserRepository = self._repository_factory(uow.session)
            user = _require_user(repo, inp.user_id)
            return _profile_from_user(user)


class UpdateProfileCommand:
    def __init__(self, uow_factory: UnitOfWorkFactory, repository_factory: Any):
        self._uow_factory = uow_factory
        self._repository_factory = repository_factory

    def execute(self, inp: UpdateProfileInput) -> ProfileResult:
        with self._uow_factory() as uow:
            repo: UserRepository = self._repository_factory(uow.session)
            user = _require_user(repo, inp.user_id)
            user.display_name = inp.display_name
            repo.save(user)
            uow.commit()
            return _profile_from_user(user)


class SendEmailChangeCodeCommand:
    def __init__(
        self,
        uow_factory: UnitOfWorkFactory,
        repository_factory: Any,
        settings: Settings | None = None,
    ):
        self._uow_factory = uow_factory
        self._repository_factory = repository_factory
        self._settings = settings

    def execute(self, inp: SendEmailChangeCodeInput) -> SendEmailChangeCodeResult:
        settings = self._settings or get_settings()
        new_email = normalize_email(inp.new_email)

        with self._uow_factory() as uow:
            repo: UserRepository = self._repository_factory(uow.session)
            user = _require_user(repo, inp.user_id)
            current = normalize_email(user.email) if user.email else None
            if current and new_email == current:
                raise ValueError("新邮箱与当前邮箱相同")

            if repo.email_taken(new_email, exclude_user_id=user.id):
                raise ValueError("该邮箱已被其他账号使用")

        if not settings.testing:
            allowed, wait_seconds = can_send_code(
                new_email, cooldown_seconds=settings.email_code_cooldown_seconds
            )
            if not allowed:
                raise PermissionError(f"请等待 {wait_seconds}s 后再试")

        code = create_email_code(new_email, ttl_seconds=settings.email_code_expire_minutes * 60)
        try:
            send_email_change_code(settings, new_email, code)
        except EmailDeliveryError:
            rollback_email_code(new_email)
            raise

        return SendEmailChangeCodeResult(
            cooldown_seconds=settings.email_code_cooldown_seconds,
            dev_code=code if _should_expose_dev_secrets(settings) else None,
        )


class ChangeEmailCommand:
    def __init__(self, uow_factory: UnitOfWorkFactory, repository_factory: Any):
        self._uow_factory = uow_factory
        self._repository_factory = repository_factory

    def execute(self, inp: ChangeEmailInput) -> ProfileResult:
        new_email = normalize_email(inp.new_email)
        with self._uow_factory() as uow:
            repo: UserRepository = self._repository_factory(uow.session)
            user = _require_user(repo, inp.user_id)
            current = normalize_email(user.email) if user.email else None
            if current and new_email == current:
                raise ValueError("新邮箱与当前邮箱相同")

            if not verify_email_code(new_email, inp.code):
                raise ValueError("邮箱验证码错误或已过期")

            if repo.email_taken(new_email, exclude_user_id=user.id):
                raise ValueError("该邮箱已被其他账号使用")

            user.email = new_email
            repo.save(user)
            uow.commit()
            return _profile_from_user(user)


class UploadAvatarCommand:
    def __init__(
        self,
        uow_factory: UnitOfWorkFactory,
        repository_factory: Any,
        settings: Settings | None = None,
    ):
        self._uow_factory = uow_factory
        self._repository_factory = repository_factory
        self._settings = settings

    def execute(self, inp: UploadAvatarInput) -> ProfileResult:
        settings = self._settings or get_settings()
        content_type = (inp.content_type or "").split(";", 1)[0].strip().lower()
        ext = ALLOWED_AVATAR_CONTENT_TYPES.get(content_type)
        if not ext:
            raise ValueError("仅支持 JPG、PNG、WebP 格式")
        if len(inp.data) > 2 * 1024 * 1024:
            raise ValueError("图片大小不能超过 2MB")
        if not inp.data:
            raise ValueError("上传文件为空")

        remove_avatar_files(inp.user_id, settings)
        key = avatar_key(inp.user_id, ext)
        get_storage(settings).put_bytes(key, inp.data, content_type)

        with self._uow_factory() as uow:
            repo: UserRepository = self._repository_factory(uow.session)
            user = _require_user(repo, inp.user_id)
            user.avatar_url = avatar_api_url(inp.user_id, version=int(time.time()))
            repo.save(user)
            uow.commit()
            return _profile_from_user(user)
