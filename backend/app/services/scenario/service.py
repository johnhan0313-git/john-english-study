from __future__ import annotations

import json
import random
from app.utils.time import local_today

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.conversation import ConversationSession
from app.models.progress import ScenarioAttempt

from app.config import Settings, get_settings
from app.models.exercise import Exercise
from app.models.scenario import Scenario, ScenarioWord
from app.models.word import WordGroup
from app.services.scenario.word_picker import WordStrategy, pick_words
from app.services.ai.factory import AIProviders, build_providers
from app.services.ai.openai_provider import AIProviderError
from app.services.ai.prompts import EXERCISE_SCHEMA, SCENARIO_SCHEMA, TRANSLATION_SCHEMA, build_exercise_prompt, build_scenario_prompt
from app.services.ai.response_normalizer import (
    WrongResponseTypeError,
    normalize_exercise_response,
    normalize_scenario_response,
)
from app.services.exercise.generator import save_exercises_from_ai
from app.services.vocabulary.import_words import word_to_dict
from app.services.ai.openai_provider import MockAIProvider
from app.utils.json_helpers import dump_json_field, parse_json_field


class ScenarioService:
    def __init__(
        self,
        db: Session,
        settings: Settings | None = None,
        providers: AIProviders | None = None,
    ):
        self.db = db
        self.settings = settings or get_settings()
        resolved = providers or build_providers(self.settings)
        self.ai = resolved.llm

    async def _fetch_scenario_with_retry(self, messages: list[dict[str, str]], retries: int = 2) -> dict:
        last_error: Exception | None = None
        for attempt in range(retries + 1):
            attempt_messages = list(messages)
            if attempt > 0:
                attempt_messages.append({
                    "role": "user",
                    "content": (
                        "Your previous response was wrong. Return a SCENARIO only.\n"
                        "Required keys: title, theme, passage, dialogue, word_usage, summary_zh, passage_zh, fun_fact.\n"
                        "Do NOT return 'exercises'. The 'passage' field must contain 150+ words of English text."
                    ),
                })
            try:
                raw = await self.ai.chat_json(attempt_messages, SCENARIO_SCHEMA, task="scenario")
                return normalize_scenario_response(raw)
            except WrongResponseTypeError as e:
                last_error = e
            except AIProviderError as e:
                raise
        raise AIProviderError(str(last_error) if last_error else "Scenario generation failed")

    async def _fetch_exercises_with_retry(self, messages: list[dict[str, str]], retries: int = 2) -> dict:
        last_error: Exception | None = None
        for attempt in range(retries + 1):
            try:
                raw = await self.ai.chat_json(messages, EXERCISE_SCHEMA, task="exercise")
                result = normalize_exercise_response(raw)
                if result.get("exercises"):
                    return result
                last_error = AIProviderError("AI returned empty exercises list")
            except AIProviderError as e:
                last_error = e
        raise AIProviderError(str(last_error) if last_error else "Exercise generation failed")

    async def generate_scenario(
        self,
        user_id: int,
        level: str = "cet4",
        theme: str | None = None,
        word_ids: list[int] | None = None,
        scenario_type: str = "narrative",
        word_count: int = 10,
        is_daily: bool = False,
        daily_kind: str | None = None,
        word_strategy: WordStrategy = "smart",
        exclude_recent: bool = True,
        prefer_review: bool = False,
    ) -> Scenario:
        if prefer_review and word_strategy == "smart":
            word_strategy = "review"

        if not theme:
            themes = [g.slug for g in self.db.query(WordGroup).all()]
            theme = random.choice(themes) if themes else "daily"

        words = pick_words(
            self.db,
            level=level,
            theme=theme,
            word_ids=word_ids or [],
            word_count=word_count,
            user_id=user_id,
            word_strategy=word_strategy,
            exclude_recent=exclude_recent,
        )
        if len(words) < 3:
            raise ValueError("Not enough words available for scenario generation")

        word_dicts = [word_to_dict(w) for w in words]
        messages = build_scenario_prompt(word_dicts, level, theme, scenario_type)
        self.db.commit()

        result = await self._fetch_scenario_with_retry(messages)

        content = {
            "passage": result["passage"],
            "summary_zh": result.get("summary_zh", ""),
            "fun_fact": result.get("fun_fact"),
            "word_usage": result.get("word_usage", []),
        }
        dialogue = result.get("dialogue", [])

        scenario = Scenario(
            title=result.get("title") or f"Scenario: {theme}",
            theme=theme,
            level=level,
            scenario_type=scenario_type,
            content=dump_json_field(content),
            dialogue=dump_json_field(dialogue),
            user_id=user_id,
            is_daily=is_daily,
            daily_date=local_today(self.settings.app_timezone).isoformat() if is_daily else None,
            daily_kind=daily_kind,
        )
        self.db.add(scenario)
        self.db.flush()

        for word in words:
            self.db.add(ScenarioWord(scenario_id=scenario.id, word_id=word.id))

        target_lemmas = [w.lemma for w in words]
        scenario_id = scenario.id
        self.db.commit()

        exercise_messages = build_exercise_prompt(scenario.title, content["passage"], target_lemmas)
        exercise_result = await self._fetch_exercises_with_retry(exercise_messages)
        save_exercises_from_ai(self.db, scenario_id, exercise_result.get("exercises", []))

        self.db.commit()
        self.db.refresh(scenario)
        return scenario

    async def ensure_daily_scenarios(self, user_id: int) -> list[Scenario]:
        today = local_today(self.settings.app_timezone).isoformat()
        existing = (
            self.db.query(Scenario)
            .filter(Scenario.user_id == user_id, Scenario.is_daily.is_(True), Scenario.daily_date == today)
            .order_by(Scenario.id)
            .all()
        )
        if len(existing) >= self.settings.daily_scenario_count:
            return existing

        kinds = [
            ("review", "cet4", "review"),
            ("new", "cet4", "new"),
            ("challenge", "cet6", "smart"),
        ]
        generated = list(existing)
        for kind, level, strategy in kinds:
            if any(s.daily_kind == kind for s in generated):
                continue
            scenario = await self.generate_scenario(
                user_id=user_id,
                level=level,
                is_daily=True,
                daily_kind=kind,
                word_strategy=strategy,
            )
            generated.append(scenario)
        return generated

    def get_scenario(self, scenario_id: int) -> Scenario | None:
        return (
            self.db.query(Scenario)
            .options(joinedload(Scenario.words).joinedload(ScenarioWord.word))
            .options(joinedload(Scenario.exercises))
            .filter(Scenario.id == scenario_id)
            .first()
        )

    def list_scenarios(self, user_id: int, skip: int = 0, limit: int = 20) -> tuple[list[Scenario], int]:
        q = self.db.query(Scenario).filter(Scenario.user_id == user_id)
        total = q.count()
        items = (
            q.options(joinedload(Scenario.words), joinedload(Scenario.exercises))
            .order_by(Scenario.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return items, total

    def scenarios_to_briefs(self, user_id: int, scenarios: list[Scenario]) -> list[dict]:
        if not scenarios:
            return []
        scenario_ids = [s.id for s in scenarios]
        attempt_rows = (
            self.db.query(
                ScenarioAttempt.scenario_id,
                func.max(
                    ScenarioAttempt.correct_questions * 1.0 / func.nullif(ScenarioAttempt.total_questions, 0)
                ).label("best_score"),
                func.count(ScenarioAttempt.id).label("attempt_count"),
            )
            .filter(ScenarioAttempt.user_id == user_id, ScenarioAttempt.scenario_id.in_(scenario_ids))
            .group_by(ScenarioAttempt.scenario_id)
            .all()
        )
        attempt_map = {row.scenario_id: row for row in attempt_rows}

        conv_counts = (
            self.db.query(ConversationSession.scenario_id, func.count(ConversationSession.id))
            .filter(
                ConversationSession.user_id == user_id,
                ConversationSession.scenario_id.in_(scenario_ids),
            )
            .group_by(ConversationSession.scenario_id)
            .all()
        )
        conv_map = dict(conv_counts)

        briefs: list[dict] = []
        for scenario in scenarios:
            attempt = attempt_map.get(scenario.id)
            best_score = float(attempt.best_score) if attempt and attempt.best_score is not None else None
            is_completed = attempt is not None and attempt.attempt_count > 0
            briefs.append(
                self.scenario_to_brief(
                    scenario,
                    user_id=user_id,
                    best_score=best_score,
                    is_completed=is_completed,
                    conversation_count=conv_map.get(scenario.id, 0),
                )
            )
        return briefs

    def scenario_to_detail(self, scenario: Scenario) -> dict:
        content = parse_json_field(scenario.content, {})
        words = [sw.word.lemma for sw in scenario.words if sw.word]
        return {
            "id": scenario.id,
            "title": scenario.title,
            "theme": scenario.theme,
            "level": scenario.level,
            "scenario_type": scenario.scenario_type,
            "is_daily": scenario.is_daily,
            "daily_kind": scenario.daily_kind,
            "word_count": len(words),
            "created_at": scenario.created_at,
            "content": content,
            "dialogue": parse_json_field(scenario.dialogue, []),
            "words": words,
            "has_audio": bool(scenario.audio_path),
            "exercise_count": len(scenario.exercises),
        }

    def scenario_to_brief(
        self,
        scenario: Scenario,
        *,
        user_id: int | None = None,
        best_score: float | None = None,
        is_completed: bool = False,
        conversation_count: int = 0,
    ) -> dict:
        content = parse_json_field(scenario.content, {})
        summary_zh = content.get("summary_zh") or ""
        summary_preview = summary_zh[:80] if summary_zh else None
        word_count = len(scenario.words) if scenario.words else 0
        exercise_count = len(scenario.exercises) if scenario.exercises else 0
        return {
            "id": scenario.id,
            "title": scenario.title,
            "theme": scenario.theme,
            "level": scenario.level,
            "scenario_type": scenario.scenario_type,
            "is_daily": scenario.is_daily,
            "daily_kind": scenario.daily_kind,
            "word_count": word_count,
            "created_at": scenario.created_at,
            "summary_preview": summary_preview,
            "is_completed": is_completed,
            "best_score": best_score,
            "conversation_count": conversation_count,
            "exercise_count": exercise_count,
        }

    def _mock_translation(self, content: dict, dialogue: list[dict], theme: str) -> tuple[str, list[dict]]:
        meta = MockAIProvider._THEME_META.get(theme, MockAIProvider._THEME_META["daily"])
        parts = [meta["summary_zh"]]
        for item in content.get("word_usage", []):
            word = _as_str(item.get("word"))
            meaning = _as_str(item.get("meaning_zh"))
            if word and meaning and meaning.lower() != word.lower():
                parts.append(f"在情节发展中，{word}（{meaning}）成为讨论焦点。")
        passage_zh = "\n".join(parts)
        dialogue_zh = [
            {
                "speaker": _as_str(item.get("speaker") or "Speaker"),
                "text": f"{_as_str(item.get('text'))}（对话译文略）",
            }
            for item in dialogue
            if isinstance(item, dict) and _as_str(item.get("text"))
        ]
        return passage_zh, dialogue_zh

    async def get_scenario_translation(self, scenario_id: int) -> dict:
        scenario = self.get_scenario(scenario_id)
        if not scenario:
            raise ValueError("Scenario not found")

        content = parse_json_field(scenario.content, {})
        dialogue = parse_json_field(scenario.dialogue, [])
        cached_dialogue = content.get("dialogue_zh")
        if content.get("passage_zh"):
            return {
                "passage_zh": content["passage_zh"],
                "dialogue_zh": cached_dialogue if isinstance(cached_dialogue, list) else [],
            }

        passage = content.get("passage", "")
        if isinstance(self.ai, MockAIProvider):
            passage_zh, dialogue_zh = self._mock_translation(content, dialogue, scenario.theme)
        else:
            import json

            messages = [
                {
                    "role": "user",
                    "content": (
                        "Translate the following English learning content into natural Simplified Chinese.\n\n"
                        f"Passage:\n{passage}\n\n"
                        f"Dialogue JSON:\n{json.dumps(dialogue, ensure_ascii=False)}"
                    ),
                }
            ]
            raw = await self.ai.chat_json(messages, TRANSLATION_SCHEMA, task="translate")
            passage_zh = _as_str(raw.get("passage_zh")) or _as_str(content.get("summary_zh"))
            dialogue_zh = raw.get("dialogue_zh") if isinstance(raw.get("dialogue_zh"), list) else []

        content["passage_zh"] = passage_zh
        if dialogue_zh:
            content["dialogue_zh"] = dialogue_zh
        scenario.content = dump_json_field(content)
        self.db.commit()

        return {"passage_zh": passage_zh, "dialogue_zh": dialogue_zh}


def _as_str(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()
