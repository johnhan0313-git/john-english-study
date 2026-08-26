from __future__ import annotations

from dataclasses import dataclass

from app.application.reference.reference_query import (
    GetGrammarQuery,
    GetPhoneticQuery,
    ListGrammarQuery,
    ListPhoneticsQuery,
    MaterializePhoneticAudioCommand,
)
from app.config import Settings, get_settings
from app.database import SessionLocal
from app.infrastructure.unit_of_work import SqlAlchemyUnitOfWork


def _uow_factory() -> SqlAlchemyUnitOfWork:
    return SqlAlchemyUnitOfWork(_session=SessionLocal())


@dataclass
class ReferenceApplication:
    list_phonetics: ListPhoneticsQuery
    get_phonetic: GetPhoneticQuery
    materialize_phonetic_audio: MaterializePhoneticAudioCommand
    list_grammar: ListGrammarQuery
    get_grammar: GetGrammarQuery


def build_reference_application(settings: Settings | None = None) -> ReferenceApplication:
    cfg = settings or get_settings()
    return ReferenceApplication(
        list_phonetics=ListPhoneticsQuery(_uow_factory),
        get_phonetic=GetPhoneticQuery(_uow_factory),
        materialize_phonetic_audio=MaterializePhoneticAudioCommand(_uow_factory, cfg),
        list_grammar=ListGrammarQuery(_uow_factory),
        get_grammar=GetGrammarQuery(_uow_factory),
    )
