from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.auth.dependencies import get_current_user, get_current_user_optional
from app.database import get_db
from app.models.progress import UserWordProgress
from app.models.scenario import ScenarioWord
from app.models.user import User
from app.models.word import Word, WordGroup, WordGroupMember, WordTag
from app.schemas.word import (
    WordBrief,
    WordDetail,
    WordGroupResponse,
    WordLettersResponse,
    WordListResponse,
    WordStatsResponse,
)
from app.services.vocabulary.definition_lookup import enrich_definitions
from app.services.vocabulary.exam_tags import count_words_for_exam_level
from app.services.vocabulary.levels import ALL_EXAM_LEVELS, is_exam_tag, resolve_exam_levels
from app.services.vocabulary.word_query import apply_letter_filter, collect_index_letters, words_base_query
from app.utils.json_helpers import parse_json_field
from app.utils.time import utc_now

router = APIRouter(prefix="/words", tags=["words"])


@router.get("", response_model=WordListResponse)
def list_words(
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    level: str | None = None,
    theme: str | None = None,
    search: str | None = None,
    letter: str | None = None,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
):
    query = apply_letter_filter(words_base_query(db, level=level, theme=theme, search=search), letter)
    total = query.count()
    words = query.order_by(func.lower(Word.lemma)).offset((page - 1) * page_size).limit(page_size).all()

    progress_map: dict[int, int] = {}
    exam_tags_map: dict[int, list[str]] = {}
    if words:
        word_ids = [w.id for w in words]
        if user:
            progresses = (
                db.query(UserWordProgress)
                .filter(UserWordProgress.user_id == user.id, UserWordProgress.word_id.in_(word_ids))
                .all()
            )
            progress_map = {p.word_id: p.familiarity for p in progresses}
        tag_rows = (
            db.query(WordTag)
            .filter(WordTag.word_id.in_(word_ids), WordTag.tag.in_(ALL_EXAM_LEVELS))
            .all()
        )
        for row in tag_rows:
            exam_tags_map.setdefault(row.word_id, []).append(row.tag)

    items = [
        WordBrief(
            id=w.id,
            lemma=w.lemma,
            phonetic=w.phonetic,
            level=w.level,
            pos=w.pos,
            definitions=enrich_definitions(w.lemma, parse_json_field(w.definitions, [])),
            familiarity=progress_map.get(w.id) if user else None,
            exam_levels=resolve_exam_levels(w.level, exam_tags_map.get(w.id, [])),
        )
        for w in words
    ]
    return WordListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/stats", response_model=WordStatsResponse)
def word_stats(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    total = db.query(Word).count()
    cet4_count = count_words_for_exam_level(db, "cet4")
    cet6_count = count_words_for_exam_level(db, "cet6")
    learned = (
        db.query(UserWordProgress)
        .filter(UserWordProgress.user_id == user.id, UserWordProgress.familiarity > 0)
        .count()
    )
    mastered = (
        db.query(UserWordProgress)
        .filter(UserWordProgress.user_id == user.id, UserWordProgress.familiarity >= 5)
        .count()
    )
    now = utc_now()
    due_review = (
        db.query(UserWordProgress)
        .filter(
            UserWordProgress.user_id == user.id,
            UserWordProgress.next_review.isnot(None),
            UserWordProgress.next_review <= now,
        )
        .count()
    )
    return WordStatsResponse(
        total=total,
        cet4_count=cet4_count,
        cet6_count=cet6_count,
        pets1_count=count_words_for_exam_level(db, "pets1"),
        pets2_count=count_words_for_exam_level(db, "pets2"),
        pets3_count=count_words_for_exam_level(db, "pets3"),
        pets4_count=count_words_for_exam_level(db, "pets4"),
        pets5_count=count_words_for_exam_level(db, "pets5"),
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


@router.get("/letters", response_model=WordLettersResponse)
def list_word_letters(
    level: str | None = None,
    theme: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
):
    query = words_base_query(db, level=level, theme=theme, search=search)
    lemmas = [row[0] for row in query.with_entities(Word.lemma).all()]
    return WordLettersResponse(letters=collect_index_letters(lemmas))


@router.get("/{word_id}", response_model=WordDetail)
def get_word(
    word_id: int,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_current_user_optional),
):
    word = (
        db.query(Word)
        .options(joinedload(Word.tags), joinedload(Word.group_memberships).joinedload(WordGroupMember.group))
        .filter(Word.id == word_id)
        .first()
    )
    if not word:
        raise HTTPException(status_code=404, detail="Word not found")

    familiarity = 0
    if user:
        progress = (
            db.query(UserWordProgress)
            .filter(UserWordProgress.user_id == user.id, UserWordProgress.word_id == word_id)
            .first()
        )
        familiarity = progress.familiarity if progress else 0

    scenario_count = db.query(ScenarioWord).filter(ScenarioWord.word_id == word_id).count()
    groups = [m.group.slug for m in word.group_memberships if m.group]
    exam_tag_list = [t.tag for t in word.tags if is_exam_tag(t.tag)]

    return WordDetail(
        id=word.id,
        lemma=word.lemma,
        phonetic=word.phonetic,
        level=word.level,
        pos=word.pos,
        definitions=enrich_definitions(word.lemma, parse_json_field(word.definitions, [])),
        examples=parse_json_field(word.examples, []),
        tags=[t.tag for t in word.tags if not is_exam_tag(t.tag)],
        groups=groups,
        familiarity=familiarity if user else None,
        scenario_count=scenario_count,
        exam_levels=resolve_exam_levels(word.level, exam_tag_list),
    )
