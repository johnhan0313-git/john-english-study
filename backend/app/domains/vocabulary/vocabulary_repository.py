from __future__ import annotations

from typing import Any, Protocol


class VocabularyReadRepository(Protocol):
    def list_words(
        self,
        *,
        page: int = 1,
        page_size: int = 30,
        level: str | None = None,
        theme: str | None = None,
        search: str | None = None,
        letter: str | None = None,
        user_id: int | None = None,
    ) -> dict[str, Any]: ...

    def get_stats(self, user_id: int) -> dict[str, Any]: ...

    def list_groups(self) -> list[dict[str, Any]]: ...

    def list_letters(
        self,
        *,
        level: str | None = None,
        theme: str | None = None,
        search: str | None = None,
    ) -> list[str]: ...

    def get_detail(self, word_id: int, user_id: int | None = None) -> dict[str, Any]: ...

    def get_lemma(self, word_id: int) -> str: ...
