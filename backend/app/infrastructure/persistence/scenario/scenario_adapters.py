from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.services.exercise.generator import save_exercises_from_ai
from app.services.scenario.word_picker import WordStrategy, pick_words
from app.services.vocabulary.import_words import word_to_dict


class SqlAlchemyWordSelectionAdapter:
    def __init__(self, session: Session):
        self._session = session

    def pick_words(
        self,
        *,
        user_id: int,
        level: str,
        theme: str | None,
        word_ids: list[int],
        word_count: int,
        word_strategy: str,
        exclude_recent: bool,
    ) -> list[dict[str, Any]]:
        words = pick_words(
            self._session,
            level=level,
            theme=theme,
            word_ids=word_ids,
            word_count=word_count,
            user_id=user_id,
            word_strategy=word_strategy,  # type: ignore[arg-type]
            exclude_recent=exclude_recent,
        )
        return [word_to_dict(w) for w in words]


class SqlAlchemyExerciseDraftAdapter:
    def __init__(self, session: Session):
        self._session = session

    def save_from_ai(self, scenario_id: int, exercises: list[dict]) -> int:
        saved = save_exercises_from_ai(self._session, scenario_id, exercises)
        return len(saved)
