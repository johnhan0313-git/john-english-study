from __future__ import annotations

from dataclasses import dataclass

from app.application.activity.activity_query import ActivityApplication, build_activity_application
from app.application.identity.identity_command import (
    LoginOrRegisterByEmailCommand,
    LoginOrRegisterByWechatCommand,
    MergeDeviceCommand,
)
from app.composition.conversation_composition import (
    ConversationApplication,
    build_conversation_application,
)
from app.composition.profile_composition import ProfileApplication, build_profile_application
from app.composition.progress_composition import (
    ExerciseApplication,
    ProgressApplication,
    build_exercise_application,
    build_progress_application,
)
from app.composition.reference_composition import ReferenceApplication, build_reference_application
from app.composition.scenario_composition import ScenarioApplication, build_scenario_application
from app.composition.vocabulary_composition import (
    VocabularyApplication,
    build_vocabulary_application,
)
from app.config import Settings, get_settings
from app.database import SessionLocal
from app.infrastructure.unit_of_work import SqlAlchemyUnitOfWork


@dataclass
class IdentityApplication:
    login_or_register_email: LoginOrRegisterByEmailCommand
    login_or_register_wechat: LoginOrRegisterByWechatCommand
    merge_device: MergeDeviceCommand


@dataclass
class AppContainer:
    settings: Settings
    scenario: ScenarioApplication
    progress: ProgressApplication
    exercise: ExerciseApplication
    conversation: ConversationApplication
    activity: ActivityApplication
    identity: IdentityApplication
    vocabulary: VocabularyApplication
    reference: ReferenceApplication
    profile: ProfileApplication


_container: AppContainer | None = None


def _uow_factory() -> SqlAlchemyUnitOfWork:
    return SqlAlchemyUnitOfWork(_session=SessionLocal())


def build_identity_application() -> IdentityApplication:
    return IdentityApplication(
        login_or_register_email=LoginOrRegisterByEmailCommand(_uow_factory),
        login_or_register_wechat=LoginOrRegisterByWechatCommand(_uow_factory),
        merge_device=MergeDeviceCommand(_uow_factory),
    )


def build_container(settings: Settings | None = None) -> AppContainer:
    cfg = settings or get_settings()
    progress = build_progress_application(cfg)
    return AppContainer(
        settings=cfg,
        scenario=build_scenario_application(cfg),
        progress=progress,
        exercise=build_exercise_application(progress),
        conversation=build_conversation_application(cfg, record_answer=progress.record_answer),
        activity=build_activity_application(),
        identity=build_identity_application(),
        vocabulary=build_vocabulary_application(),
        reference=build_reference_application(cfg),
        profile=build_profile_application(cfg),
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
