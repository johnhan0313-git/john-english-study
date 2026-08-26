from __future__ import annotations

from dataclasses import dataclass

from app.application.profile.profile_command import (
    ChangeEmailCommand,
    GetProfileQuery,
    SendEmailChangeCodeCommand,
    UpdateProfileCommand,
    UploadAvatarCommand,
)
from app.config import Settings, get_settings
from app.database import SessionLocal
from app.infrastructure.unit_of_work import SqlAlchemyUnitOfWork


def _uow_factory() -> SqlAlchemyUnitOfWork:
    return SqlAlchemyUnitOfWork(_session=SessionLocal())


@dataclass
class ProfileApplication:
    get_profile: GetProfileQuery
    update_profile: UpdateProfileCommand
    send_email_change_code: SendEmailChangeCodeCommand
    change_email: ChangeEmailCommand
    upload_avatar: UploadAvatarCommand


def build_profile_application(settings: Settings | None = None) -> ProfileApplication:
    cfg = settings or get_settings()
    return ProfileApplication(
        get_profile=GetProfileQuery(_uow_factory),
        update_profile=UpdateProfileCommand(_uow_factory),
        send_email_change_code=SendEmailChangeCodeCommand(_uow_factory, cfg),
        change_email=ChangeEmailCommand(_uow_factory),
        upload_avatar=UploadAvatarCommand(_uow_factory, cfg),
    )
