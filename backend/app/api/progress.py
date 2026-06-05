from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.schemas.progress import ProgressOverview, ReviewWordItem, WritingEvaluateRequest, WritingEvaluateResponse
from app.schemas.speaking import SpeakingEvaluateResponse
from app.services.ai.openai_provider import get_ai_provider
from app.services.speaking.evaluator import evaluate_speaking, evaluate_writing
from app.services.vocabulary.progress_service import get_progress_overview, get_review_words

router = APIRouter(prefix="/progress", tags=["progress"])


@router.get("/overview", response_model=ProgressOverview)
def progress_overview(device_id: str = "default", db: Session = Depends(get_db)):
    return ProgressOverview(**get_progress_overview(db, device_id))


@router.get("/review", response_model=list[ReviewWordItem])
def review_words(device_id: str = "default", limit: int = 20, db: Session = Depends(get_db)):
    return [ReviewWordItem(**w) for w in get_review_words(db, device_id, limit)]


@router.post("/writing/evaluate", response_model=WritingEvaluateResponse)
async def writing_evaluate(body: WritingEvaluateRequest):
    settings = get_settings()
    result = await evaluate_writing(settings, body.prompt, body.content, body.target_words)
    return WritingEvaluateResponse(**result)


@router.post("/speaking/evaluate", response_model=SpeakingEvaluateResponse)
async def speaking_evaluate(
    expected: str = Form(...),
    audio: UploadFile = File(...),
):
    settings = get_settings()
    audio_bytes = await audio.read()
    provider = get_ai_provider(settings)
    if settings.ai_api_key:
        transcript = await provider.speech_to_text(audio_bytes, audio.filename or "audio.webm")
    else:
        transcript = expected
    result = evaluate_speaking(expected, transcript)
    return SpeakingEvaluateResponse(**result)
