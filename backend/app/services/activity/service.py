from __future__ import annotations

from datetime import timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.conversation import ConversationSession
from app.models.progress import ScenarioAttempt
from app.models.scenario import Scenario
from app.services.conversation.service import ConversationService
from app.services.scenario.service import ScenarioService
from app.utils.time import local_today


class ActivityService:
    def __init__(self, db: Session, timezone: str = "Asia/Shanghai"):
        self.db = db
        self.timezone = timezone
        self.scenario_service = ScenarioService(db)
        self.conversation_service = ConversationService(db)

    def get_overview(self, user_id: int) -> dict:
        today = local_today(self.timezone)
        week_start = today - timedelta(days=today.weekday())

        scenario_total = self.db.query(func.count(Scenario.id)).filter(Scenario.user_id == user_id).scalar() or 0
        scenario_this_week = (
            self.db.query(func.count(Scenario.id))
            .filter(Scenario.user_id == user_id, func.date(Scenario.created_at) >= week_start.isoformat())
            .scalar()
            or 0
        )

        conversation_total = (
            self.db.query(func.count(ConversationSession.id)).filter(ConversationSession.user_id == user_id).scalar()
            or 0
        )
        conversation_active = (
            self.db.query(func.count(ConversationSession.id))
            .filter(ConversationSession.user_id == user_id, ConversationSession.status == "active")
            .scalar()
            or 0
        )

        theme_rows = (
            self.db.query(Scenario.theme, func.count(Scenario.id))
            .filter(Scenario.user_id == user_id)
            .group_by(Scenario.theme)
            .all()
        )
        theme_counts = {theme: count for theme, count in theme_rows}

        active_sessions = (
            self.db.query(ConversationSession)
            .options(joinedload(ConversationSession.messages))
            .filter(ConversationSession.user_id == user_id, ConversationSession.status == "active")
            .order_by(ConversationSession.created_at.desc())
            .limit(3)
            .all()
        )

        recent_scenarios = (
            self.db.query(Scenario)
            .options(joinedload(Scenario.words), joinedload(Scenario.exercises))
            .filter(Scenario.user_id == user_id)
            .order_by(Scenario.created_at.desc())
            .limit(20)
            .all()
        )
        recent_briefs = self.scenario_service.scenarios_to_briefs(user_id, recent_scenarios)
        incomplete = [b for b in recent_briefs if not b["is_completed"]][:3]

        return {
            "scenario_total": scenario_total,
            "scenario_this_week": scenario_this_week,
            "conversation_total": conversation_total,
            "conversation_active": conversation_active,
            "theme_counts": theme_counts,
            "heatmap": self._build_heatmap(user_id, weeks=12),
            "continue": {
                "active_conversations": [
                    self.conversation_service.session_to_brief(s) for s in active_sessions
                ],
                "incomplete_scenarios": incomplete,
            },
        }

    def _build_heatmap(self, user_id: int, weeks: int = 12) -> list[dict]:
        today = local_today(self.timezone)
        start = today - timedelta(days=weeks * 7 - 1)
        start_iso = start.isoformat()
        counts: dict[str, int] = {}

        def bump(day) -> None:
            key = day.isoformat() if hasattr(day, "isoformat") else str(day)
            counts[key] = counts.get(key, 0) + 1

        scenario_dates = (
            self.db.query(func.date(Scenario.created_at))
            .filter(Scenario.user_id == user_id, func.date(Scenario.created_at) >= start_iso)
            .all()
        )
        for (d,) in scenario_dates:
            bump(d)

        conv_dates = (
            self.db.query(func.date(ConversationSession.created_at))
            .filter(ConversationSession.user_id == user_id, func.date(ConversationSession.created_at) >= start_iso)
            .all()
        )
        for (d,) in conv_dates:
            bump(d)

        attempt_dates = (
            self.db.query(func.date(ScenarioAttempt.completed_at))
            .filter(ScenarioAttempt.user_id == user_id, func.date(ScenarioAttempt.completed_at) >= start_iso)
            .all()
        )
        for (d,) in attempt_dates:
            bump(d)

        return [{"date": k, "count": v} for k, v in sorted(counts.items())]

    def get_timeline(self, user_id: int, skip: int = 0, limit: int = 30) -> tuple[list[dict], int]:
        events: list[dict] = []

        scenarios = (
            self.db.query(Scenario)
            .options(joinedload(Scenario.words), joinedload(Scenario.exercises))
            .filter(Scenario.user_id == user_id)
            .all()
        )
        briefs = self.scenario_service.scenarios_to_briefs(user_id, scenarios)
        scenario_brief_map = {b["id"]: b for b in briefs}

        for scenario in scenarios:
            events.append(
                {
                    "type": "scenario_created",
                    "at": scenario.created_at,
                    "scenario": scenario_brief_map[scenario.id],
                }
            )

        attempts = (
            self.db.query(ScenarioAttempt)
            .options(joinedload(ScenarioAttempt.scenario).joinedload(Scenario.words))
            .options(joinedload(ScenarioAttempt.scenario).joinedload(Scenario.exercises))
            .filter(ScenarioAttempt.user_id == user_id)
            .all()
        )
        for attempt in attempts:
            if not attempt.scenario:
                continue
            score = attempt.correct_questions / attempt.total_questions if attempt.total_questions else 0.0
            brief = self.scenario_service.scenario_to_brief(
                attempt.scenario,
                user_id=user_id,
                best_score=score,
                is_completed=True,
                conversation_count=0,
            )
            events.append(
                {
                    "type": "scenario_completed",
                    "at": attempt.completed_at,
                    "scenario": brief,
                    "score": score,
                }
            )

        sessions = (
            self.db.query(ConversationSession)
            .options(joinedload(ConversationSession.messages))
            .filter(ConversationSession.user_id == user_id)
            .all()
        )
        for session in sessions:
            brief = self.conversation_service.session_to_brief(session)
            events.append(
                {
                    "type": "conversation_started",
                    "at": session.created_at,
                    "conversation": brief,
                }
            )
            if session.status != "active" and session.ended_at:
                events.append(
                    {
                        "type": "conversation_ended",
                        "at": session.ended_at,
                        "conversation": brief,
                    }
                )

        events.sort(key=lambda e: e["at"], reverse=True)
        total = len(events)
        page = events[skip : skip + limit]
        return page, total
