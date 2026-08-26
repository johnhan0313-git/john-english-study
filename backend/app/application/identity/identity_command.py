from __future__ import annotations

import re
import secrets
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.auth.jwt import create_access_token
from app.auth.users import normalize_email
from app.infrastructure.unit_of_work import UnitOfWorkFactory
from app.models.conversation import ConversationSession
from app.models.progress import LearningStreak, ScenarioAttempt, UserWordProgress
from app.models.scenario import Scenario
from app.models.user import User
from app.utils.time import utc_now


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


@dataclass(frozen=True)
class MergeDeviceInput:
    user_id: int
    device_id: str


def _merge_word_progress(session: Session, user_id: int, device_id: str) -> int:
    merged = 0
    legacy_rows = (
        session.query(UserWordProgress)
        .filter(UserWordProgress.device_id == device_id, UserWordProgress.user_id.is_(None))
        .all()
    )
    for row in legacy_rows:
        existing = (
            session.query(UserWordProgress)
            .filter(UserWordProgress.user_id == user_id, UserWordProgress.word_id == row.word_id)
            .first()
        )
        if existing:
            if row.familiarity > existing.familiarity:
                existing.familiarity = row.familiarity
                existing.correct_count = max(existing.correct_count, row.correct_count)
                existing.wrong_count = max(existing.wrong_count, row.wrong_count)
                if row.next_review:
                    existing.next_review = row.next_review
                if row.last_reviewed:
                    existing.last_reviewed = row.last_reviewed
            session.delete(row)
        else:
            row.user_id = user_id
            row.device_id = None
            merged += 1
    session.flush()
    return merged


def _reassign_rows(session: Session, model, user_id: int, device_id: str) -> int:
    rows = (
        session.query(model)
        .filter(model.device_id == device_id, model.user_id.is_(None))
        .all()
    )
    for row in rows:
        row.user_id = user_id
        row.device_id = None
    session.flush()
    return len(rows)


def _merge_streak(session: Session, user_id: int, device_id: str) -> int:
    legacy = session.query(LearningStreak).filter(LearningStreak.device_id == device_id).first()
    if not legacy:
        return 0
    existing = session.query(LearningStreak).filter(LearningStreak.user_id == user_id).first()
    if existing:
        existing.current_streak = max(existing.current_streak, legacy.current_streak)
        existing.longest_streak = max(existing.longest_streak, legacy.longest_streak)
        if legacy.last_active_date and (
            not existing.last_active_date or legacy.last_active_date > existing.last_active_date
        ):
            existing.last_active_date = legacy.last_active_date
        session.delete(legacy)
    else:
        legacy.user_id = user_id
        legacy.device_id = None
    return 1


class MergeDeviceCommand:
    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

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
            user = uow.session.query(User).filter(User.id == inp.user_id).first()
            if not user:
                raise LookupError("User not found")

            result = {
                "word_progress": _merge_word_progress(uow.session, user.id, inp.device_id),
                "scenarios": _reassign_rows(uow.session, Scenario, user.id, inp.device_id),
                "attempts": _reassign_rows(uow.session, ScenarioAttempt, user.id, inp.device_id),
                "conversations": _reassign_rows(
                    uow.session, ConversationSession, user.id, inp.device_id
                ),
                "streak": _merge_streak(uow.session, user.id, inp.device_id),
            }
            user.legacy_device_id = inp.device_id
            uow.commit()
            return result
