from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.schemas.scenario import (
    DailyScenariosResponse,
    ScenarioBrief,
    ScenarioDetail,
    ScenarioGenerateRequest,
    ScenarioListResponse,
)
from app.services.ai.tts_service import generate_speech
from app.services.scenario.service import ScenarioService

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@router.post("/generate", response_model=ScenarioDetail)
async def generate_scenario(body: ScenarioGenerateRequest, db: Session = Depends(get_db)):
    service = ScenarioService(db)
    try:
        scenario = await service.generate_scenario(
            level=body.level,
            theme=body.theme,
            word_ids=body.word_ids,
            scenario_type=body.scenario_type,
            device_id=body.device_id,
            word_count=body.word_count,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Scenario generation failed: {e}") from e

    full = service.get_scenario(scenario.id)
    return ScenarioDetail(**service.scenario_to_detail(full))


@router.get("/daily", response_model=DailyScenariosResponse)
async def daily_scenarios(device_id: str = "default", db: Session = Depends(get_db)):
    service = ScenarioService(db)
    today = date.today().isoformat()
    try:
        scenarios = await service.ensure_daily_scenarios(device_id)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Daily scenario generation failed: {e}") from e
    return DailyScenariosResponse(
        date=today,
        items=[ScenarioBrief(**service.scenario_to_brief(s)) for s in scenarios],
        generated=True,
    )


@router.get("", response_model=ScenarioListResponse)
def list_scenarios(
    device_id: str = "default",
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    service = ScenarioService(db)
    items, total = service.list_scenarios(device_id, skip, limit)
    return ScenarioListResponse(
        items=[ScenarioBrief(**service.scenario_to_brief(s)) for s in items],
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

    from pathlib import Path

    audio_path = Path(scenario.audio_path) if scenario.audio_path else settings.media_dir / f"scenario_{scenario_id}.mp3"

    if not audio_path.exists():
        content = service.scenario_to_detail(scenario)
        passage = content["content"].get("passage", "")
        dialogue_lines = content.get("dialogue", [])
        text = passage
        if dialogue_lines:
            text += " " + " ".join(f"{d['speaker']}: {d['text']}" for d in dialogue_lines)
        await generate_speech(text, audio_path, settings)
        scenario.audio_path = str(audio_path)
        db.commit()

    return FileResponse(audio_path, media_type="audio/mpeg", filename=f"scenario_{scenario_id}.mp3")
