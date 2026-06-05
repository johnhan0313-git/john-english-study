from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.progress import UserWordProgress
from app.models.scenario import ScenarioWord
from app.models.word import Word, WordGroup, WordGroupMember, WordTag
from app.schemas.word import WordBrief, WordDetail, WordGroupResponse, WordListResponse, WordStatsResponse
from app.utils.json_helpers import parse_json_field

router = APIRouter(prefix="/words", tags=["words"])


@router.get("", response_model=WordListResponse)
def list_words(
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    level: str | None = None,
    theme: str | None = None,
    search: str | None = None,
    device_id: str = "default",
    db: Session = Depends(get_db),
):
    query = db.query(Word)
    if level == "cet4":
        query = query.filter(Word.level.in_(["cet4", "both"]))
    elif level == "cet6":
        query = query.filter(Word.level.in_(["cet6", "both"]))
    if search:
        query = query.filter(Word.lemma.ilike(f"%{search}%"))
    if theme:
        query = query.join(WordTag, WordTag.word_id == Word.id).filter(WordTag.tag == theme)
    total = query.count()
    words = query.order_by(Word.lemma).offset((page - 1) * page_size).limit(page_size).all()

    progress_map = {}
    if words:
        word_ids = [w.id for w in words]
        progresses = (
            db.query(UserWordProgress)
            .filter(UserWordProgress.device_id == device_id, UserWordProgress.word_id.in_(word_ids))
            .all()
        )
        progress_map = {p.word_id: p.familiarity for p in progresses}

    items = [
        WordBrief(
            id=w.id,
            lemma=w.lemma,
            phonetic=w.phonetic,
            level=w.level,
            pos=w.pos,
            definitions=parse_json_field(w.definitions, []),
            familiarity=progress_map.get(w.id),
        )
        for w in words
    ]
    return WordListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/stats", response_model=WordStatsResponse)
def word_stats(device_id: str = "default", db: Session = Depends(get_db)):
    total = db.query(Word).count()
    cet4_count = db.query(Word).filter(Word.level.in_(["cet4", "both"])).count()
    cet6_count = db.query(Word).filter(Word.level.in_(["cet6", "both"])).count()
    learned = (
        db.query(UserWordProgress)
        .filter(UserWordProgress.device_id == device_id, UserWordProgress.familiarity > 0)
        .count()
    )
    mastered = (
        db.query(UserWordProgress)
        .filter(UserWordProgress.device_id == device_id, UserWordProgress.familiarity >= 5)
        .count()
    )
    from datetime import datetime

    now = datetime.utcnow()
    due_review = (
        db.query(UserWordProgress)
        .filter(
            UserWordProgress.device_id == device_id,
            UserWordProgress.next_review.isnot(None),
            UserWordProgress.next_review <= now,
        )
        .count()
    )
    return WordStatsResponse(
        total=total,
        cet4_count=cet4_count,
        cet6_count=cet6_count,
        learned=learned,
        mastered=mastered,
        due_review=due_review,
        mastery_rate=round(mastered / total * 100, 1) if total else 0.0,
    )


@router.get("/groups", response_model=list[WordGroupResponse])
def list_groups(db: Session = Depends(get_db)):
    groups = db.query(WordGroup).all()
    result = []
    for g in groups:
        count = db.query(WordGroupMember).filter(WordGroupMember.group_id == g.id).count()
        result.append(
            WordGroupResponse(
                id=g.id,
                slug=g.slug,
                name_zh=g.name_zh,
                name_en=g.name_en,
                description=g.description,
                word_count=count,
            )
        )
    return result


@router.get("/{word_id}", response_model=WordDetail)
def get_word(word_id: int, device_id: str = "default", db: Session = Depends(get_db)):
    word = (
        db.query(Word)
        .options(joinedload(Word.tags), joinedload(Word.group_memberships).joinedload(WordGroupMember.group))
        .filter(Word.id == word_id)
        .first()
    )
    if not word:
        raise HTTPException(status_code=404, detail="Word not found")

    progress = (
        db.query(UserWordProgress)
        .filter(UserWordProgress.device_id == device_id, UserWordProgress.word_id == word_id)
        .first()
    )
    scenario_count = db.query(ScenarioWord).filter(ScenarioWord.word_id == word_id).count()
    groups = [m.group.slug for m in word.group_memberships if m.group]

    return WordDetail(
        id=word.id,
        lemma=word.lemma,
        phonetic=word.phonetic,
        level=word.level,
        pos=word.pos,
        definitions=parse_json_field(word.definitions, []),
        examples=parse_json_field(word.examples, []),
        tags=[t.tag for t in word.tags],
        groups=groups,
        familiarity=progress.familiarity if progress else 0,
        scenario_count=scenario_count,
    )
