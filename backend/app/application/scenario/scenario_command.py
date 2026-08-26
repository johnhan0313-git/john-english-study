from __future__ import annotations

from dataclasses import asdict
from typing import Any

from sqlalchemy.exc import IntegrityError

from app.application.scenario.scenario_input import (
    CreateMissingDailySlotsInput,
    DailyScenariosOutput,
    GenerateScenarioInput,
    ScenarioBriefOutput,
    ScenarioDetailOutput,
    ScenarioTranslationOutput,
)
from app.domains.scenario.scenario_domain import (
    DAILY_SLOT_KINDS,
    DialogueLine,
    ScenarioAggregate,
    ScenarioContent,
)
from app.domains.scenario.scenario_ports import ExerciseDraftPort, LlmPort, WordSelectionPort
from app.domains.scenario.scenario_repository import ScenarioRepository
from app.infrastructure.unit_of_work import UnitOfWorkFactory
from app.services.ai.openai_provider import AIProviderError, MockAIProvider
from app.services.ai.prompts import EXERCISE_SCHEMA, SCENARIO_SCHEMA, TRANSLATION_SCHEMA, build_exercise_prompt, build_scenario_prompt
from app.services.ai.response_normalizer import WrongResponseTypeError, normalize_exercise_response, normalize_scenario_response


