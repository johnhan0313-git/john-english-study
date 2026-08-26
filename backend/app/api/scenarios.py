from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException, Query

from app.application.scenario.scenario_input import (
    CreateMissingDailySlotsInput,
    GenerateScenarioInput,
    GetScenarioInput,
    ListScenariosInput,
)
from app.auth.dependencies import get_current_user
from app.composition.shared_composition import AppContainer, get_container
from app.models.user import User
from app.schemas.scenario import (
    DailyScenariosResponse,
    ScenarioBrief,
    ScenarioDetail,
    ScenarioGenerateRequest,
    ScenarioListResponse,
    ScenarioTranslationResponse,
)
from app.services.storage.responses import storage_stream_response
from app.utils.time import local_today

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


def _scenario_app(container: AppContainer = Depends(get_container)):
    return container.scenario


@router.post("/generate", response_model=ScenarioDetail)
async def generate_scenario(
    body: ScenarioGenerateRequest,
    user: User = Depends(get_current_user),
    app=Depends(_scenario_app),
):
    try:
        detail = await app.generate.execute(
            GenerateScenarioInput(
                user_id=user.id,
                level=body.level,
                theme=body.theme,
                word_ids=tuple(body.word_ids),
                scenario_type=body.scenario_type,
                word_count=body.word_count,
                word_strategy=body.word_strategy,
                exclude_recent=body.exclude_recent,
            )
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Scenario generation failed: {e}") from e
    return ScenarioDetail(**asdict(detail))


@router.get("/daily", response_model=DailyScenariosResponse)
async def daily_scenarios(
    user: User = Depends(get_current_user),
    app=Depends(_scenario_app),
    container: AppContainer = Depends(get_container),
):
    today = local_today(container.settings.app_timezone).isoformat()
    try:
        result = await app.create_missing_daily_slots.execute(
            CreateMissingDailySlotsInput(
                user_id=user.id,
                daily_date=today,
                target_count=container.settings.daily_scenario_count,
            )
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Daily scenario generation failed: {e}") from e
    return DailyScenariosResponse(
        date=result.date,
        items=[ScenarioBrief(**asdict(item)) for item in result.items],
        generated=result.generated,
    )


@router.get("", response_model=ScenarioListResponse)
def list_scenarios(
    user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    app=Depends(_scenario_app),
):
    result = app.list_scenarios.execute(
        ListScenariosInput(user_id=user.id, skip=skip, limit=limit)
    )
    return ScenarioListResponse(
        items=[ScenarioBrief(**asdict(item)) for item in result.items],
        total=result.total,
    )


@router.get("/{scenario_id}", response_model=ScenarioDetail)
def get_scenario(
    scenario_id: int,
    user: User = Depends(get_current_user),
    app=Depends(_scenario_app),
):
    detail = app.get_scenario.execute(GetScenarioInput(scenario_id=scenario_id, user_id=user.id))
    if not detail:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return ScenarioDetail(**asdict(detail))


@router.get("/{scenario_id}/translation", response_model=ScenarioTranslationResponse)
async def get_scenario_translation(
    scenario_id: int,
    user: User = Depends(get_current_user),
    app=Depends(_scenario_app),
):
    try:
        result = await app.translate.execute(scenario_id, user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Translation failed: {e}") from e
    return ScenarioTranslationResponse(
        passage_zh=result.passage_zh,
        dialogue_zh=result.dialogue_zh,
    )


@router.get("/{scenario_id}/audio")
async def get_scenario_audio(
    scenario_id: int,
    user: User = Depends(get_current_user),
    app=Depends(_scenario_app),
):
    detail = app.get_scenario.execute(GetScenarioInput(scenario_id=scenario_id, user_id=user.id))
    if not detail:
        raise HTTPException(status_code=404, detail="Scenario not found")

    passage = (detail.content or {}).get("passage", "")
    dialogue_lines = detail.dialogue or []
    text = passage
    if dialogue_lines:
        text += " " + " ".join(f"{d['speaker']}: {d['text']}" for d in dialogue_lines)

    try:
        audio_key = await app.materialize_audio.execute(
            scenario_id=scenario_id,
            user_id=user.id,
            text=text,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    return storage_stream_response(
        audio_key,
        media_type="audio/mpeg",
        filename=f"scenario_{scenario_id}.mp3",
    )
