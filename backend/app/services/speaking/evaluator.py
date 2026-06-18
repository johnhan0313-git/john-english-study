from __future__ import annotations

import difflib
import re

from app.services.ai.openai_provider import get_ai_provider
from app.services.ai.prompts import WRITING_EVAL_PROMPT, WRITING_SAMPLE_SCHEMA
from app.config import Settings


def evaluate_speaking(expected: str, transcript: str) -> dict:
    def tokenize(text: str) -> list[str]:
        return re.findall(r"[a-zA-Z']+", text.lower())

    expected_tokens = tokenize(expected)
    transcript_tokens = tokenize(transcript)
    matcher = difflib.SequenceMatcher(None, expected_tokens, transcript_tokens)
    match_rate = round(matcher.ratio() * 100, 1)

    missing = [w for w in expected_tokens if w not in transcript_tokens]
    extra = [w for w in transcript_tokens if w not in expected_tokens]

    if match_rate >= 90:
        feedback = "Excellent! Your pronunciation and reading are very accurate."
    elif match_rate >= 70:
        feedback = "Good effort! Pay attention to the highlighted missing words."
    else:
        feedback = "Keep practicing. Try reading slowly and focus on each word."

    return {
        "transcript": transcript,
        "expected": expected,
        "match_rate": match_rate,
        "missing_words": missing[:10],
        "extra_words": extra[:10],
        "feedback": feedback,
    }


async def evaluate_writing(
    settings: Settings,
    prompt: str,
    content: str,
    target_words: list[str],
) -> dict:
    provider = get_ai_provider(settings)
    target = ", ".join(target_words)
    messages = [
        {
            "role": "user",
            "content": (
                f"{WRITING_EVAL_PROMPT}\n\n"
                f"Writing prompt: {prompt}\n"
                f"Target words: {target}\n"
                f"Student writing:\n{content}"
            ),
        }
    ]
    try:
        result = await provider.chat_json(messages, WRITING_EVAL_PROMPT)
    except Exception:
        content_lower = content.lower()
        used = [w for w in target_words if w.lower() in content_lower]
        missing = [w for w in target_words if w.lower() not in content_lower]
        return {
            "score": 70.0 if used else 50.0,
            "grammar_feedback": "Unable to reach AI service. Basic check applied.",
            "vocabulary_feedback": f"Used {len(used)} of {len(target_words)} target words.",
            "used_target_words": used,
            "missing_target_words": missing,
            "suggestions": ["Configure AI API key for detailed feedback."],
        }
    return {
        "score": float(result.get("score", 0)),
        "grammar_feedback": result.get("grammar_feedback", ""),
        "vocabulary_feedback": result.get("vocabulary_feedback", ""),
        "used_target_words": result.get("used_target_words", []),
        "missing_target_words": result.get("missing_target_words", []),
        "suggestions": result.get("suggestions", []),
    }


async def generate_writing_sample(
    settings: Settings,
    prompt: str,
    target_words: list[str],
    *,
    level: str = "cet4",
    theme: str | None = None,
    regenerate: bool = False,
) -> dict:
    provider = get_ai_provider(settings)
    target = ", ".join(target_words)
    theme_line = f"Theme/context: {theme}\n" if theme else ""
    regenerate_line = (
        "Important: This is a REGENERATION request. Write a completely NEW paragraph "
        "with a different story angle and sentence structure. Do not repeat a previous version.\n"
        if regenerate
        else ""
    )
    messages = [
        {
            "role": "user",
            "content": (
                f"Write a model paragraph for this writing exercise.\n"
                f"Level: {level}\n"
                f"{theme_line}"
                f"{regenerate_line}"
                f"Prompt: {prompt}\n"
                f"Target words (each MUST appear at least once): {target}"
            ),
        }
    ]
    result = await provider.chat_json(messages, WRITING_SAMPLE_SCHEMA, task="writing_sample")
    sample_en = str(result.get("sample_en", "")).strip()
    sample_zh = str(result.get("sample_zh", "")).strip()
    if not sample_en:
        raise ValueError("AI returned empty writing sample")
    return {"sample_en": sample_en, "sample_zh": sample_zh}
