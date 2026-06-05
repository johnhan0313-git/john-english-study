from __future__ import annotations

import pytest

from app.services.ai.openai_provider import AIProviderError
from app.services.ai.response_normalizer import (
    WrongResponseTypeError,
    normalize_exercise_response,
    normalize_scenario_response,
)


def test_normalize_flat_scenario():
    raw = {"title": "Test", "passage": "Hello world", "summary_zh": "你好"}
    result = normalize_scenario_response(raw)
    assert result["passage"] == "Hello world"
    assert result["title"] == "Test"


def test_normalize_nested_scenario():
    raw = {"scenario": {"title": "Nested", "text": "A long passage here."}}
    result = normalize_scenario_response(raw)
    assert result["passage"] == "A long passage here."


def test_normalize_dialogue_fallback():
    raw = {
        "title": "Dialogue",
        "dialogue": [
            {"speaker": "A", "text": "Hello there."},
            {"speaker": "B", "text": "Hi back."},
        ],
    }
    result = normalize_scenario_response(raw)
    assert "Hello there" in result["passage"]


def test_normalize_missing_passage_raises():
    with pytest.raises(AIProviderError, match="missing 'passage'"):
        normalize_scenario_response({"title": "No content"})


def test_normalize_exercises_only_raises_wrong_type():
    with pytest.raises(WrongResponseTypeError, match="exercises instead of scenario"):
        normalize_scenario_response({"exercises": [{"type": "single_choice"}]})


def test_normalize_exercises_nested():
    raw = {"questions": [{"type": "single_choice", "question": "Q?", "options": ["a", "b"], "correct_label": "A"}]}
    result = normalize_exercise_response(raw)
    assert len(result["exercises"]) == 1
