from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import joinedload

from app.infrastructure.unit_of_work import UnitOfWorkFactory
from app.models.progress import UserWordProgress
from app.models.scenario import ScenarioWord
from app.models.word import Word, WordGroup, WordGroupMember, WordTag
from app.services.vocabulary.definition_lookup import enrich_definitions
from app.services.vocabulary.exam_tags import count_words_for_exam_level
from app.services.vocabulary.levels import ALL_EXAM_LEVELS, is_exam_tag, resolve_exam_levels
from app.services.vocabulary.theme_tags import count_theme_tagged_words
from app.services.vocabulary.word_query import apply_letter_filter, collect_index_letters, words_base_query
from app.utils.json_helpers import parse_json_field
from app.utils.time import utc_now


@dataclass(frozen=True)
class ListWordsInput:
    page: int = 1
    page_size: int = 30
    level: str | None = None
    theme: str | None = None
    search: str | None = None
    letter: str | None = None
    user_id: int | None = None


@dataclass(frozen=True)
class GetWordStatsInput:
    user_id: int


@dataclass(frozen=True)
class GetWordDetailInput:
    word_id: int
    user_id: int | None = None


@dataclass(frozen=True)
class ListWordLettersInput:
    level: str | None = None
    theme: str | None = None
    search: str | None = None


@dataclass(frozen=True)
class GetWordLemmaInput:
    word_id: int


class ListWordsQuery:
    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

    def execute(self, inp: ListWordsInput) -> dict[str, Any]:
        with self._uow_factory() as uow:
            db = uow.session
            query = apply_letter_filter(
                words_base_query(db, level=inp.level, theme=inp.theme, search=inp.search),
                inp.letter,
            )
            total = query.count()
            words = (
                query.order_by(func.lower(Word.lemma))
                .offset((inp.page - 1) * inp.page_size)
                .limit(inp.page_size)
                .all()
            )

            progress_map: dict[int, int] = {}
            exam_tags_map: dict[int, list[str]] = {}
            if words:
                word_ids = [w.id for w in words]
                if inp.user_id is not None:
                    progresses = (
                        db.query(UserWordProgress)
                        .filter(
                            UserWordProgress.user_id == inp.user_id,
                            UserWordProgress.word_id.in_(word_ids),
                        )
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
                {
                    "id": w.id,
                    "lemma": w.lemma,
                    "phonetic": w.phonetic,
                    "level": w.level,
                    "pos": w.pos,
                    "definitions": enrich_definitions(w.lemma, parse_json_field(w.definitions, [])),
                    "familiarity": progress_map.get(w.id) if inp.user_id is not None else None,
                    "exam_levels": resolve_exam_levels(w.level, exam_tags_map.get(w.id, [])),
                }
                for w in words
            ]
            return {
                "items": items,
                "total": total,
                "page": inp.page,
                "page_size": inp.page_size,
            }


class GetWordStatsQuery:
    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

    def execute(self, inp: GetWordStatsInput) -> dict[str, Any]:
        with self._uow_factory() as uow:
            db = uow.session
            total = db.query(Word).count()
            learned = (
                db.query(UserWordProgress)
                .filter(UserWordProgress.user_id == inp.user_id, UserWordProgress.familiarity > 0)
                .count()
            )
            mastered = (
                db.query(UserWordProgress)
                .filter(UserWordProgress.user_id == inp.user_id, UserWordProgress.familiarity >= 5)
                .count()
            )
            now = utc_now()
            due_review = (
                db.query(UserWordProgress)
                .filter(
                    UserWordProgress.user_id == inp.user_id,
                    UserWordProgress.next_review.isnot(None),
                    UserWordProgress.next_review <= now,
                )
                .count()
            )
            return {
                "total": total,
                "cet4_count": count_words_for_exam_level(db, "cet4"),
                "cet6_count": count_words_for_exam_level(db, "cet6"),
                "pets1_count": count_words_for_exam_level(db, "pets1"),
                "pets2_count": count_words_for_exam_level(db, "pets2"),
                "pets3_count": count_words_for_exam_level(db, "pets3"),
                "pets4_count": count_words_for_exam_level(db, "pets4"),
                "pets5_count": count_words_for_exam_level(db, "pets5"),
                "learned": learned,
                "mastered": mastered,
                "due_review": due_review,
                "mastery_rate": round(mastered / total * 100, 1) if total else 0.0,
            }


class ListWordGroupsQuery:
    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

    def execute(self) -> list[dict[str, Any]]:
        with self._uow_factory() as uow:
            db = uow.session
            groups = db.query(WordGroup).all()
            return [
                {
                    "id": g.id,
                    "slug": g.slug,
                    "name_zh": g.name_zh,
                    "name_en": g.name_en,
                    "description": g.description,
                    "word_count": count_theme_tagged_words(db, g.slug),
                }
                for g in groups
            ]


class ListWordLettersQuery:
    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

    def execute(self, inp: ListWordLettersInput) -> list[str]:
        with self._uow_factory() as uow:
            query = words_base_query(
                uow.session, level=inp.level, theme=inp.theme, search=inp.search
            )
            lemmas = [row[0] for row in query.with_entities(Word.lemma).all()]
            return collect_index_letters(lemmas)


class GetWordDetailQuery:
    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

    def execute(self, inp: GetWordDetailInput) -> dict[str, Any]:
        with self._uow_factory() as uow:
            db = uow.session
            word = (
                db.query(Word)
                .options(
                    joinedload(Word.tags),
                    joinedload(Word.group_memberships).joinedload(WordGroupMember.group),
                )
                .filter(Word.id == inp.word_id)
                .first()
            )
            if not word:
                raise ValueError("Word not found")

            familiarity = 0
            if inp.user_id is not None:
                progress = (
                    db.query(UserWordProgress)
                    .filter(
                        UserWordProgress.user_id == inp.user_id,
                        UserWordProgress.word_id == inp.word_id,
                    )
                    .first()
                )
                familiarity = progress.familiarity if progress else 0

            scenario_count = db.query(ScenarioWord).filter(ScenarioWord.word_id == inp.word_id).count()
            groups = [m.group.slug for m in word.group_memberships if m.group]
            exam_tag_list = [t.tag for t in word.tags if is_exam_tag(t.tag)]

            return {
                "id": word.id,
                "lemma": word.lemma,
                "phonetic": word.phonetic,
                "level": word.level,
                "pos": word.pos,
                "definitions": enrich_definitions(word.lemma, parse_json_field(word.definitions, [])),
                "examples": parse_json_field(word.examples, []),
                "tags": [t.tag for t in word.tags if not is_exam_tag(t.tag)],
                "groups": groups,
                "familiarity": familiarity if inp.user_id is not None else None,
                "scenario_count": scenario_count,
                "exam_levels": resolve_exam_levels(word.level, exam_tag_list),
            }


class GetWordLemmaQuery:
    def __init__(self, uow_factory: UnitOfWorkFactory):
        self._uow_factory = uow_factory

    def execute(self, inp: GetWordLemmaInput) -> str:
        with self._uow_factory() as uow:
            word = uow.session.query(Word).filter(Word.id == inp.word_id).first()
            if not word:
                raise ValueError("Word not found")
            return word.lemma
