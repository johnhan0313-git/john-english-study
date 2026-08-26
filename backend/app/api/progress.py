from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.application.progress.ability_command import (
    EvaluateSpeakingInput,
    EvaluateWritingInput,
    GenerateWritingSampleInput,
)
from app.application.progress.progress_query import GetProgressOverviewInput, GetReviewWordsInput
from app.auth.dependencies import get_current_user
from app.composition.shared_composition import AppContainer, get_container
from app.config import get_settings
from app.models.user import User
from app.schemas.progress import (
    ProgressOverview,
    ReviewWordItem,
    WritingEvaluateRequest,
    WritingEvaluateResponse,
    WritingSampleRequest,
    WritingSampleResponse,
)
from app.schemas.speaking import SpeakingEvaluateResponse
from app.services.ai.openai_provider import get_stt_provider

router = APIRouter(prefix="/progress", tags=["progress"])


@router.get("/overview", response_model=ProgressOverview)
def progress_overview(
    user: User = Depends(get_current_user),
    container: AppContainer = Depends(get_container),
):
    return ProgressOverview(
        **container.progress.overview.execute(GetProgressOverviewInput(user_id=user.id))
    )


@router.get("/review", response_model=list[ReviewWordItem])
def review_words(
    user: User = Depends(get_current_user),
    limit: int = 20,
    container: AppContainer = Depends(get_container),
):
    return [
        ReviewWordItem(**w)
        for w in container.progress.review_words.execute(
            GetReviewWordsInput(user_id=user.id, limit=limit)
        )
    ]


@router.post("/writing/evaluate", response_model=WritingEvaluateResponse)
async def writing_evaluate(
    body: WritingEvaluateRequest,
    user: User = Depends(get_current_user),
    container: AppContainer = Depends(get_container),
):
    result = await container.progress.evaluate_writing.execute(
        EvaluateWritingInput(
            prompt=body.prompt,
            content=body.content,
            target_words=list(body.target_words or []),
        )
    )
    return WritingEvaluateResponse(**result)


@router.post("/writing/sample", response_model=WritingSampleResponse)
async def writing_sample(
    body: WritingSampleRequest,
    user: User = Depends(get_current_user),
    container: AppContainer = Depends(get_container),
):
    try:
        result = await container.progress.generate_writing_sample.execute(
            GenerateWritingSampleInput(
                prompt=body.prompt,
                target_words=list(body.target_words or []),
                level=body.level,
                theme=body.theme,
                regenerate=body.regenerate,
            )
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Writing sample generation failed: {e}") from e
    return WritingSampleResponse(**result)


@router.post("/speaking/evaluate", response_model=SpeakingEvaluateResponse)
async def speaking_evaluate(
    expected: str = Form(...),
    audio: UploadFile = File(...),
    user: User = Depends(get_current_user),
    container: AppContainer = Depends(get_container),
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
    result = container.progress.evaluate_speaking.execute(
        EvaluateSpeakingInput(expected=expected, transcript=transcript)
    )
    return SpeakingEvaluateResponse(**result)
