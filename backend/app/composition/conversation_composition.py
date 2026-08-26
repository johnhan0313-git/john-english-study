from __future__ import annotations

from dataclasses import dataclass

from app.application.conversation.conversation_command import (
    CreateSessionCommand,
    EndSessionCommand,
    SendMessageCommand,
    UpdateSettingsCommand,
)
from app.application.conversation.conversation_query import (
    GetConversationQuery,
    ListConversationsQuery,
    ListMessagesQuery,
)
from app.application.progress.progress_command import RecordAnswerCommand
from app.config import Settings, get_settings
from app.database import SessionLocal
from app.infrastructure.persistence.conversation.conversation_repository_impl import (
    SqlAlchemyConversationRepository,
)
from app.infrastructure.persistence.progress.progress_repository_impl import SqlAlchemyProgressRepository
from app.infrastructure.persistence.scenario.scenario_adapters import SqlAlchemyWordSelectionAdapter
from app.infrastructure.persistence.scenario.scenario_repository_impl import SqlAlchemyScenarioRepository
from app.infrastructure.unit_of_work import SqlAlchemyUnitOfWork
from app.services.ai.factory import build_providers


def _uow_factory() -> SqlAlchemyUnitOfWork:
    return SqlAlchemyUnitOfWork(_session=SessionLocal())


@dataclass
class ConversationApplication:
    create_session: CreateSessionCommand
    update_settings: UpdateSettingsCommand
    send_message: SendMessageCommand
    end_session: EndSessionCommand
    get_session: GetConversationQuery
    list_sessions: ListConversationsQuery
    list_messages: ListMessagesQuery


def build_conversation_application(
    settings: Settings | None = None,
    record_answer: RecordAnswerCommand | None = None,
) -> ConversationApplication:
    cfg = settings or get_settings()
    llm = build_providers(cfg).llm
    answer = record_answer or RecordAnswerCommand(_uow_factory, SqlAlchemyProgressRepository)
    return ConversationApplication(
        create_session=CreateSessionCommand(
            uow_factory=_uow_factory,
            repository_factory=SqlAlchemyConversationRepository,
            word_selection_factory=SqlAlchemyWordSelectionAdapter,
            scenario_repository_factory=SqlAlchemyScenarioRepository,
            llm=llm,
        ),
        update_settings=UpdateSettingsCommand(_uow_factory, SqlAlchemyConversationRepository),
        send_message=SendMessageCommand(_uow_factory, SqlAlchemyConversationRepository, llm),
        end_session=EndSessionCommand(
            _uow_factory,
            SqlAlchemyConversationRepository,
            llm,
            answer,
        ),
        get_session=GetConversationQuery(_uow_factory, SqlAlchemyConversationRepository),
        list_sessions=ListConversationsQuery(_uow_factory, SqlAlchemyConversationRepository),
        list_messages=ListMessagesQuery(_uow_factory, SqlAlchemyConversationRepository),
    )
