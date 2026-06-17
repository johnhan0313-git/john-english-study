from __future__ import annotations

from app.services.reference.import_reference import PHONETICS_SEED
from app.services.reference.phonetic_audio import (
    SYMBOL_SOUND_CUE,
    build_phonetic_symbol_speech_text,
    get_primary_example_word,
)


class _FakePhonetic:
    def __init__(self, symbol: str, category: str, name_en: str, examples: str = "[]"):
        self.symbol = symbol
        self.category = category
        self.name_en = name_en
        self.examples = examples


def test_all_seed_symbols_have_examples_or_sound_cue():
    for item in PHONETICS_SEED:
        has_examples = bool(item.get("examples"))
        has_cue = item["symbol"] in SYMBOL_SOUND_CUE
        assert has_examples or has_cue, item["symbol"]


def test_symbol_speech_text_prefers_example_word():
    p = _FakePhonetic(
        "ɒ",
        "short_vowel",
        "lot (BrE)",
        '[{"word": "hot", "ipa": "/hɒt/", "meaning_zh": "热的"}]',
    )
    assert get_primary_example_word(p) == "hot"
    assert build_phonetic_symbol_speech_text(p) == "hot"


def test_symbol_speech_text_fallback_to_cue_without_examples():
    p = _FakePhonetic("p", "consonant", "p", "[]")
    assert build_phonetic_symbol_speech_text(p) == "puh"
