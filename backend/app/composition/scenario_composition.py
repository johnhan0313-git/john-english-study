from __future__ import annotations

from dataclasses import dataclass

from app.application.scenario.scenario_audio_command import MaterializeAndStoreScenarioAudioCommand
from app.application.scenario.scenario_command import (
    CreateMissingDailySlotsCommand,
    GenerateScenarioCommand,
    TranslateScenarioCommand,
)
from app.application.scenario.scenario_query import (
    GetDailyScenariosQuery,
    GetScenarioQuery,
    ListScenariosQuery,
)
from app.config import Settings, get_settings
from app.database import SessionLocal
from app.infrastructure.persistence.scenario.scenario_adapters import (
    SqlAlchemyExerciseDraftAdapter,
    SqlAlchemyWordSelectionAdapter,
)
from app.infrastructure.persistence.scenario.scenario_repository_impl import SqlAlchemyScenarioRepository
from app.infrastructure.unit_of_work import SqlAlchemyUnitOfWork
from app.services.ai.factory import build_providers


@dataclass
class ScenarioApplication:
    generate: GenerateScenarioCommand
    create_missing_daily_slots: CreateMissingDailySlotsCommand
    translate: TranslateScenarioCommand
    get_daily: GetDailyScenariosQuery
    get_scenario: GetScenarioQuery
    list_scenarios: ListScenariosQuery
    materialize_audio: MaterializeAndStoreScenarioAudioCommand


def _uow_factory() -> SqlAlchemyUnitOfWork:
    return SqlAlchemyUnitOfWork(_session=SessionLocal())


def build_scenario_application(settings: Settings | None = None) -> ScenarioApplication:
    cfg = settings or get_settings()
    providers = build_providers(cfg)
    llm = providers.llm

    generate = GenerateScenarioCommand(
        uow_factory=_uow_factory,
        repository_factory=SqlAlchemyScenarioRepository,
        word_selection_factory=SqlAlchemyWordSelectionAdapter,
        exercise_draft_factory=SqlAlchemyExerciseDraftAdapter,
        llm=llm,
        timezone=cfg.app_timezone,
    )
    create_daily = CreateMissingDailySlotsCommand(
        generate=generate,
        uow_factory=_uow_factory,
        repository_factory=SqlAlchemyScenarioRepository,
    )
    translate = TranslateScenarioCommand(
        uow_factory=_uow_factory,
        repository_factory=SqlAlchemyScenarioRepository,
        llm=llm,
    )
    return ScenarioApplication(
        generate=generate,
        create_missing_daily_slots=create_daily,
        translate=translate,
        get_daily=GetDailyScenariosQuery(_uow_factory, SqlAlchemyScenarioRepository),
        get_scenario=GetScenarioQuery(_uow_factory, SqlAlchemyScenarioRepository),
        list_scenarios=ListScenariosQuery(_uow_factory, SqlAlchemyScenarioRepository),
        materialize_audio=MaterializeAndStoreScenarioAudioCommand(cfg),
    )
