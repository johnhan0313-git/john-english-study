from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.schemas.activity import ActivityOverviewResponse, ActivityTimelineResponse
from app.services.activity.service import ActivityService

router = APIRouter(prefix="/activity", tags=["activity"])


@router.get("/overview", response_model=ActivityOverviewResponse)
def activity_overview(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    settings = get_settings()
    service = ActivityService(db, timezone=settings.app_timezone)
    return ActivityOverviewResponse(**service.get_overview(user.id))


@router.get("/timeline", response_model=ActivityTimelineResponse)
def activity_timeline(
    user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db),
):
    settings = get_settings()
    service = ActivityService(db, timezone=settings.app_timezone)
    items, total = service.get_timeline(user.id, skip=skip, limit=limit)
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
