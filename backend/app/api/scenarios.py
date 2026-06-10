from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.schemas.scenario import (
    DailyScenariosResponse,
    ScenarioBrief,
    ScenarioDetail,
    ScenarioGenerateRequest,
    ScenarioListResponse,
)
from app.services.media.tts_facade import ensure_scenario_audio
from app.services.scenario.service import ScenarioService
from app.utils.time import local_today

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@router.post("/generate", response_model=ScenarioDetail)
async def generate_scenario(
    body: ScenarioGenerateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = ScenarioService(db)
    try:
        scenario = await service.generate_scenario(
            user_id=user.id,
            level=body.level,
            theme=body.theme,
            word_ids=body.word_ids,
            scenario_type=body.scenario_type,
            word_count=body.word_count,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Scenario generation failed: {e}") from e

    full = service.get_scenario(scenario.id)
    return ScenarioDetail(**service.scenario_to_detail(full))


@router.get("/daily", response_model=DailyScenariosResponse)
async def daily_scenarios(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    settings = get_settings()
    service = ScenarioService(db)
    today = local_today(settings.app_timezone).isoformat()
    try:
        scenarios = await service.ensure_daily_scenarios(user.id)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Daily scenario generation failed: {e}") from e
    return DailyScenariosResponse(
        date=today,
        items=[ScenarioBrief(**service.scenario_to_brief(s)) for s in scenarios],
        generated=True,
    )


@router.get("", response_model=ScenarioListResponse)
def list_scenarios(
    user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    service = ScenarioService(db)
    items, total = service.list_scenarios(user.id, skip, limit)
    return ScenarioListResponse(
        items=[ScenarioBrief(**b) for b in service.scenarios_to_briefs(user.id, items)],
        total=total,
    )


@router.get("/{scenario_id}", response_model=ScenarioDetail)
def get_scenario(scenario_id: int, db: Session = Depends(get_db)):
    service = ScenarioService(db)
    scenario = service.get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return ScenarioDetail(**service.scenario_to_detail(scenario))


@router.get("/{scenario_id}/audio")
async def get_scenario_audio(scenario_id: int, db: Session = Depends(get_db)):
    settings = get_settings()
    service = ScenarioService(db)
    scenario = service.get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    content = service.scenario_to_detail(scenario)
    passage = content["content"].get("passage", "")
    dialogue_lines = content.get("dialogue", [])
    text = passage
    if dialogue_lines:
        text += " " + " ".join(f"{d['speaker']}: {d['text']}" for d in dialogue_lines)

    audio_path = await ensure_scenario_audio(
        scenario_id,
        text,
        settings,
        stored_path=scenario.audio_path,
    )
    if scenario.audio_path != str(audio_path):
        scenario.audio_path = str(audio_path)
        db.commit()

    return FileResponse(audio_path, media_type="audio/mpeg", filename=f"scenario_{scenario_id}.mp3")
