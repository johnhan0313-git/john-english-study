from __future__ import annotations

import re

CONVERSATION_SETUP_SCHEMA = """
{
  "title": "string",
  "role_ai": "string",
  "role_user": "string",
  "scene_brief": {
    "location": "string",
    "task": "string",
    "background_zh": "string"
  }
}
"""

_CHINESE_HINT_SUFFIX = re.compile(
    r"\s*[（(][^）)]*[\u4e00-\u9fff][^）)]*[）)]\s*$"
)


def strip_chinese_hint_suffix(text: str) -> str:
    return _CHINESE_HINT_SUFFIX.sub("", text).strip()


CONVERSATION_SUMMARY_SCHEMA = """
{
  "summary": "string (Chinese, 2-4 sentences)",
  "grammar_feedback": "string (Chinese)",
  "vocabulary_feedback": "string (Chinese)",
  "suggestions": ["string"]
}
"""

CONVERSATION_SUMMARY_PROMPT = """Summarize this English role-play conversation for a CET learner.
Return JSON with: summary, grammar_feedback, vocabulary_feedback, suggestions (array).
Be encouraging and specific."""


def build_system_prompt(
    *,
    role_ai: str,
    role_user: str,
    level: str,
    scene_brief: dict,
    target_words: list[str],
    show_chinese_hint: bool,
) -> str:
    location = scene_brief.get("location", "a real-life setting")
    task = scene_brief.get("task", "complete a practical conversation")
    background = scene_brief.get("background_zh", "")
    words = ", ".join(target_words) if target_words else "none specified"
    hint_rule = (
        "After your English reply, add ONE short Chinese gloss in parentheses, e.g. (你好)."
        if show_chinese_hint
        else "Reply in English only. Never add Chinese translations, glosses, or parenthetical Chinese."
    )
    return (
        f"You are role-playing as {role_ai} in a 1-on-1 English learning scene.\n"
        f"The learner plays {role_user}.\n"
        f"Setting: {location}. Goal: {task}.\n"
        f"Background: {background}\n"
        f"Target CET level: {level.upper()}.\n"
        f"Target vocabulary to encourage: {words}.\n"
        "Rules:\n"
        "- Reply in 1-3 short English sentences. Stay in character.\n"
        "- Ask a follow-up question when natural to keep the dialogue going.\n"
        "- If the learner uses Chinese, give a brief English model phrase, then encourage English.\n"
        f"- {hint_rule}\n"
        "- Never mention that you are an AI."
    )


def build_setup_prompt(level: str, theme: str, words: list[str]) -> list[dict[str, str]]:
    word_list = ", ".join(words)
    return [
        {
            "role": "user",
            "content": (
                f"Design a 1-on-1 English role-play setup for CET-{level[-1]} learners.\n"
                f"Theme: {theme or 'daily life'}\n"
                f"Target words: {word_list}\n"
                "Return JSON with title, role_ai, role_user, scene_brief (location, task, background_zh)."
            ),
        }
    ]


def build_summary_messages(
    title: str,
    target_words: list[str],
    words_used: list[str],
    transcript: str,
) -> list[dict[str, str]]:
    missing = [w for w in target_words if w not in words_used]
    return [
        {
            "role": "user",
            "content": (
                f"{CONVERSATION_SUMMARY_PROMPT}\n\n"
                f"Scenario: {title}\n"
                f"Target words: {', '.join(target_words)}\n"
                f"Words used by learner: {', '.join(words_used) or 'none'}\n"
                f"Words not used: {', '.join(missing) or 'none'}\n"
                f"Conversation transcript:\n{transcript}"
            ),
        }
    ]
