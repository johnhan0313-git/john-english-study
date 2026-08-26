from __future__ import annotations

from typing import Protocol

from app.domains.conversation.conversation_domain import (
    ConversationMessageRecord,
    ConversationSessionRecord,
)


class ConversationRepository(Protocol):
    def get_by_id(
        self, session_id: int, user_id: int | None = None
    ) -> ConversationSessionRecord | None: ...

    def list_by_user(
        self, user_id: int, skip: int, limit: int
    ) -> tuple[list[ConversationSessionRecord], int]: ...

    def add(self, session: ConversationSessionRecord) -> ConversationSessionRecord: ...

    def save(self, session: ConversationSessionRecord) -> None: ...

    def add_message(
        self, session_id: int, message: ConversationMessageRecord
    ) -> ConversationMessageRecord: ...

    def resolve_word_ids_by_lemmas(self, lemmas: list[str]) -> dict[str, int]: ...
