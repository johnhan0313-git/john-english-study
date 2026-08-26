from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.application.reference.reference_query import (
    GetGrammarInput,
    GetPhoneticInput,
    ListGrammarInput,
    ListPhoneticsInput,
    MaterializePhoneticAudioInput,
)
from app.composition.shared_composition import AppContainer, get_container
from app.schemas.reference import (
    GrammarBrief,
    GrammarCategoryGroup,
    GrammarDetail,
    GrammarListResponse,
    PhoneticBrief,
    PhoneticCategoryGroup,
    PhoneticDetail,
    PhoneticListResponse,
)
from app.services.ai.openai_provider import AIProviderError
from app.services.storage.responses import storage_stream_response

router = APIRouter(prefix="/reference", tags=["reference"])


@router.get("/phonetics", response_model=PhoneticListResponse)
def list_phonetics(
    category: str | None = None,
    search: str | None = None,
    container: AppContainer = Depends(get_container),
):
    result = container.reference.list_phonetics.execute(
        ListPhoneticsInput(category=category, search=search)
    )
    return PhoneticListResponse(
        items=[PhoneticBrief(**item) for item in result["items"]],
        groups=[
            PhoneticCategoryGroup(
                category=g["category"],
                category_zh=g["category_zh"],
                items=[PhoneticBrief(**item) for item in g["items"]],
                count=g["count"],
            )
            for g in result["groups"]
        ],
        total=result["total"],
    )


@router.get("/phonetics/{phonetic_id}", response_model=PhoneticDetail)
def get_phonetic(phonetic_id: int, container: AppContainer = Depends(get_container)):
    try:
        detail = container.reference.get_phonetic.execute(GetPhoneticInput(phonetic_id=phonetic_id))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return PhoneticDetail(**detail)


@router.get("/phonetics/{phonetic_id}/audio")
async def get_phonetic_audio(
    phonetic_id: int,
    word: str | None = None,
    preview: bool = Query(False, description="仅播放第一个例词"),
    kind: str | None = Query(None, description="symbol=IPA 音标本身, 默认=例词"),
    container: AppContainer = Depends(get_container),
):
    try:
        audio_key = await container.reference.materialize_phonetic_audio.execute(
            MaterializePhoneticAudioInput(
                phonetic_id=phonetic_id,
                word=word,
                preview=preview,
                kind=kind,
            )
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except AIProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return storage_stream_response(
        audio_key,
        media_type="audio/mpeg",
        filename=f"phonetic_{phonetic_id}.mp3",
    )


@router.get("/grammar", response_model=GrammarListResponse)
def list_grammar(
    category: str | None = None,
    level: str | None = None,
    search: str | None = None,
    container: AppContainer = Depends(get_container),
):
    result = container.reference.list_grammar.execute(
        ListGrammarInput(category=category, level=level, search=search)
    )
    return GrammarListResponse(
        items=[GrammarBrief(**item) for item in result["items"]],
        groups=[
            GrammarCategoryGroup(
                category=g["category"],
                category_zh=g["category_zh"],
                items=[GrammarBrief(**item) for item in g["items"]],
                count=g["count"],
            )
            for g in result["groups"]
        ],
        total=result["total"],
    )


@router.get("/grammar/{slug}", response_model=GrammarDetail)
def get_grammar(slug: str, container: AppContainer = Depends(get_container)):
    try:
        detail = container.reference.get_grammar.execute(GetGrammarInput(slug=slug))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return GrammarDetail(**detail)
