from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.application.media.media_command import materialize_word_audio
from app.application.vocabulary.vocabulary_query import (
    GetWordDetailInput,
    GetWordLemmaInput,
    GetWordStatsInput,
    ListWordLettersInput,
    ListWordsInput,
)
from app.auth.dependencies import get_current_user, get_current_user_optional
from app.composition.shared_composition import AppContainer, get_container
from app.config import get_settings
from app.models.user import User
from app.schemas.word import (
    WordBrief,
    WordDetail,
    WordGroupResponse,
    WordLettersResponse,
    WordListResponse,
    WordStatsResponse,
)
from app.services.ai.openai_provider import AIProviderError
from app.services.storage.responses import storage_stream_response

router = APIRouter(prefix="/words", tags=["words"])


@router.get("", response_model=WordListResponse)
def list_words(
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    level: str | None = None,
    theme: str | None = None,
    search: str | None = None,
    letter: str | None = None,
    user: User | None = Depends(get_current_user_optional),
    container: AppContainer = Depends(get_container),
):
    result = container.vocabulary.list_words.execute(
        ListWordsInput(
            page=page,
            page_size=page_size,
            level=level,
            theme=theme,
            search=search,
            letter=letter,
            user_id=user.id if user else None,
        )
    )
    return WordListResponse(
        items=[WordBrief(**item) for item in result["items"]],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
    )


@router.get("/stats", response_model=WordStatsResponse)
def word_stats(
    user: User = Depends(get_current_user),
    container: AppContainer = Depends(get_container),
):
    return WordStatsResponse(
        **container.vocabulary.stats.execute(GetWordStatsInput(user_id=user.id))
    )


@router.get("/groups", response_model=list[WordGroupResponse])
def list_groups(container: AppContainer = Depends(get_container)):
    return [WordGroupResponse(**g) for g in container.vocabulary.groups.execute()]


@router.get("/letters", response_model=WordLettersResponse)
def list_word_letters(
    level: str | None = None,
    theme: str | None = None,
    search: str | None = None,
    container: AppContainer = Depends(get_container),
):
    letters = container.vocabulary.letters.execute(
        ListWordLettersInput(level=level, theme=theme, search=search)
    )
    return WordLettersResponse(letters=letters)


@router.get("/{word_id}/audio")
async def get_word_audio(
    word_id: int,
    container: AppContainer = Depends(get_container),
):
    try:
        lemma = container.vocabulary.lemma.execute(GetWordLemmaInput(word_id=word_id))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    settings = get_settings()
    try:
        audio_key = await materialize_word_audio(word_id, lemma, settings)
    except AIProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return storage_stream_response(
        audio_key,
        media_type="audio/mpeg",
        filename=f"word_{word_id}.mp3",
    )


@router.get("/{word_id}", response_model=WordDetail)
def get_word(
    word_id: int,
    user: User | None = Depends(get_current_user_optional),
    container: AppContainer = Depends(get_container),
):
    try:
        detail = container.vocabulary.detail.execute(
            GetWordDetailInput(word_id=word_id, user_id=user.id if user else None)
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return WordDetail(**detail)
