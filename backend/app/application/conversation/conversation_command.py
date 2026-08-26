from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from app.application.conversation.conversation_input import (
    ConversationDetailOutput,
    ConversationMessageOutput,
    ConversationSummaryOutput,
    CreateConversationInput,
    EndConversationInput,
    SendMessageInput,
    UpdateSettingsInput,
)
from app.application.conversation.conversation_mapping import (
    build_chat_messages,
    message_to_output,
    session_to_detail,
)
from app.application.progress.progress_command import RecordAnswerCommand, RecordAnswerInput
from app.domains.conversation.conversation_domain import (
    ConversationMessageRecord,
    ConversationSessionRecord,
)
from app.domains.conversation.conversation_repository import ConversationRepository
from app.domains.scenario.scenario_ports import LlmPort, WordSelectionPort
from app.domains.scenario.scenario_repository import ScenarioRepository
from app.infrastructure.unit_of_work import UnitOfWorkFactory
from app.services.ai.openai_provider import AIProviderError
from app.services.conversation.prompts import (
    CONVERSATION_SETUP_SCHEMA,
    CONVERSATION_SUMMARY_SCHEMA,
    build_setup_prompt,
    build_summary_messages,
)
from app.utils.time import utc_now


def _mock_reply(messages: list[dict[str, str]], *, show_chinese_hint: bool = True) -> str:
    user_msgs = [m["content"] for m in messages if m["role"] == "user"]
    last = user_msgs[-1] if user_msgs else ""
    if "Start the role-play" in last:
        if show_chinese_hint:
            return (
                "Good morning! Welcome to the airport check-in desk. "
                "May I help you with your reservation today? (您好，请问需要办理什么？)"
            )
        return (
            "Good morning! Welcome to the airport check-in desk. "
            "May I help you with your reservation today?"
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


async def _chat_with_mock(
    llm: LlmPort,
    messages: list[dict[str, str]],
    *,
    show_chinese_hint: bool = True,
) -> str:
    if hasattr(llm, "chat_stream"):
        chunks: list[str] = []
        async for token in llm.chat_stream(messages):
            chunks.append(token)
        text = "".join(chunks).strip()
        if text:
            return text
    try:
        return await llm.chat_text(messages)
    except (AIProviderError, Exception):
        return _mock_reply(messages, show_chinese_hint=show_chinese_hint)


class CreateSessionCommand:
    def __init__(
        self,
        uow_factory: UnitOfWorkFactory,
        repository_factory: Any,
        word_selection_factory: Any,
        scenario_repository_factory: Any,
        llm: LlmPort,
    ):
        self._uow_factory = uow_factory
        self._repository_factory = repository_factory
        self._word_selection_factory = word_selection_factory
        self._scenario_repository_factory = scenario_repository_factory
        self._llm = llm

    async def _setup_from_scenario(self, scenario_id: int, level: str) -> dict[str, Any]:
        with self._uow_factory() as uow:
            repo: ScenarioRepository = self._scenario_repository_factory(uow.session)
            scenario = repo.get_by_id(scenario_id)
            if not scenario:
                raise ValueError("Scenario not found")

            target_words = [w.lemma for w in scenario.words if w.lemma]
            role_ai = "Assistant"
            role_user = "Learner"
            if scenario.dialogue:
                speakers = [d.speaker for d in scenario.dialogue if d.speaker]
                if len(speakers) >= 2:
                    role_ai = speakers[0]
                    role_user = speakers[1]

            scene_brief = {
                "location": scenario.theme,
                "task": scenario.content.summary_zh or scenario.title,
                "background_zh": scenario.content.summary_zh or "",
                "passage_excerpt": (scenario.content.passage or "")[:300],
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
        user_id: int,
        level: str,
        theme: str,
        word_count: int,
    ) -> dict[str, Any]:
        with self._uow_factory() as uow:
            picker: WordSelectionPort = self._word_selection_factory(uow.session)
            word_dicts = picker.pick_words(
                user_id=user_id,
                level=level,
                theme=theme if theme != "daily" else None,
                word_ids=[],
                word_count=word_count,
                word_strategy="smart",
                exclude_recent=True,
            )
            lemmas = [str(w.get("lemma", "")) for w in word_dicts if w.get("lemma")]

        role_ai = "Clerk"
        role_user = "Traveler"
        title = f"{theme.replace('_', ' ').title()} Conversation"
        scene_brief: dict[str, Any] = {
            "location": theme,
            "task": "Practice a natural conversation using target vocabulary",
            "background_zh": f"围绕{theme}主题进行英语对话练习",
        }

        try:
            setup = await self._llm.chat_json(
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

    async def execute(self, inp: CreateConversationInput) -> ConversationDetailOutput:
        if inp.scenario_id:
            session_data = await self._setup_from_scenario(inp.scenario_id, inp.level)
        else:
            session_data = await self._setup_standalone(
                user_id=inp.user_id,
                level=inp.level,
                theme=inp.theme or "daily",
                word_count=inp.word_count,
            )

        draft = ConversationSessionRecord.create_new(
            user_id=inp.user_id,
            scenario_id=inp.scenario_id,
            title=session_data["title"],
            theme=session_data["theme"],
            level=inp.level,
            role_ai=session_data["role_ai"],
            role_user=session_data["role_user"],
            scene_brief=session_data["scene_brief"],
            target_words=session_data["target_words"],
            show_chinese_hint=inp.show_chinese_hint,
        )

        opening_messages = build_chat_messages(draft, inp.show_chinese_hint)
        opening_messages.append(
            {
                "role": "user",
                "content": (
                    "Start the role-play now. Greet the learner and open the conversation "
                    "with your first line as your character. Keep it to 1-2 sentences."
                ),
            }
        )
        opening = await _chat_with_mock(
            self._llm,
            opening_messages,
            show_chinese_hint=inp.show_chinese_hint,
        )

        with self._uow_factory() as uow:
            repo: ConversationRepository = self._repository_factory(uow.session)
            saved = repo.add(draft)
            assert saved.id is not None
            repo.add_message(
                saved.id,
                ConversationMessageRecord(
                    id=None,
                    role="assistant",
                    content=opening,
                    meta={"kind": "opening"},
                ),
            )
            uow.commit()
            full = repo.get_by_id(saved.id, inp.user_id)
            assert full is not None
            return session_to_detail(full)


class UpdateSettingsCommand:
    def __init__(self, uow_factory: UnitOfWorkFactory, repository_factory: Any):
        self._uow_factory = uow_factory
        self._repository_factory = repository_factory

    def execute(self, inp: UpdateSettingsInput) -> ConversationDetailOutput:
        with self._uow_factory() as uow:
            repo: ConversationRepository = self._repository_factory(uow.session)
            session = repo.get_by_id(inp.session_id, inp.user_id)
            if not session:
                raise ValueError("Conversation not found")
            session.set_show_chinese_hint(inp.show_chinese_hint)
            repo.save(session)
            uow.commit()
            full = repo.get_by_id(inp.session_id, inp.user_id)
            assert full is not None
            return session_to_detail(full)


class SendMessageCommand:
    def __init__(
        self,
        uow_factory: UnitOfWorkFactory,
        repository_factory: Any,
        llm: LlmPort,
    ):
        self._uow_factory = uow_factory
        self._repository_factory = repository_factory
        self._llm = llm

    async def stream(self, inp: SendMessageInput) -> AsyncIterator[str]:
        with self._uow_factory() as uow:
            repo: ConversationRepository = self._repository_factory(uow.session)
            session = repo.get_by_id(inp.session_id, inp.user_id)
            if not session:
                raise ValueError("Conversation not found")
            if session.status != "active":
                raise ValueError("Conversation has ended")

            session.set_show_chinese_hint(inp.show_chinese_hint)
            user_msg = session.record_user_turn(inp.content, meta=inp.user_meta)
            repo.save(session)
            repo.add_message(session.id, user_msg)  # type: ignore[arg-type]
            # Reload messages for chat context after flush inside add_message
            session = repo.get_by_id(inp.session_id, inp.user_id)
            assert session is not None
            chat_messages = build_chat_messages(session, inp.show_chinese_hint)
            uow.commit()

        full_parts: list[str] = []
        async for token in self._llm.chat_stream(chat_messages):
            full_parts.append(token)
            yield token

        assistant_content = "".join(full_parts).strip()
        if not assistant_content:
            assistant_content = _mock_reply(chat_messages, show_chinese_hint=inp.show_chinese_hint)

        with self._uow_factory() as uow:
            repo = self._repository_factory(uow.session)
            assistant_msg = repo.add_message(
                inp.session_id,
                ConversationMessageRecord(
                    id=None,
                    role="assistant",
                    content=assistant_content,
                    meta={"kind": "reply"},
                ),
            )
            uow.commit()
            assert assistant_msg.id is not None
            yield f"\n__DONE__:{assistant_msg.id}"

    async def execute(self, inp: SendMessageInput) -> ConversationMessageOutput:
        message_id = 0
        async for chunk in self.stream(inp):
            if chunk.startswith("\n__DONE__:"):
                message_id = int(chunk.split(":")[1])
        with self._uow_factory() as uow:
            repo: ConversationRepository = self._repository_factory(uow.session)
            session = repo.get_by_id(inp.session_id, inp.user_id)
            if not session:
                raise AIProviderError("Failed to save assistant message")
            msg = next((m for m in session.messages if m.id == message_id), None)
            if not msg:
                raise AIProviderError("Failed to save assistant message")
            return message_to_output(msg)


class EndSessionCommand:
    def __init__(
        self,
        uow_factory: UnitOfWorkFactory,
        repository_factory: Any,
        llm: LlmPort,
        record_answer: RecordAnswerCommand,
    ):
        self._uow_factory = uow_factory
        self._repository_factory = repository_factory
        self._llm = llm
        self._record_answer = record_answer

    async def execute(self, inp: EndConversationInput) -> ConversationSummaryOutput:
        with self._uow_factory() as uow:
            repo: ConversationRepository = self._repository_factory(uow.session)
            session = repo.get_by_id(inp.session_id, inp.user_id)
            if not session:
                raise ValueError("Conversation not found")

            if session.status == "ended" and session.summary:
                return ConversationSummaryOutput(
                    session_id=session.id or inp.session_id,
                    summary=session.summary,
                    words_used=list(session.words_used),
                    missing_words=session.missing_words(),
                    grammar_feedback="",
                    vocabulary_feedback="",
                    suggestions=[],
                )

            target_words = list(session.target_words)
            words_used = list(session.words_used)
            title = session.title
            user_id = session.user_id
            transcript_lines = [
                f"{msg.role}: {msg.content}"
                for msg in sorted(session.messages, key=lambda m: m.id if m.id is not None else 0)
                if msg.role in ("user", "assistant")
            ]

        transcript = "\n".join(transcript_lines)
        summary_data: dict[str, Any] = {
            "summary": "本次对话练习已完成，继续保持！",
            "grammar_feedback": "整体表达清晰，可继续练习完整句型。",
            "vocabulary_feedback": f"已使用 {len(words_used)}/{len(target_words)} 个目标词。",
            "suggestions": ["复习未使用的目标词", "尝试用完整句子回答"],
        }
        try:
            result = await self._llm.chat_json(
                build_summary_messages(title, target_words, words_used, transcript),
                CONVERSATION_SUMMARY_SCHEMA,
            )
            summary_data.update(result)
        except (AIProviderError, Exception):
            pass

        with self._uow_factory() as uow:
            repo = self._repository_factory(uow.session)
            session = repo.get_by_id(inp.session_id, inp.user_id)
            if not session:
                raise ValueError("Conversation not found")

            if words_used and user_id is not None:
                lemma_to_id = repo.resolve_word_ids_by_lemmas(words_used)
                for lemma in words_used:
                    word_id = lemma_to_id.get(lemma)
                    if word_id:
                        self._record_answer.execute_in_session(
                            uow.session,
                            RecordAnswerInput(user_id=user_id, word_id=word_id, correct=True),
                        )

            session.end(summary=summary_data.get("summary", ""), ended_at=utc_now())
            repo.save(session)
            uow.commit()

            return ConversationSummaryOutput(
                session_id=session.id or inp.session_id,
                summary=summary_data.get("summary", ""),
                words_used=words_used,
                missing_words=[w for w in target_words if w not in words_used],
                grammar_feedback=summary_data.get("grammar_feedback", ""),
                vocabulary_feedback=summary_data.get("vocabulary_feedback", ""),
                suggestions=list(summary_data.get("suggestions") or []),
            )
