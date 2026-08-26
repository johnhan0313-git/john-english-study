from __future__ import annotations

from dataclasses import asdict

from app.application.conversation.conversation_input import (
    ConversationBriefOutput,
    ConversationDetailOutput,
    ConversationMessageOutput,
)
from app.domains.conversation.conversation_domain import (
    ConversationMessageRecord,
    ConversationSessionRecord,
)
from app.services.conversation.prompts import build_system_prompt, strip_chinese_hint_suffix


def message_to_output(message: ConversationMessageRecord) -> ConversationMessageOutput:
    assert message.id is not None
    assert message.created_at is not None
    return ConversationMessageOutput(
        id=message.id,
        role=message.role,
        content=message.content,
        meta=dict(message.meta or {}),
        created_at=message.created_at,
    )


def session_to_brief(session: ConversationSessionRecord) -> ConversationBriefOutput:
    assert session.id is not None
    assert session.created_at is not None
    messages = sorted(
        session.messages,
        key=lambda m: m.id if m.id is not None else 0,
    )
    last = messages[-1].content[:120] if messages else None
    return ConversationBriefOutput(
        id=session.id,
        title=session.title,
        theme=session.theme,
        level=session.level,
        role_ai=session.role_ai,
        role_user=session.role_user,
        mode=session.mode,
        status=session.status,
        turn_count=session.turn_count,
        target_words=list(session.target_words),
        words_used=list(session.words_used),
        last_message=last,
        created_at=session.created_at,
        scenario_id=session.scenario_id,
        ended_at=session.ended_at,
    )


def session_to_detail(session: ConversationSessionRecord) -> ConversationDetailOutput:
    brief = session_to_brief(session)
    messages = [
        message_to_output(m)
        for m in sorted(session.messages, key=lambda x: x.id if x.id is not None else 0)
        if m.id is not None and m.created_at is not None
    ]
    return ConversationDetailOutput(
        **asdict(brief),
        scene_brief=dict(session.scene_brief),
        summary=session.summary,
        messages=messages,
    )


def build_chat_messages(
    session: ConversationSessionRecord,
    show_chinese_hint: bool,
) -> list[dict[str, str]]:
    system = build_system_prompt(
        role_ai=session.role_ai,
        role_user=session.role_user,
        level=session.level,
        scene_brief=session.scene_brief,
        target_words=session.target_words,
        show_chinese_hint=show_chinese_hint,
    )
    messages: list[dict[str, str]] = [{"role": "system", "content": system}]
    for msg in sorted(session.messages, key=lambda m: m.id if m.id is not None else 0):
        if msg.role in ("user", "assistant"):
            content = msg.content
            if msg.role == "assistant" and not show_chinese_hint:
                content = strip_chinese_hint_suffix(content)
            messages.append({"role": msg.role, "content": content})
    return messages
