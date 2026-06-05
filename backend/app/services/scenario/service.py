from __future__ import annotations

import json
import random
from datetime import date, datetime

from sqlalchemy.orm import Session, joinedload

from app.config import Settings, get_settings
from app.models.exercise import Exercise
from app.models.scenario import Scenario, ScenarioWord
from app.models.word import Word, WordGroup, WordGroupMember
from app.services.ai.openai_provider import AIProviderError, get_ai_provider
from app.services.ai.prompts import EXERCISE_SCHEMA, SCENARIO_SCHEMA, build_exercise_prompt, build_scenario_prompt
from app.services.exercise.generator import save_exercises_from_ai
from app.services.vocabulary.import_words import word_to_dict
from app.services.vocabulary.srs import get_due_word_ids
from app.utils.json_helpers import dump_json_field, parse_json_field


class ScenarioService:
    def __init__(self, db: Session, settings: Settings | None = None):
        self.db = db
        self.settings = settings or get_settings()
        self.ai = get_ai_provider(self.settings)

    def pick_words(
        self,
        level: str,
        theme: str | None,
        word_ids: list[int],
        word_count: int,
        device_id: str,
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
            due_ids = get_due_word_ids(self.db, device_id, word_count * 2)
            if due_ids:
                due_words = self.db.query(Word).filter(Word.id.in_(due_ids)).limit(word_count).all()
                if len(due_words) >= 5:
                    return due_words

        all_words = query.all()
        if len(all_words) <= word_count:
            return all_words
        return random.sample(all_words, word_count)

    async def generate_scenario(
        self,
        level: str = "cet4",
        theme: str | None = None,
        word_ids: list[int] | None = None,
        scenario_type: str = "narrative",
        device_id: str = "default",
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
            device_id=device_id,
            prefer_review=prefer_review,
        )
        if len(words) < 3:
            raise ValueError("Not enough words available for scenario generation")

        word_dicts = [word_to_dict(w) for w in words]
        messages = build_scenario_prompt(word_dicts, level, theme, scenario_type)

        try:
            result = await self.ai.chat_json(messages, SCENARIO_SCHEMA)
        except AIProviderError:
            raise

        content = {
            "passage": result["passage"],
            "summary_zh": result.get("summary_zh", ""),
            "fun_fact": result.get("fun_fact"),
            "word_usage": result.get("word_usage", []),
        }
        dialogue = result.get("dialogue", [])

        scenario = Scenario(
            title=result.get("title", f"Scenario: {theme}"),
            theme=theme,
            level=level,
            scenario_type=scenario_type,
            content=dump_json_field(content),
            dialogue=dump_json_field(dialogue),
            device_id=device_id,
            is_daily=is_daily,
            daily_date=date.today().isoformat() if is_daily else None,
            daily_kind=daily_kind,
        )
        self.db.add(scenario)
        self.db.flush()

        for word in words:
            self.db.add(ScenarioWord(scenario_id=scenario.id, word_id=word.id))

        target_lemmas = [w.lemma for w in words]
        exercise_messages = build_exercise_prompt(scenario.title, content["passage"], target_lemmas)
        exercise_result = await self.ai.chat_json(exercise_messages, EXERCISE_SCHEMA)
        save_exercises_from_ai(self.db, scenario.id, exercise_result.get("exercises", []))

        self.db.commit()
        self.db.refresh(scenario)
        return scenario

    async def ensure_daily_scenarios(self, device_id: str) -> list[Scenario]:
        today = date.today().isoformat()
        existing = (
            self.db.query(Scenario)
            .filter(Scenario.device_id == device_id, Scenario.is_daily.is_(True), Scenario.daily_date == today)
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
                level=level,
                device_id=device_id,
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

    def list_scenarios(self, device_id: str, skip: int = 0, limit: int = 20) -> tuple[list[Scenario], int]:
        q = self.db.query(Scenario).filter(Scenario.device_id == device_id)
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
