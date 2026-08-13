from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
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
from app.services.exercise.generator import submit_exercise
from app.services.vocabulary.progress_service import record_scenario_attempt
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
    db: Session = Depends(get_db),
):
    exercise = (
        db.query(Exercise)
        .join(Scenario, Scenario.id == Exercise.scenario_id)
        .filter(Exercise.id == exercise_id, Scenario.user_id == user.id)
        .first()
    )
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    result = submit_exercise(db, exercise, body.answer, user.id)
    return ExerciseSubmitResponse(**result)


@router.post("/scenario/{scenario_id}/submit", response_model=BatchSubmitResponse)
def submit_batch(
    scenario_id: int,
    body: BatchSubmitRequest,
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
    results = []
    correct = 0
    for ex in exercises:
        answer = body.answers.get(ex.id, "")
        result = submit_exercise(db, ex, answer, user.id)
        if result["correct"]:
            correct += 1
        results.append(ExerciseSubmitResponse(**result))

    total = len(exercises)
    record_scenario_attempt(db, scenario_id, user.id, total, correct)
    return BatchSubmitResponse(
        score=round(correct / total * 100, 1) if total else 0,
        total=total,
        correct=correct,
        results=results,
    )
