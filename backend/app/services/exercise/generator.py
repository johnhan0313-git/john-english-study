from __future__ import annotations

import re

from sqlalchemy.orm import Session

from app.models.exercise import Exercise
from app.models.scenario import ScenarioWord
from app.services.vocabulary.srs import record_answer
from app.utils.json_helpers import dump_json_field, parse_json_field


def save_exercises_from_ai(db: Session, scenario_id: int, exercises: list[dict]) -> list[Exercise]:
    saved: list[Exercise] = []
    for idx, ex in enumerate(exercises):
        ex_type = ex.get("type", "single_choice")
        if ex_type == "single_choice":
            payload = {
                "question": ex["question"],
                "options": ex.get("options", []),
                "explanation": ex.get("explanation"),
            }
            answer_key = {"correct_label": ex.get("correct_label", "A")}
        elif ex_type == "fill_blank":
            payload = {
                "question": ex.get("question", "Fill in the blanks:"),
                "passage_with_blanks": ex.get("passage_with_blanks", ""),
                "blanks": ex.get("blanks", []),
                "explanation": ex.get("explanation"),
            }
            answer_key = {"blanks": ex.get("blanks", [])}
        else:
            continue

        exercise = Exercise(
            scenario_id=scenario_id,
            type=ex_type,
            payload=dump_json_field(payload),
            answer_key=dump_json_field(answer_key),
            sort_order=idx,
        )
        db.add(exercise)
        saved.append(exercise)
    return saved


def normalize_answer(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def check_exercise_answer(exercise: Exercise, answer: str | list[str]) -> tuple[bool, str | list[str]]:
    payload = parse_json_field(exercise.payload, {})
    answer_key = parse_json_field(exercise.answer_key, {})

    if exercise.type == "single_choice":
        correct = answer_key.get("correct_label", "A")
        user = str(answer).strip().upper()
        return user == correct.upper(), correct

    if exercise.type == "fill_blank":
        blanks = answer_key.get("blanks", payload.get("blanks", []))
        if isinstance(answer, str):
            user_answers = [answer]
        else:
            user_answers = answer

        if len(blanks) == 1 and len(user_answers) == 1:
            accept = blanks[0].get("accept", [blanks[0].get("answer", "")])
            normalized = normalize_answer(user_answers[0])
            correct = any(normalized == normalize_answer(a) for a in accept)
            return correct, blanks[0].get("answer", "")

        correct_answers = []
        all_correct = True
        for i, blank in enumerate(blanks):
            accept = blank.get("accept", [blank.get("answer", "")])
            user_val = user_answers[i] if i < len(user_answers) else ""
            normalized = normalize_answer(user_val)
            match = any(normalized == normalize_answer(a) for a in accept)
            if not match:
                all_correct = False
            correct_answers.append(blank.get("answer", ""))
        return all_correct, correct_answers

    return False, ""


def submit_exercise(
    db: Session,
    exercise: Exercise,
    answer: str | list[str],
    user_id: int,
) -> dict:
    """Legacy helper — prefer Exercise Application. Does not commit."""
    correct, correct_answer = check_exercise_answer(exercise, answer)
    payload = parse_json_field(exercise.payload, {})

    word_ids = [
        sw.word_id
        for sw in db.query(ScenarioWord).filter(ScenarioWord.scenario_id == exercise.scenario_id).all()
    ]
    familiarity_updates = []
    for word_id in word_ids[:3]:
        progress = record_answer(db, user_id, word_id, correct)
        familiarity_updates.append({"word_id": word_id, "familiarity": progress.familiarity})

    return {
        "correct": correct,
        "correct_answer": correct_answer,
        "explanation": payload.get("explanation"),
        "familiarity_updates": familiarity_updates,
    }
