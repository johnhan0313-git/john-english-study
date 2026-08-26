from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.config import Settings, get_settings
from app.infrastructure.unit_of_work import UnitOfWorkFactory
from app.models.reference import GrammarPoint, PhoneticSymbol
from app.services.ai.openai_provider import AIProviderError
from app.services.ai.tts_service import generate_speech_bytes
from app.services.reference.import_reference import (
    GRAMMAR_CATEGORY_ZH,
    PHONETIC_CATEGORY_ZH,
    grammar_to_brief,
    grammar_to_detail,
    phonetic_to_brief,
    phonetic_to_detail,
)
from app.services.reference.phonetic_audio import (
    PHONETIC_TTS_VOICE,
    PHONETIC_WORD_RATE,
    build_phonetic_speech_text,
    build_phonetic_symbol_speech_text,
    phonetic_audio_key,
    resolve_phonetic_audio,
)
from app.services.storage.factory import get_storage
from app.utils.json_helpers import parse_json_field


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
    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

    def execute(self, inp: ListPhoneticsInput) -> dict[str, Any]:
        with self._uow_factory() as uow:
            query = uow.session.query(PhoneticSymbol)
            if inp.category:
                query = query.filter(PhoneticSymbol.category == inp.category)
            if inp.search:
                like = f"%{inp.search}%"
                query = query.filter(
                    (PhoneticSymbol.symbol.ilike(like))
                    | (PhoneticSymbol.name_zh.ilike(like))
                    | (PhoneticSymbol.name_en.ilike(like))
                )
            items = query.order_by(PhoneticSymbol.sort_order).all()
            briefs = [phonetic_to_brief(p) for p in items]

            groups: list[dict[str, Any]] = []
            by_cat: dict[str, list[dict]] = {}
            for b in briefs:
                by_cat.setdefault(b["category"], []).append(b)
            for cat, cat_items in by_cat.items():
                groups.append(
                    {
                        "category": cat,
                        "category_zh": PHONETIC_CATEGORY_ZH.get(cat, cat),
                        "items": cat_items,
                        "count": len(cat_items),
                    }
                )

            return {"items": briefs, "groups": groups, "total": len(briefs)}


class GetPhoneticQuery:
    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

    def execute(self, inp: GetPhoneticInput) -> dict[str, Any]:
        with self._uow_factory() as uow:
            p = uow.session.query(PhoneticSymbol).filter(PhoneticSymbol.id == inp.phonetic_id).first()
            if not p:
                raise ValueError("Phonetic symbol not found")
            return phonetic_to_detail(p)


class MaterializePhoneticAudioCommand:
    def __init__(self, uow_factory: UnitOfWorkFactory, settings: Settings | None = None):
        self._uow_factory = uow_factory
        self._settings = settings

    async def execute(self, inp: MaterializePhoneticAudioInput) -> str:
        if inp.kind not in (None, "symbol", "examples", "word"):
            raise ValueError("Invalid kind; use symbol, examples, or word")

        settings = self._settings or get_settings()
        with self._uow_factory() as uow:
            phonetic = (
                uow.session.query(PhoneticSymbol)
                .filter(PhoneticSymbol.id == inp.phonetic_id)
                .first()
            )
            if not phonetic:
                raise LookupError("Phonetic symbol not found")

            if inp.kind == "symbol":
                audio_kind, resolved_word = "symbol", None
            elif inp.kind == "examples":
                examples = parse_json_field(phonetic.examples, [])
                if not examples:
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
    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

    def execute(self, inp: ListGrammarInput) -> dict[str, Any]:
        with self._uow_factory() as uow:
            query = uow.session.query(GrammarPoint)
            if inp.category:
                query = query.filter(GrammarPoint.category == inp.category)
            if inp.level == "cet4":
                query = query.filter(GrammarPoint.level.in_(["cet4", "both"]))
            elif inp.level == "cet6":
                query = query.filter(GrammarPoint.level.in_(["cet6", "both"]))
            if inp.search:
                like = f"%{inp.search}%"
                query = query.filter(
                    (GrammarPoint.title.ilike(like)) | (GrammarPoint.summary.ilike(like))
                )
            items = query.order_by(GrammarPoint.sort_order).all()
            briefs = [grammar_to_brief(g) for g in items]

            groups: list[dict[str, Any]] = []
            by_cat: dict[str, list[dict]] = {}
            for b in briefs:
                by_cat.setdefault(b["category"], []).append(b)
            for cat, cat_items in by_cat.items():
                groups.append(
                    {
                        "category": cat,
                        "category_zh": GRAMMAR_CATEGORY_ZH.get(cat, cat),
                        "items": cat_items,
                        "count": len(cat_items),
                    }
                )

            return {"items": briefs, "groups": groups, "total": len(briefs)}


class GetGrammarQuery:
    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

    def execute(self, inp: GetGrammarInput) -> dict[str, Any]:
        with self._uow_factory() as uow:
            g = uow.session.query(GrammarPoint).filter(GrammarPoint.slug == inp.slug).first()
            if not g:
                raise ValueError("Grammar point not found")
            return grammar_to_detail(g)
