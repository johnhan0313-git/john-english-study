from __future__ import annotations

from fastapi.testclient import TestClient

from app.services.exercise.generator import check_exercise_answer, normalize_answer
from app.models.exercise import Exercise
from app.utils.json_helpers import dump_json_field


def test_health(client: TestClient):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_words_list(client):
    resp = client.get("/api/words?page=1&page_size=10")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] > 0
    assert len(data["items"]) <= 10


def test_word_stats(client):
    resp = client.get("/api/words/stats")
    assert resp.status_code == 200
    assert resp.json()["total"] > 0


def test_normalize_answer():
    assert normalize_answer("  Plan  ") == "plan"


def test_check_fill_blank():
    exercise = Exercise(
        scenario_id=1,
        type="fill_blank",
        payload=dump_json_field({
            "passage_with_blanks": "They ___ carefully.",
            "blanks": [{"index": 0, "answer": "plan", "accept": ["plan", "planned"]}],
        }),
        answer_key=dump_json_field({"blanks": [{"answer": "plan", "accept": ["plan", "planned"]}]}),
        sort_order=0,
    )
    correct, _ = check_exercise_answer(exercise, "plan")
    assert correct is True
    correct2, _ = check_exercise_answer(exercise, "planned")
    assert correct2 is True
