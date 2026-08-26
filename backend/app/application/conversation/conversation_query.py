from __future__ import annotations

from typing import Any

from app.application.conversation.conversation_input import (
    ConversationDetailOutput,
    ConversationListOutput,
    ConversationMessageOutput,
    GetConversationInput,
    ListConversationsInput,
)
from app.application.conversation.conversation_mapping import (
    message_to_output,
    session_to_brief,
    session_to_detail,
)
from app.domains.conversation.conversation_repository import ConversationRepository
from app.infrastructure.unit_of_work import UnitOfWorkFactory


class GetConversationQuery:
    def __init__(self, uow_factory: UnitOfWorkFactory, repository_factory: Any):
        self._uow_factory = uow_factory
        self._repository_factory = repository_factory

    def execute(self, inp: GetConversationInput) -> ConversationDetailOutput | None:
        with self._uow_factory() as uow:
            repo: ConversationRepository = self._repository_factory(uow.session)
            session = repo.get_by_id(inp.session_id, inp.user_id)
            if not session:
                return None
            return session_to_detail(session)


class ListConversationsQuery:
    def __init__(self, uow_factory: UnitOfWorkFactory, repository_factory: Any):
        self._uow_factory = uow_factory
        self._repository_factory = repository_factory

    def execute(self, inp: ListConversationsInput) -> ConversationListOutput:
        with self._uow_factory() as uow:
            repo: ConversationRepository = self._repository_factory(uow.session)
            items, total = repo.list_by_user(inp.user_id, inp.skip, inp.limit)
            return ConversationListOutput(
                items=[session_to_brief(item) for item in items],
                total=total,
            )


class ListMessagesQuery:
    def __init__(self, uow_factory: UnitOfWorkFactory, repository_factory: Any):
        self._uow_factory = uow_factory
        self._repository_factory = repository_factory

    def execute(self, inp: GetConversationInput) -> list[ConversationMessageOutput] | None:
        with self._uow_factory() as uow:
            repo: ConversationRepository = self._repository_factory(uow.session)
            session = repo.get_by_id(inp.session_id, inp.user_id)
            if not session:
                return None
            return [
                message_to_output(m)
                for m in sorted(session.messages, key=lambda x: x.id if x.id is not None else 0)
                if m.id is not None and m.created_at is not None
            ]
