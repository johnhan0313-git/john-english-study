from __future__ import annotations

from dataclasses import dataclass

from app.application.activity.activity_query import ActivityApplication, build_activity_application
from app.application.identity.identity_command import (
    LoginOrRegisterByEmailCommand,
    LoginOrRegisterByWechatCommand,
)
from app.composition.progress_composition import (
    ExerciseApplication,
    ProgressApplication,
    build_exercise_application,
    build_progress_application,
)
from app.composition.scenario_composition import ScenarioApplication, build_scenario_application
from app.config import Settings, get_settings
from app.database import SessionLocal
from app.infrastructure.unit_of_work import SqlAlchemyUnitOfWork


@dataclass
class IdentityApplication:
    login_or_register_email: LoginOrRegisterByEmailCommand
    login_or_register_wechat: LoginOrRegisterByWechatCommand


@dataclass
class AppContainer:
    settings: Settings
    scenario: ScenarioApplication
    progress: ProgressApplication
    exercise: ExerciseApplication
    activity: ActivityApplication
    identity: IdentityApplication


_container: AppContainer | None = None


def _uow_factory() -> SqlAlchemyUnitOfWork:
    return SqlAlchemyUnitOfWork(_session=SessionLocal())


def build_identity_application() -> IdentityApplication:
    return IdentityApplication(
        login_or_register_email=LoginOrRegisterByEmailCommand(_uow_factory),
        login_or_register_wechat=LoginOrRegisterByWechatCommand(_uow_factory),
    )


def build_container(settings: Settings | None = None) -> AppContainer:
    cfg = settings or get_settings()
    progress = build_progress_application()
    return AppContainer(
        settings=cfg,
        scenario=build_scenario_application(cfg),
        progress=progress,
        exercise=build_exercise_application(progress),
        activity=build_activity_application(),
        identity=build_identity_application(),
    )


def init_container(settings: Settings | None = None) -> AppContainer:
    global _container
    _container = build_container(settings)
    return _container


def get_container() -> AppContainer:
    global _container
    if _container is None:
        _container = build_container()
    return _container


def reset_container() -> None:
    global _container
    _container = None
