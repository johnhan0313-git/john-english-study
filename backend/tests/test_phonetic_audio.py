from __future__ import annotations

from app.services.reference.import_reference import PHONETICS_SEED
from app.services.reference.phonetic_audio import SYMBOL_SOUND_CUE, build_phonetic_symbol_speech_text


class _FakePhonetic:
    def __init__(self, symbol: str, category: str, name_en: str, examples: str = "[]"):
        self.symbol = symbol
        self.category = category
        self.name_en = name_en
        self.examples = examples


def test_all_seed_symbols_have_sound_cue():
    missing = [item["symbol"] for item in PHONETICS_SEED if item["symbol"] not in SYMBOL_SOUND_CUE]
    assert not missing, f"Missing sound cue for: {missing}"


def test_symbol_speech_text_is_not_example_word():
    p = _FakePhonetic("ɪ", "short_vowel", "short i", '[{"word": "sit", "ipa": "/sɪt/", "meaning_zh": "坐"}]')
    assert build_phonetic_symbol_speech_text(p) == "ih"
    assert build_phonetic_symbol_speech_text(p) != "sit"


def test_consonant_sound_cue():
    p = _FakePhonetic("p", "consonant", "p")
    assert build_phonetic_symbol_speech_text(p) == "puh"
