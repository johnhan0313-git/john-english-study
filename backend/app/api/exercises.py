from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.application.exercise.exercise_command import SubmitBatchInput, SubmitExerciseInput
from app.application.progress.progress_query import ListExercisesInput
from app.auth.dependencies import get_current_user
from app.composition.shared_composition import AppContainer, get_container
from app.models.user import User
from app.schemas.exercise import (
    BatchSubmitRequest,
    BatchSubmitResponse,
    ExercisePayload,
    ExerciseResponse,
    ExerciseSubmitRequest,
    ExerciseSubmitResponse,
)

router = APIRouter(prefix="/exercises", tags=["exercises"])


@router.get("/scenario/{scenario_id}", response_model=list[ExerciseResponse])
def list_exercises(
    scenario_id: int,
    user: User = Depends(get_current_user),
    container: AppContainer = Depends(get_container),
):
    try:
        items = container.exercise.list_for_scenario.execute(
            ListExercisesInput(user_id=user.id, scenario_id=scenario_id)
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return [
        ExerciseResponse(
            id=item["id"],
            scenario_id=item["scenario_id"],
            type=item["type"],
            payload=ExercisePayload(**item["payload"]),
            sort_order=item["sort_order"],
        )
        for item in items
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
