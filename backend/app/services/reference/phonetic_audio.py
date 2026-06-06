from __future__ import annotations

import re
from pathlib import Path

from app.models.reference import PhoneticSymbol
from app.utils.json_helpers import parse_json_field

PHONETIC_TTS_VOICE = "en-GB-SoniaNeural"
SYMBOL_AUDIO_VERSION = "v2"

# Edge TTS 无法直接合成 IPA phoneme，使用英式教学用的独立音素提示音（非例词整词）
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


def get_phonetic_examples(phonetic: PhoneticSymbol) -> list[dict]:
    return parse_json_field(phonetic.examples, [])


def build_phonetic_symbol_speech_text(phonetic: PhoneticSymbol) -> str:
    cue = SYMBOL_SOUND_CUE.get(phonetic.symbol.strip())
    if cue:
        return cue

    examples = get_phonetic_examples(phonetic)
    if examples:
        return examples[0]["word"]

    return phonetic.name_en.replace("/", " ").strip() or phonetic.symbol


def build_phonetic_speech_text(phonetic: PhoneticSymbol, word: str | None = None) -> str:
    examples = get_phonetic_examples(phonetic)
    if word:
        return word

    words = [ex["word"] for ex in examples if ex.get("word")]
    if words:
        return ". ".join(words) + "."

    return phonetic.name_en.replace("/", " ").strip() or phonetic.symbol


def phonetic_audio_path(
    media_dir: Path,
    phonetic_id: int,
    *,
    kind: str = "examples",
    word: str | None = None,
) -> Path:
    if kind == "symbol":
        filename = f"phonetic_{phonetic_id}_symbol_{SYMBOL_AUDIO_VERSION}.mp3"
    elif word:
        safe = re.sub(r"[^a-z0-9-]", "", word.lower()) or "word"
        filename = f"phonetic_{phonetic_id}_{safe}.mp3"
    else:
        filename = f"phonetic_{phonetic_id}_examples.mp3"
    return media_dir / "phonetics" / filename


def resolve_phonetic_audio(
    phonetic: PhoneticSymbol,
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
