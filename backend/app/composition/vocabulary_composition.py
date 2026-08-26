from __future__ import annotations

from dataclasses import dataclass

from app.application.vocabulary.vocabulary_query import (
    GetWordDetailQuery,
    GetWordLemmaQuery,
    GetWordStatsQuery,
    ListWordGroupsQuery,
    ListWordLettersQuery,
    ListWordsQuery,
)
from app.database import SessionLocal
from app.infrastructure.unit_of_work import SqlAlchemyUnitOfWork


def _uow_factory() -> SqlAlchemyUnitOfWork:
    return SqlAlchemyUnitOfWork(_session=SessionLocal())


@dataclass
class VocabularyApplication:
    list_words: ListWordsQuery
    stats: GetWordStatsQuery
    groups: ListWordGroupsQuery
    letters: ListWordLettersQuery
    detail: GetWordDetailQuery
    lemma: GetWordLemmaQuery


def build_vocabulary_application() -> VocabularyApplication:
    return VocabularyApplication(
        list_words=ListWordsQuery(_uow_factory),
        stats=GetWordStatsQuery(_uow_factory),
        groups=ListWordGroupsQuery(_uow_factory),
        letters=ListWordLettersQuery(_uow_factory),
        detail=GetWordDetailQuery(_uow_factory),
        lemma=GetWordLemmaQuery(_uow_factory),
    )