def _as_str(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _content_dict(content: ScenarioContent) -> dict[str, Any]:
    data: dict[str, Any] = {
        "passage": content.passage,
        "summary_zh": content.summary_zh,
        "fun_fact": content.fun_fact,
        "word_usage": content.word_usage,
    }
    if content.passage_zh:
        data["passage_zh"] = content.passage_zh
    if content.dialogue_zh is not None:
        data["dialogue_zh"] = content.dialogue_zh
    return data


def aggregate_to_brief(scenario: ScenarioAggregate, **extra: Any) -> ScenarioBriefOutput:
    summary = scenario.content.summary_zh or ""
    return ScenarioBriefOutput(
        id=scenario.id or 0,
        title=scenario.title,
        theme=scenario.theme,
        level=scenario.level,
        scenario_type=scenario.scenario_type,
        is_daily=scenario.is_daily,
        daily_kind=scenario.daily_kind,
        word_count=len(scenario.words),
        created_at=scenario.created_at,  # type: ignore[arg-type]
        summary_preview=summary[:80] if summary else None,
        exercise_count=scenario.exercise_count,
        **extra,
    )


def aggregate_to_detail(scenario: ScenarioAggregate) -> ScenarioDetailOutput:
    brief = aggregate_to_brief(scenario)
    return ScenarioDetailOutput(
        **asdict(brief),
        content=_content_dict(scenario.content),
        dialogue=[{"speaker": d.speaker, "text": d.text} for d in scenario.dialogue],
        words=[w.lemma for w in scenario.words if w.lemma],
        has_audio=bool(scenario.audio_path),
    )


class GenerateScenarioCommand:
    def __init__(
        self,
        uow_factory: UnitOfWorkFactory,
        repository_factory: Any,
        word_selection_factory: Any,
        exercise_draft_factory: Any,
        llm: LlmPort,
        timezone: str,
    ):
        self._uow_factory = uow_factory
        self._repository_factory = repository_factory
        self._word_selection_factory = word_selection_factory
        self._exercise_draft_factory = exercise_draft_factory
        self._llm = llm
        self._timezone = timezone

    async def _fetch_scenario_with_retry(self, messages: list[dict[str, str]], retries: int = 2) -> dict:
        last_error: Exception | None = None
        for attempt in range(retries + 1):
            attempt_messages = list(messages)
            if attempt > 0:
                attempt_messages.append(
                    {
                        "role": "user",
                        "content": (
                            "Your previous response was wrong. Return a SCENARIO only.\n"
                            "Required keys: title, theme, passage, dialogue, word_usage, summary_zh, passage_zh, fun_fact.\n"
                            "Do NOT return 'exercises'. The 'passage' field must contain 150+ words of English text."
                        ),
                    }
                )
            try:
                raw = await self._llm.chat_json(attempt_messages, SCENARIO_SCHEMA, task="scenario")
                return normalize_scenario_response(raw)
            except WrongResponseTypeError as e:
                last_error = e
            except AIProviderError:
                raise
        raise AIProviderError(str(last_error) if last_error else "Scenario generation failed")

    async def _fetch_exercises_with_retry(self, messages: list[dict[str, str]], retries: int = 2) -> dict:
        last_error: Exception | None = None
        for attempt in range(retries + 1):
            try:
                raw = await self._llm.chat_json(messages, EXERCISE_SCHEMA, task="exercise")
                result = normalize_exercise_response(raw)
                if result.get("exercises"):
                    return result
                last_error = AIProviderError("AI returned empty exercises list")
            except AIProviderError as e:
                last_error = e
        raise AIProviderError(str(last_error) if last_error else "Exercise generation failed")

    async def execute(self, inp: GenerateScenarioInput) -> ScenarioDetailOutput:
        from app.utils.time import local_today

        strategy = inp.word_strategy
        if inp.prefer_review and strategy == "smart":
            strategy = "review"

        with self._uow_factory() as uow:
            repo: ScenarioRepository = self._repository_factory(uow.session)
            picker: WordSelectionPort = self._word_selection_factory(uow.session)

            theme = inp.theme
            if not theme:
                themes = repo.list_theme_slugs()
                import random

                theme = random.choice(themes) if themes else "daily"

            word_dicts = picker.pick_words(
                user_id=inp.user_id,
                level=inp.level,
                theme=theme,
                word_ids=list(inp.word_ids),
                word_count=inp.word_count,
                word_strategy=strategy,
                exclude_recent=inp.exclude_recent,
            )
            if len(word_dicts) < 3:
                raise ValueError("Not enough words available for scenario generation")

            messages = build_scenario_prompt(word_dicts, inp.level, theme, inp.scenario_type)

        # LLM outside the open write transaction to avoid commit-before-AI.
        result = await self._fetch_scenario_with_retry(messages)

        content = ScenarioContent(
            passage=result["passage"],
            summary_zh=result.get("summary_zh", ""),
            fun_fact=result.get("fun_fact"),
            word_usage=result.get("word_usage", []),
        )
        dialogue = [
            DialogueLine(speaker=_as_str(item.get("speaker") or "Speaker"), text=_as_str(item.get("text")))
            for item in result.get("dialogue", [])
            if isinstance(item, dict)
        ]
        daily_date = local_today(self._timezone).isoformat() if inp.is_daily else None
        aggregate = ScenarioAggregate.create_generated(
            title=result.get("title") or f"Scenario: {theme}",
            theme=theme,
            level=inp.level,
            scenario_type=inp.scenario_type,
            content=content,
            dialogue=dialogue,
            user_id=inp.user_id,
            word_ids=[int(w["id"]) for w in word_dicts],
            is_daily=inp.is_daily,
            daily_date=daily_date,
            daily_kind=inp.daily_kind,
        )
        # Attach lemmas for response mapping
        lemma_by_id = {int(w["id"]): w.get("lemma", "") for w in word_dicts}
        for ref in aggregate.words:
            ref.lemma = lemma_by_id.get(ref.word_id, "")

        target_lemmas = [w.get("lemma", "") for w in word_dicts]
        exercise_messages = build_exercise_prompt(aggregate.title, content.passage, target_lemmas)
        exercise_result = await self._fetch_exercises_with_retry(exercise_messages)

        with self._uow_factory() as uow:
            repo = self._repository_factory(uow.session)
            exercises: ExerciseDraftPort = self._exercise_draft_factory(uow.session)
            saved = repo.add(aggregate)
            assert saved.id is not None
            count = exercises.save_from_ai(saved.id, exercise_result.get("exercises", []))
            saved.exercise_count = count
            uow.commit()
            # Re-load with relationships for response
            full = repo.get_by_id(saved.id, inp.user_id)
            assert full is not None
            return aggregate_to_detail(full)


class CreateMissingDailySlotsCommand:
    def __init__(
        self,
        generate: GenerateScenarioCommand,
        uow_factory: UnitOfWorkFactory,
        repository_factory: Any,
    ):
        self._generate = generate
        self._uow_factory = uow_factory
        self._repository_factory = repository_factory

    async def execute(self, inp: CreateMissingDailySlotsInput) -> DailyScenariosOutput:
        with self._uow_factory() as uow:
            repo: ScenarioRepository = self._repository_factory(uow.session)
            existing = repo.list_daily(inp.user_id, inp.daily_date)

        if len(existing) >= inp.target_count:
            return DailyScenariosOutput(
                date=inp.daily_date,
                items=[aggregate_to_brief(s) for s in existing],
                generated=False,
            )

        generated = list(existing)
        for kind, level, strategy in DAILY_SLOT_KINDS:
            if any(s.daily_kind == kind for s in generated):
                continue
            try:
                detail = await self._generate.execute(
                    GenerateScenarioInput(
                        user_id=inp.user_id,
                        level=level,
                        word_strategy=strategy,  # type: ignore[arg-type]
                        is_daily=True,
                        daily_kind=kind,
                    )
                )
                with self._uow_factory() as uow:
                    repo = self._repository_factory(uow.session)
                    scenario = repo.get_by_id(detail.id, inp.user_id)
                    if scenario:
                        generated.append(scenario)
            except IntegrityError:
                with self._uow_factory() as uow:
                    repo = self._repository_factory(uow.session)
                    uow.rollback()
                    scenario = repo.get_daily_by_kind(inp.user_id, inp.daily_date, kind)
                    if scenario is None:
                        raise
                    generated.append(scenario)

        return DailyScenariosOutput(
            date=inp.daily_date,
            items=[aggregate_to_brief(s) for s in generated],
            generated=True,
        )


class TranslateScenarioCommand:
    def __init__(
        self,
        uow_factory: UnitOfWorkFactory,
        repository_factory: Any,
        llm: LlmPort,
    ):
        self._uow_factory = uow_factory
        self._repository_factory = repository_factory
        self._llm = llm

    def _mock_translation(self, content: ScenarioContent, dialogue: list[DialogueLine], theme: str) -> tuple[str, list[dict[str, str]]]:
        meta = MockAIProvider._THEME_META.get(theme, MockAIProvider._THEME_META["daily"])
        parts = [meta["summary_zh"]]
        for item in content.word_usage:
            word = _as_str(item.get("word"))
            meaning = _as_str(item.get("meaning_zh"))
            if word and meaning and meaning.lower() != word.lower():
                parts.append(f"在情节发展中，{word}（{meaning}）成为讨论焦点。")
        passage_zh = "\n".join(parts)
        dialogue_zh = [
            {"speaker": d.speaker, "text": f"{d.text}（对话译文略）"}
            for d in dialogue
            if d.text
        ]
        return passage_zh, dialogue_zh

    async def execute(self, scenario_id: int, user_id: int) -> ScenarioTranslationOutput:
        import json

        with self._uow_factory() as uow:
            repo: ScenarioRepository = self._repository_factory(uow.session)
            scenario = repo.get_by_id(scenario_id, user_id)
            if not scenario:
                raise ValueError("Scenario not found")

            if scenario.content.passage_zh:
                return ScenarioTranslationOutput(
                    passage_zh=scenario.content.passage_zh,
                    dialogue_zh=scenario.content.dialogue_zh or [],
                )

            content = scenario.content
            dialogue = scenario.dialogue
            theme = scenario.theme

        if isinstance(self._llm, MockAIProvider):
            passage_zh, dialogue_zh = self._mock_translation(content, dialogue, theme)
        else:
            messages = [
                {
                    "role": "user",
                    "content": (
                        "Translate the following English learning content into natural Simplified Chinese.\n\n"
                        f"Passage:\n{content.passage}\n\n"
                        f"Dialogue JSON:\n{json.dumps([{'speaker': d.speaker, 'text': d.text} for d in dialogue], ensure_ascii=False)}"
                    ),
                }
            ]
            raw = await self._llm.chat_json(messages, TRANSLATION_SCHEMA, task="translate")
            passage_zh = _as_str(raw.get("passage_zh")) or _as_str(content.summary_zh)
            dialogue_zh = raw.get("dialogue_zh") if isinstance(raw.get("dialogue_zh"), list) else []

        with self._uow_factory() as uow:
            repo = self._repository_factory(uow.session)
            scenario = repo.get_by_id(scenario_id, user_id)
            if not scenario:
                raise ValueError("Scenario not found")
            scenario.content.passage_zh = passage_zh
            if dialogue_zh:
                scenario.content.dialogue_zh = dialogue_zh
            repo.save_content(scenario)
            uow.commit()

        return ScenarioTranslationOutput(passage_zh=passage_zh, dialogue_zh=dialogue_zh)
