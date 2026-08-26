from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


def detect_used_words(text: str, target_words: list[str]) -> list[str]:
    text_lower = text.lower()
    used: list[str] = []
    for word in target_words:
        if re.search(rf"\b{re.escape(word.lower())}\b", text_lower):
            used.append(word)
    return used


def merge_words_used(existing: list[str], new_words: list[str]) -> list[str]:
    merged = list(existing)
    for word in new_words:
        if word not in merged:
            merged.append(word)
    return merged


@dataclass
class ConversationMessageRecord:
    id: int | None
    role: str
    content: str
    meta: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None


@dataclass
class ConversationSessionRecord:
    """Conversation session aggregate root (persistence-independent)."""

    id: int | None
    user_id: int | None
    scenario_id: int | None
    title: str
    theme: str
    level: str
    role_ai: str
    role_user: str
    scene_brief: dict[str, Any]
    target_words: list[str]
    mode: str = "text"
    status: str = "active"
    turn_count: int = 0
    words_used: list[str] = field(default_factory=list)
    summary: str | None = None
    created_at: datetime | None = None
    ended_at: datetime | None = None
    messages: list[ConversationMessageRecord] = field(default_factory=list)

    @staticmethod
    def create_new(
        *,
        user_id: int,
        scenario_id: int | None,
        title: str,
        theme: str,
        level: str,
        role_ai: str,
        role_user: str,
        scene_brief: dict[str, Any],
        target_words: list[str],
        show_chinese_hint: bool,
    ) -> ConversationSessionRecord:
        brief = {**scene_brief, "show_chinese_hint": show_chinese_hint}
        return ConversationSessionRecord(
            id=None,
            user_id=user_id,
            scenario_id=scenario_id,
            title=title,
            theme=theme,
            level=level,
            role_ai=role_ai,
            role_user=role_user,
            scene_brief=brief,
            target_words=list(target_words),
            mode="text",
            status="active",
            turn_count=0,
            words_used=[],
            summary=None,
        )

    def get_show_chinese_hint(self) -> bool:
        return bool(self.scene_brief.get("show_chinese_hint", True))

    def set_show_chinese_hint(self, show_chinese_hint: bool) -> None:
        self.scene_brief = {**self.scene_brief, "show_chinese_hint": show_chinese_hint}

    def record_user_turn(
        self,
        content: str,
        *,
        meta: dict[str, Any] | None = None,
    ) -> ConversationMessageRecord:
        if self.status != "active":
            raise ValueError("Conversation has ended")
        used = detect_used_words(content, self.target_words)
        self.words_used = merge_words_used(self.words_used, used)
        self.turn_count += 1
        return ConversationMessageRecord(
            id=None,
            role="user",
            content=content,
            meta={**(meta or {}), "used_words": used},
        )

    def end(self, *, summary: str, ended_at: datetime) -> None:
        self.status = "ended"
        self.summary = summary
        self.ended_at = ended_at

    def missing_words(self) -> list[str]:
        return [w for w in self.target_words if w not in self.words_used]
