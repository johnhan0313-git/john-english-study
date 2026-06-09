from __future__ import annotations

import json
import random
from app.utils.time import local_today

from sqlalchemy.orm import Session, joinedload

from app.config import Settings, get_settings
from app.models.exercise import Exercise
from app.models.scenario import Scenario, ScenarioWord
from app.models.word import Word, WordGroup, WordGroupMember
from app.services.ai.factory import AIProviders, build_providers
from app.services.ai.openai_provider import AIProviderError
from app.services.ai.prompts import EXERCISE_SCHEMA, SCENARIO_SCHEMA, build_exercise_prompt, build_scenario_prompt
from app.services.ai.response_normalizer import (
    WrongResponseTypeError,
    normalize_exercise_response,
    normalize_scenario_response,
)
from app.services.exercise.generator import save_exercises_from_ai
from app.services.vocabulary.import_words import word_to_dict
from app.services.vocabulary.srs import get_due_word_ids
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

    def pick_words(
        self,
        level: str,
        theme: str | None,
        word_ids: list[int],
        word_count: int,
        user_id: int,
        prefer_review: bool = False,
    ) -> list[Word]:
        if word_ids:
            words = self.db.query(Word).filter(Word.id.in_(word_ids)).all()
            if words:
                return words[:word_count]

        query = self.db.query(Word)
        if level == "cet4":
            query = query.filter(Word.level.in_(["cet4", "both"]))
        elif level == "cet6":
            query = query.filter(Word.level.in_(["cet6", "both"]))

        if theme:
            group = self.db.query(WordGroup).filter(WordGroup.slug == theme).first()
            if group:
                member_ids = [
                    m.word_id
                    for m in self.db.query(WordGroupMember).filter(WordGroupMember.group_id == group.id).all()
                ]
                if member_ids:
                    query = query.filter(Word.id.in_(member_ids))

        if prefer_review:
            due_ids = get_due_word_ids(self.db, user_id, word_count * 2)
            if due_ids:
                due_words = self.db.query(Word).filter(Word.id.in_(due_ids)).limit(word_count).all()
                if len(due_words) >= 5:
                    return due_words

        all_words = query.all()
        if len(all_words) <= word_count:
            return all_words
        return random.sample(all_words, word_count)

    async def _fetch_scenario_with_retry(self, messages: list[dict[str, str]], retries: int = 2) -> dict:
        last_error: Exception | None = None
        for attempt in range(retries + 1):
            attempt_messages = list(messages)
            if attempt > 0:
                attempt_messages.append({
                    "role": "user",
                    "content": (
                        "Your previous response was wrong. Return a SCENARIO only.\n"
                        "Required keys: title, theme, passage, dialogue, word_usage, summary_zh, fun_fact.\n"
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
        prefer_review: bool = False,
    ) -> Scenario:
        if not theme:
            themes = [g.slug for g in self.db.query(WordGroup).all()]
            theme = random.choice(themes) if themes else "daily"

        words = self.pick_words(
            level=level,
            theme=theme,
            word_ids=word_ids or [],
            word_count=word_count,
            user_id=user_id,
            prefer_review=prefer_review,
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
            ("review", "cet4", True),
            ("new", "cet4", False),
            ("challenge", "cet6", False),
        ]
        generated = list(existing)
        for kind, level, prefer_review in kinds:
            if any(s.daily_kind == kind for s in generated):
                continue
            scenario = await self.generate_scenario(
                user_id=user_id,
                level=level,
                is_daily=True,
                daily_kind=kind,
                prefer_review=prefer_review,
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
        items = q.order_by(Scenario.created_at.desc()).offset(skip).limit(limit).all()
        return items, total

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

    def scenario_to_brief(self, scenario: Scenario) -> dict:
        return {
            "id": scenario.id,
            "title": scenario.title,
            "theme": scenario.theme,
            "level": scenario.level,
            "scenario_type": scenario.scenario_type,
            "is_daily": scenario.is_daily,
            "daily_kind": scenario.daily_kind,
            "word_count": len(scenario.words),
            "created_at": scenario.created_at,
        }
