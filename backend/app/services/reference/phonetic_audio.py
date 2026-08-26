from __future__ import annotations

import re
from typing import Any, Protocol

from app.utils.json_helpers import parse_json_field

PHONETIC_TTS_VOICE = "en-GB-SoniaNeural"
SYMBOL_AUDIO_VERSION = "v3"
PHONETIC_WORD_RATE = "-8%"


class PhoneticAudioLike(Protocol):
    symbol: str
    name_en: str
    examples: Any

# Edge TTS 不支持 IPA 音素合成；仅在无例词时作为最后兜底（质量有限）
SYMBOL_SOUND_CUE: dict[str, str] = {
    # 短元音
    "ɪ": "ih",
    "e": "eh",
    "æ": "ah",
    "ʌ": "uh",
    "ɒ": "o",
    "ʊ": "oo",
    "ə": "uh",
    # 长元音
    "iː": "ee",
    "ɑː": "ah",
    "ɔː": "aw",
    "uː": "oo",
    "ɜː": "er",
    # 双元音
    "eɪ": "ay",
    "aɪ": "eye",
    "ɔɪ": "oy",
    "aʊ": "ow",
    "əʊ": "oh",
    "ɪə": "ear",
    "eə": "air",
    "ʊə": "ure",
    # 辅音
    "p": "puh",
    "b": "buh",
    "t": "tuh",
    "d": "duh",
    "k": "kuh",
    "g": "guh",
    "f": "fuh",
    "v": "vuh",
    "θ": "th",
    "ð": "the",
    "s": "sss",
    "z": "zzz",
    "ʃ": "sh",
    "ʒ": "zh",
    "h": "huh",
    "tʃ": "ch",
    "dʒ": "juh",
    "m": "mmm",
    "n": "nnn",
    "ŋ": "ng",
    "l": "luh",
    "r": "ruh",
    "j": "yuh",
    "w": "wuh",
}


def get_phonetic_examples(phonetic: PhoneticAudioLike) -> list[dict]:
    return parse_json_field(phonetic.examples, [])


def get_primary_example_word(phonetic: PhoneticAudioLike) -> str | None:
    examples = get_phonetic_examples(phonetic)
    if not examples:
        return None
    word = examples[0].get("word")
    return str(word).strip() if word else None


def build_phonetic_symbol_speech_text(phonetic: PhoneticAudioLike) -> str:
    """Prefer a real BrE example word over spell-it-out cues for TTS accuracy."""
    primary = get_primary_example_word(phonetic)
    if primary:
        return primary

    cue = SYMBOL_SOUND_CUE.get(phonetic.symbol.strip())
    if cue:
        return cue

    return phonetic.name_en.replace("/", " ").strip() or phonetic.symbol


def build_phonetic_speech_text(phonetic: PhoneticAudioLike, word: str | None = None) -> str:
    examples = get_phonetic_examples(phonetic)
    if word:
        return word

    words = [ex["word"] for ex in examples if ex.get("word")]
    if words:
        return ". ".join(words) + "."

    return phonetic.name_en.replace("/", " ").strip() or phonetic.symbol


def phonetic_audio_key(
    phonetic_id: int,
    *,
    kind: str = "examples",
    word: str | None = None,
) -> str:
    if kind == "symbol":
        filename = f"phonetic_{phonetic_id}_symbol_{SYMBOL_AUDIO_VERSION}.mp3"
    elif word:
        safe = re.sub(r"[^a-z0-9-]", "", word.lower()) or "word"
        filename = f"phonetic_{phonetic_id}_{safe}.mp3"
    else:
        filename = f"phonetic_{phonetic_id}_examples.mp3"
    return f"phonetics/{filename}"


def resolve_phonetic_audio(
    phonetic: PhoneticAudioLike,
    *,
    word: str | None,
    preview: bool,
) -> tuple[str, str | None]:
    """Return (audio_kind, resolved_word). audio_kind is 'examples' or 'word'."""
    examples = get_phonetic_examples(phonetic)
    allowed = {ex["word"].lower(): ex["word"] for ex in examples if ex.get("word")}

    if preview:
        if not examples:
            raise ValueError("No example words for this phonetic symbol")
        return "word", examples[0]["word"]

    if word:
        resolved = allowed.get(word.lower())
        if not resolved:
            raise ValueError(f"Word '{word}' is not an example for this phonetic symbol")
        return "word", resolved

    if not examples:
        raise ValueError("No example words for this phonetic symbol")
    return "examples", None
