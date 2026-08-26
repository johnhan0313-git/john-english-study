from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.application.activity.activity_query import GetActivityOverviewInput, GetActivityTimelineInput
from app.auth.dependencies import get_current_user
from app.composition.shared_composition import AppContainer, get_container
from app.models.user import User
from app.schemas.activity import ActivityOverviewResponse, ActivityTimelineResponse

router = APIRouter(prefix="/activity", tags=["activity"])


@router.get("/overview", response_model=ActivityOverviewResponse)
def activity_overview(
    user: User = Depends(get_current_user),
    container: AppContainer = Depends(get_container),
):
    result = container.activity.overview.execute(
        GetActivityOverviewInput(user_id=user.id, timezone=container.settings.app_timezone)
    )
    return ActivityOverviewResponse(**result)


@router.get("/timeline", response_model=ActivityTimelineResponse)
def activity_timeline(
    user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(30, ge=1, le=100),
    container: AppContainer = Depends(get_container),
):
    items, total = container.activity.timeline.execute(
        GetActivityTimelineInput(
            user_id=user.id,
            timezone=container.settings.app_timezone,
            skip=skip,
            limit=limit,
        )
    )
    serialized = []
    for item in items:
        entry = {
            "type": item["type"],
            "at": item["at"].isoformat() if hasattr(item["at"], "isoformat") else str(item["at"]),
        }
        if "scenario" in item:
            entry["scenario"] = item["scenario"]
        if "conversation" in item:
            entry["conversation"] = item["conversation"]
        if "score" in item:
            entry["score"] = item["score"]
        serialized.append(entry)
    return ActivityTimelineResponse(items=serialized, total=total)
