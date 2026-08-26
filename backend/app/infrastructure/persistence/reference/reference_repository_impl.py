from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.domains.reference.reference_repository import PhoneticAudioSource
from app.models.reference import GrammarPoint, PhoneticSymbol
from app.services.reference.import_reference import (
    GRAMMAR_CATEGORY_ZH,
    PHONETIC_CATEGORY_ZH,
    grammar_to_brief,
    grammar_to_detail,
    phonetic_to_brief,
    phonetic_to_detail,
)
from app.utils.json_helpers import parse_json_field


class SqlAlchemyReferenceReadRepository:
    def __init__(self, session: Session):
        self._session = session

    def list_phonetics(
        self, *, category: str | None = None, search: str | None = None
    ) -> dict[str, Any]:
        query = self._session.query(PhoneticSymbol)
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
        briefs = [phonetic_to_brief(p) for p in items]

        groups: list[dict[str, Any]] = []
        by_cat: dict[str, list[dict]] = {}
        for b in briefs:
            by_cat.setdefault(b["category"], []).append(b)
        for cat, cat_items in by_cat.items():
            groups.append(
                {
                    "category": cat,
                    "category_zh": PHONETIC_CATEGORY_ZH.get(cat, cat),
                    "items": cat_items,
                    "count": len(cat_items),
                }
            )

        return {"items": briefs, "groups": groups, "total": len(briefs)}

    def get_phonetic(self, phonetic_id: int) -> dict[str, Any]:
        p = (
            self._session.query(PhoneticSymbol)
            .filter(PhoneticSymbol.id == phonetic_id)
            .first()
        )
        if not p:
            raise ValueError("Phonetic symbol not found")
        return phonetic_to_detail(p)

    def get_phonetic_audio_source(self, phonetic_id: int) -> PhoneticAudioSource | None:
        p = (
            self._session.query(PhoneticSymbol)
            .filter(PhoneticSymbol.id == phonetic_id)
            .first()
        )
        if not p:
            return None
        return PhoneticAudioSource(
            id=p.id,
            symbol=p.symbol,
            name_en=p.name_en,
            examples=parse_json_field(p.examples, []),
        )

    def list_grammar(
        self,
        *,
        category: str | None = None,
        level: str | None = None,
        search: str | None = None,
    ) -> dict[str, Any]:
        query = self._session.query(GrammarPoint)
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
        briefs = [grammar_to_brief(g) for g in items]

        groups: list[dict[str, Any]] = []
        by_cat: dict[str, list[dict]] = {}
        for b in briefs:
            by_cat.setdefault(b["category"], []).append(b)
        for cat, cat_items in by_cat.items():
            groups.append(
                {
                    "category": cat,
                    "category_zh": GRAMMAR_CATEGORY_ZH.get(cat, cat),
                    "items": cat_items,
                    "count": len(cat_items),
                }
            )

        return {"items": briefs, "groups": groups, "total": len(briefs)}

    def get_grammar(self, slug: str) -> dict[str, Any]:
        g = self._session.query(GrammarPoint).filter(GrammarPoint.slug == slug).first()
        if not g:
            raise ValueError("Grammar point not found")
        return grammar_to_detail(g)
