from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.schemas.progress import ProgressOverview, ReviewWordItem, WritingEvaluateRequest, WritingEvaluateResponse
from app.schemas.speaking import SpeakingEvaluateResponse
from app.services.ai.openai_provider import get_stt_provider
from app.services.speaking.evaluator import evaluate_speaking, evaluate_writing
from app.services.vocabulary.progress_service import get_progress_overview, get_review_words

router = APIRouter(prefix="/progress", tags=["progress"])


@router.get("/overview", response_model=ProgressOverview)
def progress_overview(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return ProgressOverview(**get_progress_overview(db, user.id))


@router.get("/review", response_model=list[ReviewWordItem])
def review_words(
    user: User = Depends(get_current_user),
    limit: int = 20,
    db: Session = Depends(get_db),
):
    return [ReviewWordItem(**w) for w in get_review_words(db, user.id, limit)]


@router.post("/writing/evaluate", response_model=WritingEvaluateResponse)
async def writing_evaluate(
    body: WritingEvaluateRequest,
    user: User = Depends(get_current_user),
):
    settings = get_settings()
    result = await evaluate_writing(settings, body.prompt, body.content, body.target_words)
    return WritingEvaluateResponse(**result)


@router.post("/speaking/evaluate", response_model=SpeakingEvaluateResponse)
async def speaking_evaluate(
    expected: str = Form(...),
    audio: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    settings = get_settings()
    audio_bytes = await audio.read()
    stt_provider = get_stt_provider(settings)
    if not stt_provider:
        raise HTTPException(
            status_code=503,
            detail="STT 未配置，请在 backend/.env 中设置 AI_STT_API_KEY。",
        )
    transcript = await stt_provider.speech_to_text(audio_bytes, audio.filename or "audio.webm")
    result = evaluate_speaking(expected, transcript)
    return SpeakingEvaluateResponse(**result)
