from __future__ import annotations

from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

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


class SqlAlchemyVocabularyReadRepository:
    def __init__(self, session: Session):
        self._session = session

    def list_words(
        self,
        *,
        page: int = 1,
        page_size: int = 30,
        level: str | None = None,
        theme: str | None = None,
        search: str | None = None,
        letter: str | None = None,
        user_id: int | None = None,
    ) -> dict[str, Any]:
        query = apply_letter_filter(
            words_base_query(self._session, level=level, theme=theme, search=search),
            letter,
        )
        total = query.count()
        words = (
            query.order_by(func.lower(Word.lemma))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        progress_map: dict[int, int] = {}
        exam_tags_map: dict[int, list[str]] = {}
        if words:
            word_ids = [w.id for w in words]
            if user_id is not None:
                progresses = (
                    self._session.query(UserWordProgress)
                    .filter(
                        UserWordProgress.user_id == user_id,
                        UserWordProgress.word_id.in_(word_ids),
                    )
                    .all()
                )
                progress_map = {p.word_id: p.familiarity for p in progresses}
            tag_rows = (
                self._session.query(WordTag)
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
                "familiarity": progress_map.get(w.id) if user_id is not None else None,
                "exam_levels": resolve_exam_levels(w.level, exam_tags_map.get(w.id, [])),
            }
            for w in words
        ]
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def get_stats(self, user_id: int) -> dict[str, Any]:
        total = self._session.query(Word).count()
        learned = (
            self._session.query(UserWordProgress)
            .filter(UserWordProgress.user_id == user_id, UserWordProgress.familiarity > 0)
            .count()
        )
        mastered = (
            self._session.query(UserWordProgress)
            .filter(UserWordProgress.user_id == user_id, UserWordProgress.familiarity >= 5)
            .count()
        )
        now = utc_now()
        due_review = (
            self._session.query(UserWordProgress)
            .filter(
                UserWordProgress.user_id == user_id,
                UserWordProgress.next_review.isnot(None),
                UserWordProgress.next_review <= now,
            )
            .count()
        )
        return {
            "total": total,
            "cet4_count": count_words_for_exam_level(self._session, "cet4"),
            "cet6_count": count_words_for_exam_level(self._session, "cet6"),
            "pets1_count": count_words_for_exam_level(self._session, "pets1"),
            "pets2_count": count_words_for_exam_level(self._session, "pets2"),
            "pets3_count": count_words_for_exam_level(self._session, "pets3"),
            "pets4_count": count_words_for_exam_level(self._session, "pets4"),
            "pets5_count": count_words_for_exam_level(self._session, "pets5"),
            "learned": learned,
            "mastered": mastered,
            "due_review": due_review,
            "mastery_rate": round(mastered / total * 100, 1) if total else 0.0,
        }

    def list_groups(self) -> list[dict[str, Any]]:
        groups = self._session.query(WordGroup).all()
        return [
            {
                "id": g.id,
                "slug": g.slug,
                "name_zh": g.name_zh,
                "name_en": g.name_en,
                "description": g.description,
                "word_count": count_theme_tagged_words(self._session, g.slug),
            }
            for g in groups
        ]

    def list_letters(
        self,
        *,
        level: str | None = None,
        theme: str | None = None,
        search: str | None = None,
    ) -> list[str]:
        query = words_base_query(self._session, level=level, theme=theme, search=search)
        lemmas = [row[0] for row in query.with_entities(Word.lemma).all()]
        return collect_index_letters(lemmas)

    def get_detail(self, word_id: int, user_id: int | None = None) -> dict[str, Any]:
        word = (
            self._session.query(Word)
            .options(
                joinedload(Word.tags),
                joinedload(Word.group_memberships).joinedload(WordGroupMember.group),
            )
            .filter(Word.id == word_id)
            .first()
        )
        if not word:
            raise ValueError("Word not found")

        familiarity = 0
        if user_id is not None:
            progress = (
                self._session.query(UserWordProgress)
                .filter(
                    UserWordProgress.user_id == user_id,
                    UserWordProgress.word_id == word_id,
                )
                .first()
            )
            familiarity = progress.familiarity if progress else 0

        scenario_count = (
            self._session.query(ScenarioWord).filter(ScenarioWord.word_id == word_id).count()
        )
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
            "familiarity": familiarity if user_id is not None else None,
            "scenario_count": scenario_count,
            "exam_levels": resolve_exam_levels(word.level, exam_tag_list),
        }

    def get_lemma(self, word_id: int) -> str:
        word = self._session.query(Word).filter(Word.id == word_id).first()
        if not word:
            raise ValueError("Word not found")
        return word.lemma
