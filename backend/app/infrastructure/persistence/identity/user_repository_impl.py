from __future__ import annotations

from sqlalchemy.orm import Session

from app.domains.identity.identity_domain import UserRecord
from app.models.conversation import ConversationSession
from app.models.progress import LearningStreak, ScenarioAttempt, UserWordProgress
from app.models.scenario import Scenario
from app.models.user import User


def _to_record(row: User) -> UserRecord:
    return UserRecord(
        id=row.id,
        username=row.username,
        email=row.email,
        display_name=row.display_name,
        avatar_url=row.avatar_url,
        is_active=bool(row.is_active),
        hashed_password=row.hashed_password,
        oauth_provider=row.oauth_provider,
        oauth_subject=row.oauth_subject,
        legacy_device_id=row.legacy_device_id,
        last_login_at=row.last_login_at,
        created_at=row.created_at,
    )


class SqlAlchemyUserRepository:
    def __init__(self, session: Session):
        self._session = session

    def get_by_id(self, user_id: int) -> UserRecord | None:
        row = self._session.query(User).filter(User.id == user_id).first()
        return _to_record(row) if row else None

    def get_by_email(self, email: str) -> UserRecord | None:
        row = self._session.query(User).filter(User.email == email).first()
        return _to_record(row) if row else None

    def get_by_wechat(self, openid: str) -> UserRecord | None:
        row = (
            self._session.query(User)
            .filter(User.oauth_provider == "wechat", User.oauth_subject == openid)
            .first()
        )
        return _to_record(row) if row else None

    def email_taken(self, email: str, *, exclude_user_id: int | None = None) -> bool:
        q = self._session.query(User.id).filter(User.email == email)
        if exclude_user_id is not None:
            q = q.filter(User.id != exclude_user_id)
        return q.first() is not None

    def username_exists(self, username: str) -> bool:
        return self._session.query(User.id).filter(User.username == username).first() is not None

    def add(self, user: UserRecord) -> UserRecord:
        row = User(
            username=user.username,
            email=user.email,
            hashed_password=user.hashed_password,
            display_name=user.display_name,
            avatar_url=user.avatar_url,
            is_active=user.is_active,
            oauth_provider=user.oauth_provider,
            oauth_subject=user.oauth_subject,
            legacy_device_id=user.legacy_device_id,
            last_login_at=user.last_login_at,
        )
        self._session.add(row)
        self._session.flush()
        user.id = row.id
        user.created_at = row.created_at
        return user

    def save(self, user: UserRecord) -> None:
        if user.id is None:
            raise ValueError("Cannot save user without id")
        row = self._session.query(User).filter(User.id == user.id).first()
        if not row:
            raise ValueError("User not found")
        row.username = user.username
        row.email = user.email
        row.hashed_password = user.hashed_password
        row.display_name = user.display_name
        row.avatar_url = user.avatar_url
        row.is_active = user.is_active
        row.oauth_provider = user.oauth_provider
        row.oauth_subject = user.oauth_subject
        row.legacy_device_id = user.legacy_device_id
        row.last_login_at = user.last_login_at
        self._session.flush()
        self._session.refresh(row)
        user.created_at = row.created_at
        user.last_login_at = row.last_login_at

    def merge_word_progress(self, user_id: int, device_id: str) -> int:
        merged = 0
        legacy_rows = (
            self._session.query(UserWordProgress)
            .filter(UserWordProgress.device_id == device_id, UserWordProgress.user_id.is_(None))
            .all()
        )
        for row in legacy_rows:
            existing = (
                self._session.query(UserWordProgress)
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
                self._session.delete(row)
            else:
                row.user_id = user_id
                row.device_id = None
                merged += 1
        self._session.flush()
        return merged

    def reassign_scenarios(self, user_id: int, device_id: str) -> int:
        return self._reassign_rows(Scenario, user_id, device_id)

    def reassign_attempts(self, user_id: int, device_id: str) -> int:
        return self._reassign_rows(ScenarioAttempt, user_id, device_id)

    def reassign_conversations(self, user_id: int, device_id: str) -> int:
        return self._reassign_rows(ConversationSession, user_id, device_id)

    def merge_streak(self, user_id: int, device_id: str) -> int:
        legacy = (
            self._session.query(LearningStreak)
            .filter(LearningStreak.device_id == device_id)
            .first()
        )
        if not legacy:
            return 0
        existing = (
            self._session.query(LearningStreak).filter(LearningStreak.user_id == user_id).first()
        )
        if existing:
            existing.current_streak = max(existing.current_streak, legacy.current_streak)
            existing.longest_streak = max(existing.longest_streak, legacy.longest_streak)
            if legacy.last_active_date and (
                not existing.last_active_date or legacy.last_active_date > existing.last_active_date
            ):
                existing.last_active_date = legacy.last_active_date
            self._session.delete(legacy)
        else:
            legacy.user_id = user_id
            legacy.device_id = None
        self._session.flush()
        return 1

    def _reassign_rows(self, model, user_id: int, device_id: str) -> int:
        rows = (
            self._session.query(model)
            .filter(model.device_id == device_id, model.user_id.is_(None))
            .all()
        )
        for row in rows:
            row.user_id = user_id
            row.device_id = None
        self._session.flush()
        return len(rows)
