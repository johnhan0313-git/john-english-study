from __future__ import annotations

from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.domains.scenario.scenario_domain import (
    DialogueLine,
    ScenarioAggregate,
    ScenarioContent,
    ScenarioListEnrichment,
    ScenarioWordRef,
)
from app.models.conversation import ConversationSession
from app.models.progress import ScenarioAttempt
from app.models.scenario import Scenario, ScenarioWord
from app.models.word import WordGroup
from app.utils.json_helpers import dump_json_field, parse_json_field


def _content_from_orm(raw: Any) -> ScenarioContent:
    data = parse_json_field(raw, {}) or {}
    return ScenarioContent(
        passage=data.get("passage", ""),
        summary_zh=data.get("summary_zh", ""),
        fun_fact=data.get("fun_fact"),
        word_usage=data.get("word_usage", []) or [],
        passage_zh=data.get("passage_zh"),
        dialogue_zh=data.get("dialogue_zh") if isinstance(data.get("dialogue_zh"), list) else None,
    )


def _dialogue_from_orm(raw: Any) -> list[DialogueLine]:
    items = parse_json_field(raw, []) or []
    result: list[DialogueLine] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        result.append(
            DialogueLine(
                speaker=str(item.get("speaker") or "Speaker"),
                text=str(item.get("text") or ""),
            )
        )
    return result


def _to_aggregate(row: Scenario) -> ScenarioAggregate:
    words: list[ScenarioWordRef] = []
    for sw in row.words or []:
        lemma = sw.word.lemma if sw.word else ""
        words.append(ScenarioWordRef(word_id=sw.word_id, lemma=lemma))
    return ScenarioAggregate(
        id=row.id,
        title=row.title,
        theme=row.theme,
        level=row.level,
        scenario_type=row.scenario_type,
        content=_content_from_orm(row.content),
        dialogue=_dialogue_from_orm(row.dialogue),
        user_id=row.user_id or 0,
        is_daily=bool(row.is_daily),
        daily_date=row.daily_date,
        daily_kind=row.daily_kind,
        audio_path=row.audio_path,
        created_at=row.created_at,
        words=words,
        exercise_count=len(row.exercises) if row.exercises is not None else 0,
    )


