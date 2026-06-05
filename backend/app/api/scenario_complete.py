from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.scenario.service import ScenarioService
from app.services.vocabulary.progress_service import record_scenario_attempt

router = APIRouter(prefix="/scenarios", tags=["scenarios-complete"])


class CompleteScenarioRequest(BaseModel):
    device_id: str = "default"
    total: int
    correct: int


@router.post("/{scenario_id}/complete")
def complete_scenario(scenario_id: int, body: CompleteScenarioRequest, db: Session = Depends(get_db)):
    service = ScenarioService(db)
    scenario = service.get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    record_scenario_attempt(db, scenario_id, body.device_id, body.total, body.correct)
    return {"ok": True, "score": round(body.correct / body.total * 100, 1) if body.total else 0}
