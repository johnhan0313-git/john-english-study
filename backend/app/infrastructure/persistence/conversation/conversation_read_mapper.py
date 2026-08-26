from __future__ import annotations

"""Conversation session → brief dict for Activity read composition (no write service)."""

from app.models.conversation import ConversationSession
from app.utils.json_helpers import parse_json_field


def conversation_session_to_brief(session: ConversationSession) -> dict:
    messages = sorted(session.messages, key=lambda m: m.id) if session.messages else []
    last = messages[-1].content[:120] if messages else None
    return {
        "id": session.id,
        "title": session.title,
        "theme": session.theme,
        "level": session.level,
        "role_ai": session.role_ai,
        "role_user": session.role_user,
        "mode": session.mode,
        "status": session.status,
        "turn_count": session.turn_count,
        "target_words": parse_json_field(session.target_words, []),
        "words_used": parse_json_field(session.words_used, []),
        "last_message": last,
        "created_at": session.created_at,
        "scenario_id": session.scenario_id,
        "ended_at": session.ended_at,
    }
