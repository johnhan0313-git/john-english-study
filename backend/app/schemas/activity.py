from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.conversation import ConversationBrief
from app.schemas.scenario import ScenarioBrief


class HeatmapDay(BaseModel):
    date: str
    count: int


class ActivityContinueSection(BaseModel):
    active_conversations: list[ConversationBrief] = Field(default_factory=list)
    incomplete_scenarios: list[ScenarioBrief] = Field(default_factory=list)


class ActivityOverviewResponse(BaseModel):
    scenario_total: int
    scenario_this_week: int
    conversation_total: int
    conversation_active: int
    theme_counts: dict[str, int] = Field(default_factory=dict)
    heatmap: list[HeatmapDay] = Field(default_factory=list)
    continue_section: ActivityContinueSection = Field(alias="continue")

    model_config = {"populate_by_name": True}


class ScenarioCreatedEvent(BaseModel):
    type: str = "scenario_created"
    at: str
    scenario: ScenarioBrief


class ScenarioCompletedEvent(BaseModel):
    type: str = "scenario_completed"
    at: str
    scenario: ScenarioBrief
    score: float


class ConversationStartedEvent(BaseModel):
    type: str = "conversation_started"
    at: str
    conversation: ConversationBrief


class ConversationEndedEvent(BaseModel):
    type: str = "conversation_ended"
    at: str
    conversation: ConversationBrief


class ActivityTimelineResponse(BaseModel):
    items: list[dict]
    total: int
