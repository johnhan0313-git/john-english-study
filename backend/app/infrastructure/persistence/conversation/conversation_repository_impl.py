from __future__ import annotations

from sqlalchemy.orm import Session, joinedload

from app.domains.conversation.conversation_domain import (
    ConversationMessageRecord,
    ConversationSessionRecord,
)
from app.models.conversation import ConversationMessage, ConversationSession
from app.models.word import Word
from app.utils.json_helpers import parse_json_field


def _message_to_record(row: ConversationMessage) -> ConversationMessageRecord:
    return ConversationMessageRecord(
        id=row.id,
        role=row.role,
        content=row.content,
        meta=parse_json_field(row.meta, {}),
        created_at=row.created_at,
    )


def _to_record(row: ConversationSession) -> ConversationSessionRecord:
    messages = [_message_to_record(m) for m in (row.messages or [])]
    scene_brief = parse_json_field(row.scene_brief, {})
    target_words = parse_json_field(row.target_words, [])
    words_used = parse_json_field(row.words_used, [])
    return ConversationSessionRecord(
        id=row.id,
        user_id=row.user_id,
        scenario_id=row.scenario_id,
        title=row.title,
        theme=row.theme,
        level=row.level,
        role_ai=row.role_ai,
        role_user=row.role_user,
        scene_brief=scene_brief,
        target_words=target_words,
        mode=row.mode,
        status=row.status,
        turn_count=row.turn_count,
        words_used=words_used,
        summary=row.summary,
        created_at=row.created_at,
        ended_at=row.ended_at,
        messages=messages,
    )


class SqlAlchemyConversationRepository:
    def __init__(self, session: Session):
        self._session = session

    def get_by_id(
        self, session_id: int, user_id: int | None = None
    ) -> ConversationSessionRecord | None:
        query = (
            self._session.query(ConversationSession)
            .options(joinedload(ConversationSession.messages))
            .filter(ConversationSession.id == session_id)
        )
        if user_id is not None:
            query = query.filter(ConversationSession.user_id == user_id)
        row = query.first()
        return _to_record(row) if row else None

    def list_by_user(
        self, user_id: int, skip: int, limit: int
    ) -> tuple[list[ConversationSessionRecord], int]:
        q = self._session.query(ConversationSession).filter(ConversationSession.user_id == user_id)
        total = q.count()
        rows = (
            q.options(joinedload(ConversationSession.messages))
            .order_by(ConversationSession.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [_to_record(r) for r in rows], total

    def add(self, session: ConversationSessionRecord) -> ConversationSessionRecord:
        row = ConversationSession(
            user_id=session.user_id,
            scenario_id=session.scenario_id,
            title=session.title,
            theme=session.theme,
            level=session.level,
            role_ai=session.role_ai,
            role_user=session.role_user,
            scene_brief=dict(session.scene_brief),
            target_words=list(session.target_words),
            mode=session.mode,
            status=session.status,
            turn_count=session.turn_count,
            words_used=list(session.words_used),
            summary=session.summary,
        )
        self._session.add(row)
        self._session.flush()
        session.id = row.id
        session.created_at = row.created_at
        return session

    def save(self, session: ConversationSessionRecord) -> None:
        if session.id is None:
            raise ValueError("Cannot save conversation without id")
        row = (
            self._session.query(ConversationSession)
            .filter(ConversationSession.id == session.id)
            .first()
        )
        if not row:
            raise ValueError("Conversation not found")
        row.title = session.title
        row.theme = session.theme
        row.level = session.level
        row.role_ai = session.role_ai
        row.role_user = session.role_user
        row.scene_brief = dict(session.scene_brief)
        row.target_words = list(session.target_words)
        row.mode = session.mode
        row.status = session.status
        row.turn_count = session.turn_count
        row.words_used = list(session.words_used)
        row.summary = session.summary
        row.ended_at = session.ended_at
        self._session.flush()

    def add_message(
        self, session_id: int, message: ConversationMessageRecord
    ) -> ConversationMessageRecord:
        row = ConversationMessage(
            session_id=session_id,
            role=message.role,
            content=message.content,
            meta=dict(message.meta or {}),
        )
        self._session.add(row)
        self._session.flush()
        message.id = row.id
        message.created_at = row.created_at
        return message

    def resolve_word_ids_by_lemmas(self, lemmas: list[str]) -> dict[str, int]:
        if not lemmas:
            return {}
        words = self._session.query(Word).filter(Word.lemma.in_(lemmas)).all()
        return {w.lemma: w.id for w in words}
