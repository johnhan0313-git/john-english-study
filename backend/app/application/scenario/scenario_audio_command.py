from __future__ import annotations

from app.application.media.media_command import materialize_scenario_audio
from app.config import Settings
from app.database import SessionLocal
from app.infrastructure.persistence.scenario.scenario_repository_impl import SqlAlchemyScenarioRepository
from app.infrastructure.unit_of_work import SqlAlchemyUnitOfWork
from app.models.scenario import Scenario


class MaterializeAndStoreScenarioAudioCommand:
    """Materialize TTS audio and persist audio_path when changed. Application owns commit."""

    def __init__(self, settings: Settings):
        self._settings = settings

    async def execute(self, *, scenario_id: int, user_id: int, text: str) -> str:
        with SqlAlchemyUnitOfWork(_session=SessionLocal()) as uow:
            repo = SqlAlchemyScenarioRepository(uow.session)
            scenario = repo.get_by_id(scenario_id, user_id)
            if not scenario:
                raise ValueError("Scenario not found")
            stored_path = scenario.audio_path

        audio_key = await materialize_scenario_audio(
            scenario_id,
            text,
            self._settings,
            stored_path=stored_path,
        )

        if stored_path != audio_key:
            with SqlAlchemyUnitOfWork(_session=SessionLocal()) as uow:
                row = uow.session.query(Scenario).filter(
                    Scenario.id == scenario_id, Scenario.user_id == user_id
                ).first()
                if row:
                    row.audio_path = audio_key
                    uow.commit()
        return audio_key
