from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.reference import GrammarPoint, PhoneticSymbol
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
from app.services.ai.tts_service import generate_speech_bytes
from app.services.storage.factory import get_storage
from app.services.storage.responses import storage_stream_response
from app.services.reference.import_reference import (
    GRAMMAR_CATEGORY_ZH,
    PHONETIC_CATEGORY_ZH,
    grammar_to_brief,
    grammar_to_detail,
    phonetic_to_brief,
    phonetic_to_detail,
)
from app.utils.json_helpers import parse_json_field
from app.services.reference.phonetic_audio import (
    PHONETIC_TTS_VOICE,
    build_phonetic_speech_text,
    build_phonetic_symbol_speech_text,
    phonetic_audio_key,
    resolve_phonetic_audio,
)

router = APIRouter(prefix="/reference", tags=["reference"])


@router.get("/phonetics", response_model=PhoneticListResponse)
def list_phonetics(
    category: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(PhoneticSymbol)
    if category:
        query = query.filter(PhoneticSymbol.category == category)
    if search:
        like = f"%{search}%"
        query = query.filter(
            (PhoneticSymbol.symbol.ilike(like))
            | (PhoneticSymbol.name_zh.ilike(like))
            | (PhoneticSymbol.name_en.ilike(like))
        )
    items = query.order_by(PhoneticSymbol.sort_order).all()
    briefs = [PhoneticBrief(**phonetic_to_brief(p)) for p in items]

    groups: list[PhoneticCategoryGroup] = []
    by_cat: dict[str, list[PhoneticBrief]] = {}
    for b in briefs:
        by_cat.setdefault(b.category, []).append(b)
    for cat, cat_items in by_cat.items():
        groups.append(PhoneticCategoryGroup(
            category=cat,
            category_zh=PHONETIC_CATEGORY_ZH.get(cat, cat),
            items=cat_items,
            count=len(cat_items),
        ))

    return PhoneticListResponse(items=briefs, groups=groups, total=len(briefs))


@router.get("/phonetics/{phonetic_id}", response_model=PhoneticDetail)
def get_phonetic(phonetic_id: int, db: Session = Depends(get_db)):
    p = db.query(PhoneticSymbol).filter(PhoneticSymbol.id == phonetic_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Phonetic symbol not found")
    return PhoneticDetail(**phonetic_to_detail(p))


@router.get("/phonetics/{phonetic_id}/audio")
async def get_phonetic_audio(
    phonetic_id: int,
    word: str | None = None,
    preview: bool = Query(False, description="仅播放第一个例词"),
    kind: str | None = Query(None, description="symbol=IPA 音标本身, 默认=例词"),
    db: Session = Depends(get_db),
):
    phonetic = db.query(PhoneticSymbol).filter(PhoneticSymbol.id == phonetic_id).first()
    if not phonetic:
        raise HTTPException(status_code=404, detail="Phonetic symbol not found")

    if kind not in (None, "symbol", "examples", "word"):
        raise HTTPException(status_code=400, detail="Invalid kind; use symbol, examples, or word")

    try:
        if kind == "symbol":
            audio_kind, resolved_word = "symbol", None
        elif kind == "examples":
            examples = parse_json_field(phonetic.examples, [])
            if not examples:
                raise ValueError("No example words for this phonetic symbol")
            audio_kind, resolved_word = "examples", None
        else:
            audio_kind, resolved_word = resolve_phonetic_audio(phonetic, word=word, preview=preview)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    settings = get_settings()
    audio_key = phonetic_audio_key(
        phonetic_id,
        kind=audio_kind,
        word=resolved_word,
    )
    storage = get_storage(settings)

    if not storage.exists(audio_key):
        try:
            if audio_kind == "symbol":
                speech_text = build_phonetic_symbol_speech_text(phonetic)
            else:
                speech_text = build_phonetic_speech_text(phonetic, resolved_word)
            audio = await generate_speech_bytes(speech_text, settings, voice=PHONETIC_TTS_VOICE)
            storage.put_bytes(audio_key, audio, "audio/mpeg")
        except AIProviderError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    filename = f"phonetic_{phonetic_id}.mp3"
    return storage_stream_response(audio_key, media_type="audio/mpeg", filename=filename)


@router.get("/grammar", response_model=GrammarListResponse)
def list_grammar(
    category: str | None = None,
    level: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(GrammarPoint)
    if category:
        query = query.filter(GrammarPoint.category == category)
    if level == "cet4":
        query = query.filter(GrammarPoint.level.in_(["cet4", "both"]))
    elif level == "cet6":
        query = query.filter(GrammarPoint.level.in_(["cet6", "both"]))
    if search:
        like = f"%{search}%"
        query = query.filter(
            (GrammarPoint.title.ilike(like)) | (GrammarPoint.summary.ilike(like))
        )
    items = query.order_by(GrammarPoint.sort_order).all()
    briefs = [GrammarBrief(**grammar_to_brief(g)) for g in items]

    groups: list[GrammarCategoryGroup] = []
    by_cat: dict[str, list[GrammarBrief]] = {}
    for b in briefs:
        by_cat.setdefault(b.category, []).append(b)
    for cat, cat_items in by_cat.items():
        groups.append(GrammarCategoryGroup(
            category=cat,
            category_zh=GRAMMAR_CATEGORY_ZH.get(cat, cat),
            items=cat_items,
            count=len(cat_items),
        ))

    return GrammarListResponse(items=briefs, groups=groups, total=len(briefs))


@router.get("/grammar/{slug}", response_model=GrammarDetail)
def get_grammar(slug: str, db: Session = Depends(get_db)):
    g = db.query(GrammarPoint).filter(GrammarPoint.slug == slug).first()
    if not g:
        raise HTTPException(status_code=404, detail="Grammar point not found")
    return GrammarDetail(**grammar_to_detail(g))
