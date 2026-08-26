from __future__ import annotations

from typing import Any

from app.application.media.media_command import materialize_scenario_audio
from app.config import Settings
from app.domains.scenario.scenario_repository import ScenarioRepository
from app.infrastructure.unit_of_work import UnitOfWorkFactory


class MaterializeAndStoreScenarioAudioCommand:
    """Materialize TTS audio and persist audio_path when changed. Application owns commit."""

    def __init__(
        self,
        uow_factory: UnitOfWorkFactory,
        repository_factory: Any,
        settings: Settings,
    ):
        self._uow_factory = uow_factory
        self._repository_factory = repository_factory
        self._settings = settings

    async def execute(self, *, scenario_id: int, user_id: int, text: str) -> str:
        with self._uow_factory() as uow:
            repo: ScenarioRepository = self._repository_factory(uow.session)
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
            with self._uow_factory() as uow:
                repo = self._repository_factory(uow.session)
                if repo.update_audio_path(scenario_id, user_id, audio_key):
                    uow.commit()
        return audio_key
