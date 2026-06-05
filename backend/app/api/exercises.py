from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.exercise import Exercise
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
def list_exercises(scenario_id: int, db: Session = Depends(get_db)):
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
def submit_single(exercise_id: int, body: ExerciseSubmitRequest, db: Session = Depends(get_db)):
    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    result = submit_exercise(db, exercise, body.answer, body.device_id)
    return ExerciseSubmitResponse(**result)


@router.post("/scenario/{scenario_id}/submit", response_model=BatchSubmitResponse)
def submit_batch(scenario_id: int, body: BatchSubmitRequest, db: Session = Depends(get_db)):
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
        result = submit_exercise(db, ex, answer, body.device_id)
        if result["correct"]:
            correct += 1
        results.append(ExerciseSubmitResponse(**result))

    total = len(exercises)
    record_scenario_attempt(db, scenario_id, body.device_id, total, correct)
    return BatchSubmitResponse(
        score=round(correct / total * 100, 1) if total else 0,
        total=total,
        correct=correct,
        results=results,
    )
