from __future__ import annotations

import re
from collections.abc import AsyncIterator
from datetime import datetime

from sqlalchemy.orm import Session, joinedload

from app.config import Settings, get_settings
from app.models.conversation import ConversationMessage, ConversationSession
from app.models.word import Word
from app.services.ai.openai_provider import AIProviderError, get_llm_provider
from app.services.conversation.prompts import (
    CONVERSATION_SETUP_SCHEMA,
    CONVERSATION_SUMMARY_SCHEMA,
    build_setup_prompt,
    build_summary_messages,
    build_system_prompt,
)
from app.services.scenario.service import ScenarioService
from app.services.vocabulary.srs import record_answer
from app.utils.json_helpers import dump_json_field, parse_json_field


def detect_used_words(text: str, target_words: list[str]) -> list[str]:
    text_lower = text.lower()
    used: list[str] = []
    for word in target_words:
        if re.search(rf"\b{re.escape(word.lower())}\b", text_lower):
            used.append(word)
    return used


def merge_words_used(existing: list[str], new_words: list[str]) -> list[str]:
    merged = list(existing)
    for w in new_words:
        if w not in merged:
            merged.append(w)
    return merged


class ConversationService:
    def __init__(self, db: Session, settings: Settings | None = None):
        self.db = db
        self.settings = settings or get_settings()
        self.ai = get_llm_provider(self.settings)
        self.scenario_service = ScenarioService(db, self.settings)

    async def create_session(
        self,
        *,
        device_id: str,
        scenario_id: int | None = None,
        level: str = "cet4",
        theme: str | None = None,
        word_count: int = 8,
        show_chinese_hint: bool = True,
    ) -> ConversationSession:
        if scenario_id:
            session_data = await self._setup_from_scenario(scenario_id, level)
        else:
            session_data = await self._setup_standalone(
                device_id=device_id,
                level=level,
                theme=theme or "daily",
                word_count=word_count,
            )

        session = ConversationSession(
            device_id=device_id,
            scenario_id=scenario_id,
            title=session_data["title"],
            theme=session_data["theme"],
            level=level,
            role_ai=session_data["role_ai"],
            role_user=session_data["role_user"],
            scene_brief=dump_json_field(session_data["scene_brief"]),
            target_words=dump_json_field(session_data["target_words"]),
            mode="text",
            status="active",
        )
        self.db.add(session)
        self.db.flush()

        opening = await self._generate_opening(session, show_chinese_hint)
        self.db.add(ConversationMessage(
            session_id=session.id,
            role="assistant",
            content=opening,
            meta=dump_json_field({"kind": "opening"}),
        ))
        session.turn_count = 0
        self.db.commit()
        self.db.refresh(session)
        return session

    async def _setup_from_scenario(self, scenario_id: int, level: str) -> dict:
        scenario = self.scenario_service.get_scenario(scenario_id)
        if not scenario:
            raise ValueError("Scenario not found")

        content = parse_json_field(scenario.content, {})
        dialogue = parse_json_field(scenario.dialogue, [])
        target_words = [sw.word.lemma for sw in scenario.words if sw.word]

        role_ai = "Assistant"
        role_user = "Learner"
        if dialogue:
            speakers = [d.get("speaker") for d in dialogue if d.get("speaker")]
            if len(speakers) >= 2:
                role_ai = speakers[0]
                role_user = speakers[1]

        scene_brief = {
            "location": scenario.theme,
            "task": content.get("summary_zh", scenario.title),
            "background_zh": content.get("summary_zh", ""),
            "passage_excerpt": (content.get("passage") or "")[:300],
        }

        return {
            "title": scenario.title,
            "theme": scenario.theme,
            "role_ai": role_ai,
            "role_user": role_user,
            "scene_brief": scene_brief,
            "target_words": target_words,
        }

    async def _setup_standalone(
        self,
        *,
        device_id: str,
        level: str,
        theme: str,
        word_count: int,
    ) -> dict:
        words = self.scenario_service.pick_words(
            level=level,
            theme=theme if theme != "daily" else None,
            word_ids=[],
            word_count=word_count,
            device_id=device_id,
        )
        lemmas = [w.lemma for w in words]

        role_ai = "Clerk"
        role_user = "Traveler"
        title = f"{theme.replace('_', ' ').title()} Conversation"
        scene_brief = {
            "location": theme,
            "task": "Practice a natural conversation using target vocabulary",
            "background_zh": f"围绕{theme}主题进行英语对话练习",
        }

        try:
            setup = await self.ai.chat_json(
                build_setup_prompt(level, theme, lemmas),
                CONVERSATION_SETUP_SCHEMA,
            )
            title = setup.get("title", title)
            role_ai = setup.get("role_ai", role_ai)
            role_user = setup.get("role_user", role_user)
            if setup.get("scene_brief"):
                scene_brief = setup["scene_brief"]
        except (AIProviderError, Exception):
            pass

        return {
            "title": title,
            "theme": theme,
            "role_ai": role_ai,
            "role_user": role_user,
            "scene_brief": scene_brief,
            "target_words": lemmas,
        }

    async def _generate_opening(self, session: ConversationSession, show_chinese_hint: bool) -> str:
        system = build_system_prompt(
            role_ai=session.role_ai,
            role_user=session.role_user,
            level=session.level,
            scene_brief=parse_json_field(session.scene_brief, {}),
            target_words=parse_json_field(session.target_words, []),
            show_chinese_hint=show_chinese_hint,
        )
        messages = [
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": (
                    "Start the role-play now. Greet the learner and open the conversation "
                    "with your first line as your character. Keep it to 1-2 sentences."
                ),
            },
        ]
        return await self._chat_with_mock(messages)

    async def _chat_with_mock(self, messages: list[dict[str, str]]) -> str:
        if hasattr(self.ai, "chat_stream"):
            chunks: list[str] = []
            async for token in self.ai.chat_stream(messages):
                chunks.append(token)
            text = "".join(chunks).strip()
            if text:
                return text
        try:
            return await self.ai.chat_text(messages)
        except (AIProviderError, Exception):
            return self._mock_reply(messages)

    def _mock_reply(self, messages: list[dict[str, str]]) -> str:
        user_msgs = [m["content"] for m in messages if m["role"] == "user"]
        last = user_msgs[-1] if user_msgs else ""
        if "Start the role-play" in last:
            return (
                "Good morning! Welcome to the airport check-in desk. "
                "May I help you with your reservation today? (您好，请问需要办理什么？)"
            )
        if any("\u4e00" <= c <= "\u9fff" for c in last):
            return (
                "I understand. Try saying: \"I'd like to check my schedule, please.\" "
                "Could you tell me your flight number?"
            )
        return (
            "That's helpful, thank you. Could you tell me more about your travel plans? "
            "We should confirm your schedule and luggage details."
        )

    def get_session(self, session_id: int, device_id: str | None = None) -> ConversationSession | None:
        q = (
            self.db.query(ConversationSession)
            .options(joinedload(ConversationSession.messages))
            .filter(ConversationSession.id == session_id)
        )
        if device_id:
            q = q.filter(ConversationSession.device_id == device_id)
        return q.first()

    def list_sessions(self, device_id: str, skip: int = 0, limit: int = 20) -> tuple[list[ConversationSession], int]:
        q = self.db.query(ConversationSession).filter(ConversationSession.device_id == device_id)
        total = q.count()
        items = q.order_by(ConversationSession.created_at.desc()).offset(skip).limit(limit).all()
        return items, total

    def session_to_brief(self, session: ConversationSession) -> dict:
        messages = sorted(session.messages, key=lambda m: m.id)
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
        }

    def session_to_detail(self, session: ConversationSession) -> dict:
        return {
            **self.session_to_brief(session),
            "scenario_id": session.scenario_id,
            "scene_brief": parse_json_field(session.scene_brief, {}),
            "summary": session.summary,
            "messages": [self.message_to_dict(m) for m in sorted(session.messages, key=lambda x: x.id)],
        }

    def message_to_dict(self, message: ConversationMessage) -> dict:
        return {
            "id": message.id,
            "role": message.role,
            "content": message.content,
            "meta": parse_json_field(message.meta, {}),
            "created_at": message.created_at,
        }

    def build_chat_messages(self, session: ConversationSession, show_chinese_hint: bool) -> list[dict[str, str]]:
        system = build_system_prompt(
            role_ai=session.role_ai,
            role_user=session.role_user,
            level=session.level,
            scene_brief=parse_json_field(session.scene_brief, {}),
            target_words=parse_json_field(session.target_words, []),
            show_chinese_hint=show_chinese_hint,
        )
        messages: list[dict[str, str]] = [{"role": "system", "content": system}]
        for msg in sorted(session.messages, key=lambda m: m.id):
            if msg.role in ("user", "assistant"):
                messages.append({"role": msg.role, "content": msg.content})
        return messages

    def save_user_message(
        self,
        session: ConversationSession,
        content: str,
        *,
        meta: dict | None = None,
    ) -> ConversationMessage:
        target_words = parse_json_field(session.target_words, [])
        used = detect_used_words(content, target_words)
        words_used = merge_words_used(parse_json_field(session.words_used, []), used)
        session.words_used = dump_json_field(words_used)

        message = ConversationMessage(
            session_id=session.id,
            role="user",
            content=content,
            meta=dump_json_field({**(meta or {}), "used_words": used}),
        )
        self.db.add(message)
        session.turn_count += 1
        self.db.flush()
        return message

    async def stream_assistant_reply(
        self,
        session: ConversationSession,
        user_content: str,
        *,
        show_chinese_hint: bool = True,
        user_meta: dict | None = None,
    ) -> AsyncIterator[str]:
        if session.status != "active":
            raise ValueError("Conversation has ended")

        self.save_user_message(session, user_content, meta=user_meta)
        self.db.refresh(session)
        chat_messages = self.build_chat_messages(session, show_chinese_hint)

        full_parts: list[str] = []
        async for token in self.ai.chat_stream(chat_messages):
            full_parts.append(token)
            yield token

        assistant_content = "".join(full_parts).strip()
        if not assistant_content:
            assistant_content = self._mock_reply(chat_messages)

        assistant_msg = ConversationMessage(
            session_id=session.id,
            role="assistant",
            content=assistant_content,
            meta=dump_json_field({"kind": "reply"}),
        )
        self.db.add(assistant_msg)
        self.db.commit()
        self.db.refresh(assistant_msg)
        yield f"\n__DONE__:{assistant_msg.id}"

    async def send_message(
        self,
        session: ConversationSession,
        content: str,
        *,
        show_chinese_hint: bool = True,
    ) -> ConversationMessage:
        message_id = 0
        async for chunk in self.stream_assistant_reply(session, content, show_chinese_hint=show_chinese_hint):
            if chunk.startswith("\n__DONE__:"):
                message_id = int(chunk.split(":")[1])
        msg = self.db.query(ConversationMessage).filter(ConversationMessage.id == message_id).first()
        if not msg:
            raise AIProviderError("Failed to save assistant message")
        return msg

    async def end_session(self, session: ConversationSession) -> dict:
        if session.status == "ended" and session.summary:
            target_words = parse_json_field(session.target_words, [])
            words_used = parse_json_field(session.words_used, [])
            return {
                "session_id": session.id,
                "summary": session.summary,
                "words_used": words_used,
                "missing_words": [w for w in target_words if w not in words_used],
                "grammar_feedback": "",
                "vocabulary_feedback": "",
                "suggestions": [],
            }

        target_words = parse_json_field(session.target_words, [])
        words_used = parse_json_field(session.words_used, [])
        transcript_lines = []
        for msg in sorted(session.messages, key=lambda m: m.id):
            if msg.role in ("user", "assistant"):
                transcript_lines.append(f"{msg.role}: {msg.content}")
        transcript = "\n".join(transcript_lines)

        summary_data = {
            "summary": "本次对话练习已完成，继续保持！",
            "grammar_feedback": "整体表达清晰，可继续练习完整句型。",
            "vocabulary_feedback": f"已使用 {len(words_used)}/{len(target_words)} 个目标词。",
            "suggestions": ["复习未使用的目标词", "尝试用完整句子回答"],
        }
        try:
            result = await self.ai.chat_json(
                build_summary_messages(session.title, target_words, words_used, transcript),
                CONVERSATION_SUMMARY_SCHEMA,
            )
            summary_data.update(result)
        except (AIProviderError, Exception):
            pass

        self._apply_srs_for_words(session.device_id, words_used)
        session.status = "ended"
        session.ended_at = datetime.utcnow()
        session.summary = summary_data.get("summary", "")
        self.db.commit()

        missing = [w for w in target_words if w not in words_used]
        return {
            "session_id": session.id,
            "summary": summary_data.get("summary", ""),
            "words_used": words_used,
            "missing_words": missing,
            "grammar_feedback": summary_data.get("grammar_feedback", ""),
            "vocabulary_feedback": summary_data.get("vocabulary_feedback", ""),
            "suggestions": summary_data.get("suggestions", []),
        }

    def _apply_srs_for_words(self, device_id: str, lemmas: list[str]) -> None:
        if not lemmas:
            return
        words = self.db.query(Word).filter(Word.lemma.in_(lemmas)).all()
        by_lemma = {w.lemma: w.id for w in words}
        for lemma in lemmas:
            word_id = by_lemma.get(lemma)
            if word_id:
                record_answer(self.db, device_id, word_id, correct=True)
        self.db.commit()
