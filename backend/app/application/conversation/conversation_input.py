from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class CreateConversationInput:
    user_id: int
    scenario_id: int | None = None
    level: str = "cet4"
    theme: str | None = None
    word_count: int = 8
    show_chinese_hint: bool = True


@dataclass(frozen=True)
class GetConversationInput:
    session_id: int
    user_id: int


@dataclass(frozen=True)
class ListConversationsInput:
    user_id: int
    skip: int = 0
    limit: int = 20


@dataclass(frozen=True)
class SendMessageInput:
    session_id: int
    user_id: int
    content: str
    show_chinese_hint: bool = True
    user_meta: dict[str, Any] | None = None


@dataclass(frozen=True)
class UpdateSettingsInput:
    session_id: int
    user_id: int
    show_chinese_hint: bool


@dataclass(frozen=True)
class EndConversationInput:
    session_id: int
    user_id: int


@dataclass
class ConversationMessageOutput:
    id: int
    role: str
    content: str
    meta: dict[str, Any]
    created_at: datetime


@dataclass
class ConversationBriefOutput:
    id: int
    title: str
    theme: str
    level: str
    role_ai: str
    role_user: str
    mode: str
    status: str
    turn_count: int
    target_words: list[str]
    words_used: list[str]
    last_message: str | None
    created_at: datetime
    scenario_id: int | None
    ended_at: datetime | None


@dataclass
class ConversationDetailOutput(ConversationBriefOutput):
    scene_brief: dict[str, Any] = field(default_factory=dict)
    summary: str | None = None
    messages: list[ConversationMessageOutput] = field(default_factory=list)


@dataclass
class ConversationListOutput:
    items: list[ConversationBriefOutput]
    total: int


@dataclass
class ConversationSummaryOutput:
    session_id: int
    summary: str
    words_used: list[str]
    missing_words: list[str]
    grammar_feedback: str = ""
    vocabulary_feedback: str = ""
    suggestions: list[str] = field(default_factory=list)
