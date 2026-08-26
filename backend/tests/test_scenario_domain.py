from __future__ import annotations

"""Domain unit tests for Scenario aggregate."""

from app.domains.scenario.scenario_domain import ScenarioAggregate, ScenarioContent


def test_create_generated_requires_at_least_three_words():
    try:
        ScenarioAggregate.create_generated(
            title="t",
            theme="daily",
            level="cet4",
            scenario_type="narrative",
            content=ScenarioContent(passage="hello"),
            dialogue=[],
            user_id=1,
            word_ids=[1, 2],
        )
        assert False, "expected ValueError"
    except ValueError as e:
        assert "Not enough words" in str(e)


def test_create_generated_ok():
    agg = ScenarioAggregate.create_generated(
        title="Airport Day",
        theme="travel",
        level="cet4",
        scenario_type="narrative",
        content=ScenarioContent(passage="passage", summary_zh="摘要"),
        dialogue=[],
        user_id=7,
        word_ids=[1, 2, 3],
        is_daily=True,
        daily_date="2026-08-26",
        daily_kind="review",
    )
    assert agg.id is None
    assert agg.user_id == 7
    assert len(agg.words) == 3
    assert agg.is_daily is True
