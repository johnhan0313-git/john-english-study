from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ConversationCreateRequest(BaseModel):
    scenario_id: int | None = None
    level: str = "cet4"
    theme: str | None = None
    word_count: int = Field(default=8, ge=3, le=15)
    show_chinese_hint: bool = True


class ConversationMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    meta: dict = Field(default_factory=dict)
    created_at: datetime


class ConversationBrief(BaseModel):
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
    last_message: str | None = None
    created_at: datetime
    scenario_id: int | None = None
    ended_at: datetime | None = None


class ConversationDetail(ConversationBrief):
    scene_brief: dict = Field(default_factory=dict)
    summary: str | None = None
    messages: list[ConversationMessageResponse] = Field(default_factory=list)


class ConversationListResponse(BaseModel):
    items: list[ConversationBrief]
    total: int


class SendMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=4000)
    show_chinese_hint: bool = True


class ConversationSettingsRequest(BaseModel):
    show_chinese_hint: bool


class EndConversationRequest(BaseModel):
    pass


class ConversationSummaryResponse(BaseModel):
    session_id: int
    summary: str
    words_used: list[str]
    missing_words: list[str]
    grammar_feedback: str = ""
    vocabulary_feedback: str = ""
    suggestions: list[str] = Field(default_factory=list)


class VoiceTurnResponse(BaseModel):
    user_message_id: int
    assistant_message_id: int
    transcript: str
    content: str
    audio_url: str
    used_words: list[str] = Field(default_factory=list)
