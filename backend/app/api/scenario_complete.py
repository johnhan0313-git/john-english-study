from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.scenario import Scenario
from app.services.vocabulary.progress_service import record_scenario_attempt

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


class CompleteScenarioRequest(BaseModel):
    total: int = 0
    correct: int = 0


@router.post("/{scenario_id}/complete")
def complete_scenario(
    scenario_id: int,
    body: CompleteScenarioRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    scenario = db.query(Scenario.id).filter(Scenario.id == scenario_id, Scenario.user_id == user.id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    record_scenario_attempt(db, scenario_id, user.id, body.total, body.correct)
    return {"ok": True}
