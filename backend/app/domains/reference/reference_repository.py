from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class PhoneticAudioSource:
    """Plain data needed to build phonetic TTS audio (no ORM)."""

    id: int
    symbol: str
    name_en: str
    examples: list[dict[str, Any]]


class ReferenceReadRepository(Protocol):
    def list_phonetics(
        self, *, category: str | None = None, search: str | None = None
    ) -> dict[str, Any]: ...

    def get_phonetic(self, phonetic_id: int) -> dict[str, Any]: ...

    def get_phonetic_audio_source(self, phonetic_id: int) -> PhoneticAudioSource | None: ...

    def list_grammar(
        self,
        *,
        category: str | None = None,
        level: str | None = None,
        search: str | None = None,
    ) -> dict[str, Any]: ...

    def get_grammar(self, slug: str) -> dict[str, Any]: ...
