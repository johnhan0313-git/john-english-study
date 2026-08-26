from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domains.vocabulary.vocabulary_repository import VocabularyReadRepository
from app.infrastructure.unit_of_work import UnitOfWorkFactory


@dataclass(frozen=True)
class ListWordsInput:
    page: int = 1
    page_size: int = 30
    level: str | None = None
    theme: str | None = None
    search: str | None = None
    letter: str | None = None
    user_id: int | None = None


@dataclass(frozen=True)
class GetWordStatsInput:
    user_id: int


@dataclass(frozen=True)
class GetWordDetailInput:
    word_id: int
    user_id: int | None = None


@dataclass(frozen=True)
class ListWordLettersInput:
    level: str | None = None
    theme: str | None = None
    search: str | None = None


@dataclass(frozen=True)
class GetWordLemmaInput:
    word_id: int


class ListWordsQuery:
    def __init__(self, uow_factory: UnitOfWorkFactory, repository_factory: Any):
        self._uow_factory = uow_factory
        self._repository_factory = repository_factory

    def execute(self, inp: ListWordsInput) -> dict[str, Any]:
        with self._uow_factory() as uow:
            repo: VocabularyReadRepository = self._repository_factory(uow.session)
            return repo.list_words(
                page=inp.page,
                page_size=inp.page_size,
                level=inp.level,
                theme=inp.theme,
                search=inp.search,
                letter=inp.letter,
                user_id=inp.user_id,
            )


class GetWordStatsQuery:
    def __init__(self, uow_factory: UnitOfWorkFactory, repository_factory: Any):
        self._uow_factory = uow_factory
        self._repository_factory = repository_factory

    def execute(self, inp: GetWordStatsInput) -> dict[str, Any]:
        with self._uow_factory() as uow:
            repo: VocabularyReadRepository = self._repository_factory(uow.session)
            return repo.get_stats(inp.user_id)


class ListWordGroupsQuery:
    def __init__(self, uow_factory: UnitOfWorkFactory, repository_factory: Any):
        self._uow_factory = uow_factory
        self._repository_factory = repository_factory

    def execute(self) -> list[dict[str, Any]]:
        with self._uow_factory() as uow:
            repo: VocabularyReadRepository = self._repository_factory(uow.session)
            return repo.list_groups()


class ListWordLettersQuery:
    def __init__(self, uow_factory: UnitOfWorkFactory, repository_factory: Any):
        self._uow_factory = uow_factory
        self._repository_factory = repository_factory

    def execute(self, inp: ListWordLettersInput) -> list[str]:
        with self._uow_factory() as uow:
            repo: VocabularyReadRepository = self._repository_factory(uow.session)
            return repo.list_letters(level=inp.level, theme=inp.theme, search=inp.search)


class GetWordDetailQuery:
    def __init__(self, uow_factory: UnitOfWorkFactory, repository_factory: Any):
        self._uow_factory = uow_factory
        self._repository_factory = repository_factory

    def execute(self, inp: GetWordDetailInput) -> dict[str, Any]:
        with self._uow_factory() as uow:
            repo: VocabularyReadRepository = self._repository_factory(uow.session)
            return repo.get_detail(inp.word_id, inp.user_id)


class GetWordLemmaQuery:
    def __init__(self, uow_factory: UnitOfWorkFactory, repository_factory: Any):
        self._uow_factory = uow_factory
        self._repository_factory = repository_factory

    def execute(self, inp: GetWordLemmaInput) -> str:
        with self._uow_factory() as uow:
            repo: VocabularyReadRepository = self._repository_factory(uow.session)
            return repo.get_lemma(inp.word_id)