class SqlAlchemyScenarioRepository:
    def __init__(self, session: Session):
        self._session = session

    def get_by_id(self, scenario_id: int, user_id: int | None = None) -> ScenarioAggregate | None:
        query = (
            self._session.query(Scenario)
            .options(joinedload(Scenario.words).joinedload(ScenarioWord.word))
            .options(joinedload(Scenario.exercises))
            .filter(Scenario.id == scenario_id)
        )
        if user_id is not None:
            query = query.filter(Scenario.user_id == user_id)
        row = query.first()
        return _to_aggregate(row) if row else None

    def list_by_user(self, user_id: int, skip: int, limit: int) -> tuple[list[ScenarioAggregate], int]:
        q = self._session.query(Scenario).filter(Scenario.user_id == user_id)
        total = q.count()
        rows = (
            q.options(joinedload(Scenario.words), joinedload(Scenario.exercises))
            .order_by(Scenario.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [_to_aggregate(r) for r in rows], total

    def list_daily(self, user_id: int, daily_date: str) -> list[ScenarioAggregate]:
        rows = (
            self._session.query(Scenario)
            .options(joinedload(Scenario.words).joinedload(ScenarioWord.word))
            .options(joinedload(Scenario.exercises))
            .filter(
                Scenario.user_id == user_id,
                Scenario.is_daily.is_(True),
                Scenario.daily_date == daily_date,
            )
            .order_by(Scenario.id)
            .all()
        )
        return [_to_aggregate(r) for r in rows]

    def get_daily_by_kind(
        self, user_id: int, daily_date: str, daily_kind: str
    ) -> ScenarioAggregate | None:
        row = (
            self._session.query(Scenario)
            .options(joinedload(Scenario.words).joinedload(ScenarioWord.word))
            .options(joinedload(Scenario.exercises))
            .filter(
                Scenario.user_id == user_id,
                Scenario.is_daily.is_(True),
                Scenario.daily_date == daily_date,
                Scenario.daily_kind == daily_kind,
            )
            .first()
        )
        return _to_aggregate(row) if row else None

    def add(self, scenario: ScenarioAggregate) -> ScenarioAggregate:
        content = {
            "passage": scenario.content.passage,
            "summary_zh": scenario.content.summary_zh,
            "fun_fact": scenario.content.fun_fact,
            "word_usage": scenario.content.word_usage,
        }
        if scenario.content.passage_zh:
            content["passage_zh"] = scenario.content.passage_zh
        if scenario.content.dialogue_zh is not None:
            content["dialogue_zh"] = scenario.content.dialogue_zh

        row = Scenario(
            title=scenario.title,
            theme=scenario.theme,
            level=scenario.level,
            scenario_type=scenario.scenario_type,
            content=dump_json_field(content),
            dialogue=dump_json_field(
                [{"speaker": d.speaker, "text": d.text} for d in scenario.dialogue]
            ),
            user_id=scenario.user_id,
            is_daily=scenario.is_daily,
            daily_date=scenario.daily_date,
            daily_kind=scenario.daily_kind,
            audio_path=scenario.audio_path,
        )
        self._session.add(row)
        self._session.flush()
        for ref in scenario.words:
            self._session.add(ScenarioWord(scenario_id=row.id, word_id=ref.word_id))
        self._session.flush()
        scenario.id = row.id
        scenario.created_at = row.created_at
        return scenario

    def save_content(self, scenario: ScenarioAggregate) -> None:
        if scenario.id is None:
            raise ValueError("Cannot save content without scenario id")
        row = self._session.query(Scenario).filter(Scenario.id == scenario.id).first()
        if not row:
            raise ValueError("Scenario not found")
        content = {
            "passage": scenario.content.passage,
            "summary_zh": scenario.content.summary_zh,
            "fun_fact": scenario.content.fun_fact,
            "word_usage": scenario.content.word_usage,
        }
        if scenario.content.passage_zh:
            content["passage_zh"] = scenario.content.passage_zh
        if scenario.content.dialogue_zh is not None:
            content["dialogue_zh"] = scenario.content.dialogue_zh
        row.content = dump_json_field(content)

    def update_audio_path(self, scenario_id: int, user_id: int, audio_path: str) -> bool:
        row = (
            self._session.query(Scenario)
            .filter(Scenario.id == scenario_id, Scenario.user_id == user_id)
            .first()
        )
        if not row:
            return False
        row.audio_path = audio_path
        self._session.flush()
        return True

    def list_enrichment(
        self, user_id: int, scenario_ids: list[int]
    ) -> dict[int, ScenarioListEnrichment]:
        if not scenario_ids:
            return {}
        attempt_rows = (
            self._session.query(
                ScenarioAttempt.scenario_id,
                func.max(
                    ScenarioAttempt.correct_questions
                    * 1.0
                    / func.nullif(ScenarioAttempt.total_questions, 0)
                ).label("best_score"),
                func.count(ScenarioAttempt.id).label("attempt_count"),
            )
            .filter(
                ScenarioAttempt.user_id == user_id,
                ScenarioAttempt.scenario_id.in_(scenario_ids),
            )
            .group_by(ScenarioAttempt.scenario_id)
            .all()
        )
        attempt_map = {row.scenario_id: row for row in attempt_rows}
        conv_counts = (
            self._session.query(ConversationSession.scenario_id, func.count(ConversationSession.id))
            .filter(
                ConversationSession.user_id == user_id,
                ConversationSession.scenario_id.in_(scenario_ids),
            )
            .group_by(ConversationSession.scenario_id)
            .all()
        )
        conv_map = dict(conv_counts)
        result: dict[int, ScenarioListEnrichment] = {}
        for scenario_id in scenario_ids:
            attempt = attempt_map.get(scenario_id)
            best_score = (
                float(attempt.best_score) if attempt and attempt.best_score is not None else None
            )
            attempt_count = int(attempt.attempt_count) if attempt else 0
            result[scenario_id] = ScenarioListEnrichment(
                best_score=best_score,
                attempt_count=attempt_count,
                conversation_count=int(conv_map.get(scenario_id, 0)),
            )
        return result

    def list_theme_slugs(self) -> list[str]:
        return [g.slug for g in self._session.query(WordGroup).all()]
