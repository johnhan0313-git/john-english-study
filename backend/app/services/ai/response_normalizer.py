from __future__ import annotations

from typing import Any

from app.services.ai.openai_provider import AIProviderError


def _as_str(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _pick(data: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in data and data[key] not in (None, ""):
            return data[key]
    return None


def _unwrap_nested(data: dict[str, Any]) -> dict[str, Any]:
    for key in ("scenario", "data", "content", "result", "output"):
        nested = data.get(key)
        if isinstance(nested, dict):
            merged = {**data, **nested}
            return merged
    return data


class WrongResponseTypeError(AIProviderError):
    """LLM returned exercises when scenario was expected, or vice versa."""


def is_scenario_misresponse(raw: dict[str, Any]) -> bool:
    keys = set(raw.keys())
    if keys <= {"exercises", "questions", "items", "题目", "练习"}:
        return bool(keys)
    if "exercises" in keys and "passage" not in keys and "text" not in keys:
        return True
    return False


def normalize_scenario_response(raw: dict[str, Any]) -> dict[str, Any]:
    if is_scenario_misresponse(raw):
        raise WrongResponseTypeError(
            f"AI returned exercises instead of scenario. Got keys: {list(raw.keys())}"
        )

    data = _unwrap_nested(raw)

    passage = _pick(data, "passage", "text", "body", "content_text", "story", "narrative", "正文", "content")
    if isinstance(passage, dict):
        passage = _pick(passage, "passage", "text", "body", "content")

    title = _pick(data, "title", "name", "heading", "标题")
    summary_zh = _pick(data, "summary_zh", "summary", "summary_cn", "chinese_summary", "中文摘要", "摘要")
    passage_zh = _pick(data, "passage_zh", "passage_cn", "translation_zh", "chinese_passage", "译文")
    fun_fact = _pick(data, "fun_fact", "funFact", "interesting_fact", "fact", "趣味知识")
    theme = _pick(data, "theme", "topic", "主题")
    dialogue = _pick(data, "dialogue", "dialogues", "conversation", "lines", "对话")
    word_usage = _pick(data, "word_usage", "wordUsage", "vocabulary", "words_usage", "target_words", "词汇用法")

    if not passage:
        if isinstance(dialogue, list) and dialogue:
            lines = []
            for item in dialogue:
                if isinstance(item, dict):
                    speaker = _as_str(item.get("speaker") or item.get("role") or item.get("name") or "")
                    text = _as_str(item.get("text") or item.get("content") or item.get("line") or "")
                    if text:
                        lines.append(f"{speaker}: {text}" if speaker else text)
                elif isinstance(item, str):
                    lines.append(item)
            passage = " ".join(lines)

    if not passage:
        raise AIProviderError(
            f"AI response missing 'passage'. Got keys: {list(raw.keys())}. "
            "Ensure the model returns JSON with a 'passage' field."
        )

    if not isinstance(dialogue, list):
        dialogue = []
    if not isinstance(word_usage, list):
        word_usage = []

    normalized_dialogue = []
    for item in dialogue:
        if isinstance(item, dict):
            normalized_dialogue.append({
                "speaker": _as_str(item.get("speaker") or item.get("role") or item.get("name") or "Speaker"),
                "text": _as_str(item.get("text") or item.get("content") or item.get("line") or ""),
            })
        elif isinstance(item, str) and ":" in item:
            speaker, _, text = item.partition(":")
            normalized_dialogue.append({"speaker": speaker.strip(), "text": text.strip()})

    normalized_word_usage = []
    for item in word_usage:
        if isinstance(item, dict):
            normalized_word_usage.append({
                "word": _as_str(item.get("word") or item.get("lemma") or item.get("vocabulary") or ""),
                "sentence": _as_str(item.get("sentence") or item.get("example") or item.get("context") or ""),
                "meaning_zh": _as_str(item.get("meaning_zh") or item.get("meaning") or item.get("translation") or ""),
            })
        elif isinstance(item, str):
            normalized_word_usage.append({"word": item, "sentence": "", "meaning_zh": ""})

    return {
        "title": _as_str(title) or "Learning Scenario",
        "theme": _as_str(theme),
        "passage": _as_str(passage),
        "dialogue": normalized_dialogue,
        "word_usage": [w for w in normalized_word_usage if w["word"]],
        "summary_zh": _as_str(summary_zh),
        "passage_zh": _as_str(passage_zh),
        "fun_fact": _as_str(fun_fact) or None,
    }


def normalize_exercise_response(raw: dict[str, Any]) -> dict[str, Any]:
    data = raw
    exercises = _pick(data, "exercises", "questions", "items", "练习", "题目")
    if exercises is None and "type" in data:
        exercises = [data]
    if not isinstance(exercises, list):
        for key in ("data", "result", "output"):
            nested = raw.get(key)
            if isinstance(nested, dict):
                return normalize_exercise_response(nested)
        exercises = []

    normalized = []
    for ex in exercises:
        if not isinstance(ex, dict):
            continue
        ex_type = _as_str(ex.get("type") or ex.get("question_type") or "single_choice").lower()
        if "fill" in ex_type or "blank" in ex_type:
            ex_type = "fill_blank"
        elif "choice" in ex_type or "select" in ex_type:
            ex_type = "single_choice"

        if ex_type == "single_choice":
            options = ex.get("options") or ex.get("choices") or []
            norm_options = []
            labels = ["A", "B", "C", "D"]
            for i, opt in enumerate(options):
                if isinstance(opt, dict):
                    norm_options.append({
                        "label": _as_str(opt.get("label") or labels[i] if i < 4 else str(i)),
                        "text": _as_str(opt.get("text") or opt.get("content") or opt.get("value") or ""),
                    })
                elif isinstance(opt, str):
                    norm_options.append({"label": labels[i] if i < 4 else str(i), "text": opt})
            normalized.append({
                "type": "single_choice",
                "question": _as_str(ex.get("question") or ex.get("stem") or ex.get("题目") or ""),
                "options": norm_options,
                "correct_label": _as_str(ex.get("correct_label") or ex.get("answer") or ex.get("correct") or "A").upper()[:1],
                "explanation": _as_str(ex.get("explanation") or ex.get("解析") or ""),
            })
        elif ex_type == "fill_blank":
            normalized.append({
                "type": "fill_blank",
                "passage_with_blanks": _as_str(
                    ex.get("passage_with_blanks") or ex.get("passage") or ex.get("text") or ""
                ),
                "blanks": ex.get("blanks") or [],
                "explanation": _as_str(ex.get("explanation") or ex.get("解析") or ""),
            })

    return {"exercises": normalized}
