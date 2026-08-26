from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.application.progress.progress_command import RecordScenarioAttemptInput
from app.application.scenario.scenario_input import GetScenarioInput
from app.auth.dependencies import get_current_user
from app.composition.shared_composition import AppContainer, get_container
from app.models.user import User

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


class CompleteScenarioRequest(BaseModel):
    total: int = 0
    correct: int = 0


@router.post("/{scenario_id}/complete")
def complete_scenario(
    scenario_id: int,
    body: CompleteScenarioRequest,
    user: User = Depends(get_current_user),
    container: AppContainer = Depends(get_container),
):
    detail = container.scenario.get_scenario.execute(
        GetScenarioInput(scenario_id=scenario_id, user_id=user.id)
    )
    if not detail:
        raise HTTPException(status_code=404, detail="Scenario not found")
    container.progress.record_scenario_attempt.execute(
        RecordScenarioAttemptInput(
            user_id=user.id,
            scenario_id=scenario_id,
            total=body.total,
            correct=body.correct,
            timezone=container.settings.app_timezone,
        )
    )
    return {"ok": True}
