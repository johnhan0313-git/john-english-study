from __future__ import annotations

from fastapi.testclient import TestClient

from tests.auth_helpers import auth_headers, register_user
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


def test_words_letters(client):
    resp = client.get("/api/words/letters")
    assert resp.status_code == 200
    letters = resp.json()["letters"]
    assert letters
    assert letters == sorted(letters, key=lambda value: (value == "#", value))

    filtered = client.get("/api/words?letter=A&page_size=5")
    assert filtered.status_code == 200
    data = filtered.json()
    assert data["total"] > 0
    assert all(item["lemma"][0].upper() == "A" for item in data["items"])

    page1 = client.get("/api/words?page=1&page_size=30")
    assert page1.status_code == 200
    page1_letters = {item["lemma"][0].upper() for item in page1.json()["items"] if item["lemma"]}
    assert page1_letters == {"A"}, page1_letters


def test_words_filters_stack(client):
    letters = client.get("/api/words/letters?level=cet4").json()["letters"]
    assert letters

    letter = letters[0]
    stacked = client.get(f"/api/words?level=cet4&letter={letter}&search={letter.lower()}&page=1&page_size=10")
    assert stacked.status_code == 200
    data = stacked.json()
    for item in data["items"]:
        lemma = item["lemma"]
        assert lemma.upper().startswith(letter)
        assert letter.lower() in lemma.lower()

    page2 = client.get(f"/api/words?level=cet4&letter={letter}&page=2&page_size=1")
    assert page2.status_code == 200
    if page2.json()["total"] > 1:
        assert page2.json()["page"] == 2


def test_word_stats(client):
    data = register_user(client, email="stats@example.com")
    resp = client.get("/api/words/stats", headers=auth_headers(data["access_token"]))
    assert resp.status_code == 200
    assert resp.json()["total"] > 0


def test_word_groups(client):
    resp = client.get("/api/words/groups")
    assert resp.status_code == 200
    groups = resp.json()
    assert len(groups) >= 8
    slugs = {group["slug"] for group in groups}
    assert {"travel", "campus", "business", "daily"}.issubset(slugs)
    assert all(group["word_count"] > 0 for group in groups)


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
