from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.composition.shared_composition import AppContainer, get_container
from app.database import get_db
from app.models.exercise import Exercise
from app.models.scenario import Scenario
from app.models.user import User
from app.schemas.exercise import (
    BatchSubmitRequest,
    BatchSubmitResponse,
    ExercisePayload,
    ExerciseResponse,
    ExerciseSubmitRequest,
    ExerciseSubmitResponse,
)
from app.application.exercise.exercise_command import SubmitBatchInput, SubmitExerciseInput
from app.utils.json_helpers import parse_json_field

router = APIRouter(prefix="/exercises", tags=["exercises"])


@router.get("/scenario/{scenario_id}", response_model=list[ExerciseResponse])
def list_exercises(
    scenario_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    owned = db.query(Scenario.id).filter(Scenario.id == scenario_id, Scenario.user_id == user.id).first()
    if not owned:
        raise HTTPException(status_code=404, detail="Scenario not found")
    exercises = (
        db.query(Exercise)
        .filter(Exercise.scenario_id == scenario_id)
        .order_by(Exercise.sort_order)
        .all()
    )
    return [
        ExerciseResponse(
            id=ex.id,
            scenario_id=ex.scenario_id,
            type=ex.type,
            payload=ExercisePayload(**parse_json_field(ex.payload, {})),
            sort_order=ex.sort_order,
        )
        for ex in exercises
    ]


@router.post("/{exercise_id}/submit", response_model=ExerciseSubmitResponse)
def submit_single(
    exercise_id: int,
    body: ExerciseSubmitRequest,
    user: User = Depends(get_current_user),
    container: AppContainer = Depends(get_container),
):
    try:
        result = container.exercise.submit.execute(
            SubmitExerciseInput(user_id=user.id, exercise_id=exercise_id, answer=body.answer)
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return ExerciseSubmitResponse(**result)


@router.post("/scenario/{scenario_id}/submit", response_model=BatchSubmitResponse)
def submit_batch(
    scenario_id: int,
    body: BatchSubmitRequest,
    user: User = Depends(get_current_user),
    container: AppContainer = Depends(get_container),
):
    try:
        result = container.exercise.submit_batch.execute(
            SubmitBatchInput(
                user_id=user.id,
                scenario_id=scenario_id,
                answers=body.answers,
                timezone=container.settings.app_timezone,
            )
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return BatchSubmitResponse(
        score=result["score"],
        total=result["total"],
        correct=result["correct"],
        results=[ExerciseSubmitResponse(**r) for r in result["results"]],
    )
