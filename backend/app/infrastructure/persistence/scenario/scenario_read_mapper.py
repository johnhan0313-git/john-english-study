from __future__ import annotations

"""ORM → brief dict helpers for Activity read composition (legacy service bridge)."""

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.conversation import ConversationSession
from app.models.progress import ScenarioAttempt
from app.models.scenario import Scenario
from app.utils.json_helpers import parse_json_field


def scenario_to_brief(
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


def scenarios_to_briefs(db: Session, user_id: int, scenarios: list[Scenario]) -> list[dict]:
    if not scenarios:
        return []
    scenario_ids = [s.id for s in scenarios]
    attempt_rows = (
        db.query(
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
        db.query(ConversationSession.scenario_id, func.count(ConversationSession.id))
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
            scenario_to_brief(
                scenario,
                user_id=user_id,
                best_score=best_score,
                is_completed=is_completed,
                conversation_count=conv_map.get(scenario.id, 0),
            )
        )
    return briefs
