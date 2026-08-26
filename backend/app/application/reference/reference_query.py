from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.config import Settings, get_settings
from app.domains.reference.reference_repository import ReferenceReadRepository
from app.infrastructure.unit_of_work import UnitOfWorkFactory
from app.services.ai.openai_provider import AIProviderError
from app.services.ai.tts_service import generate_speech_bytes
from app.services.reference.phonetic_audio import (
    PHONETIC_TTS_VOICE,
    PHONETIC_WORD_RATE,
    build_phonetic_speech_text,
    build_phonetic_symbol_speech_text,
    phonetic_audio_key,
    resolve_phonetic_audio,
)
from app.services.storage.factory import get_storage


@dataclass(frozen=True)
class ListPhoneticsInput:
    category: str | None = None
    search: str | None = None


@dataclass(frozen=True)
class GetPhoneticInput:
    phonetic_id: int


@dataclass(frozen=True)
class MaterializePhoneticAudioInput:
    phonetic_id: int
    word: str | None = None
    preview: bool = False
    kind: str | None = None


@dataclass(frozen=True)
class ListGrammarInput:
    category: str | None = None
    level: str | None = None
    search: str | None = None


@dataclass(frozen=True)
class GetGrammarInput:
    slug: str


class ListPhoneticsQuery:
    def __init__(self, uow_factory: UnitOfWorkFactory, repository_factory: Any):
        self._uow_factory = uow_factory
        self._repository_factory = repository_factory

    def execute(self, inp: ListPhoneticsInput) -> dict[str, Any]:
        with self._uow_factory() as uow:
            repo: ReferenceReadRepository = self._repository_factory(uow.session)
            return repo.list_phonetics(category=inp.category, search=inp.search)


class GetPhoneticQuery:
    def __init__(self, uow_factory: UnitOfWorkFactory, repository_factory: Any):
        self._uow_factory = uow_factory
        self._repository_factory = repository_factory

    def execute(self, inp: GetPhoneticInput) -> dict[str, Any]:
        with self._uow_factory() as uow:
            repo: ReferenceReadRepository = self._repository_factory(uow.session)
            return repo.get_phonetic(inp.phonetic_id)


class MaterializePhoneticAudioCommand:
    def __init__(
        self,
        uow_factory: UnitOfWorkFactory,
        repository_factory: Any,
        settings: Settings | None = None,
    ):
        self._uow_factory = uow_factory
        self._repository_factory = repository_factory
        self._settings = settings

    async def execute(self, inp: MaterializePhoneticAudioInput) -> str:
        if inp.kind not in (None, "symbol", "examples", "word"):
            raise ValueError("Invalid kind; use symbol, examples, or word")

        settings = self._settings or get_settings()
        with self._uow_factory() as uow:
            repo: ReferenceReadRepository = self._repository_factory(uow.session)
            phonetic = repo.get_phonetic_audio_source(inp.phonetic_id)
            if not phonetic:
                raise LookupError("Phonetic symbol not found")

            if inp.kind == "symbol":
                audio_kind, resolved_word = "symbol", None
            elif inp.kind == "examples":
                if not phonetic.examples:
                    raise ValueError("No example words for this phonetic symbol")
                audio_kind, resolved_word = "examples", None
            else:
                audio_kind, resolved_word = resolve_phonetic_audio(
                    phonetic, word=inp.word, preview=inp.preview
                )

            audio_key = phonetic_audio_key(
                inp.phonetic_id,
                kind=audio_kind,
                word=resolved_word,
            )
            if audio_kind == "symbol":
                speech_text = build_phonetic_symbol_speech_text(phonetic)
            else:
                speech_text = build_phonetic_speech_text(phonetic, resolved_word)

        storage = get_storage(settings)
        if not storage.exists(audio_key):
            try:
                rate = PHONETIC_WORD_RATE if " " not in speech_text.strip() else None
                audio = await generate_speech_bytes(
                    speech_text,
                    settings,
                    voice=PHONETIC_TTS_VOICE,
                    rate=rate,
                )
                storage.put_bytes(audio_key, audio, "audio/mpeg")
            except AIProviderError:
                raise
        return audio_key


class ListGrammarQuery:
    def __init__(self, uow_factory: UnitOfWorkFactory, repository_factory: Any):
        self._uow_factory = uow_factory
        self._repository_factory = repository_factory

    def execute(self, inp: ListGrammarInput) -> dict[str, Any]:
        with self._uow_factory() as uow:
            repo: ReferenceReadRepository = self._repository_factory(uow.session)
            return repo.list_grammar(
                category=inp.category, level=inp.level, search=inp.search
            )


class GetGrammarQuery:
    def __init__(self, uow_factory: UnitOfWorkFactory, repository_factory: Any):
        self._uow_factory = uow_factory
        self._repository_factory = repository_factory

    def execute(self, inp: GetGrammarInput) -> dict[str, Any]:
        with self._uow_factory() as uow:
            repo: ReferenceReadRepository = self._repository_factory(uow.session)
            return repo.get_grammar(inp.slug)
