from __future__ import annotations

import logging

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.dictionary import DictionaryEntry
from app.services.vocabulary.definition_lookup import clear_lookup_cache
from app.services.vocabulary.dict_lookup_builder import fetch_dict_lookup

logger = logging.getLogger(__name__)

_BATCH_SIZE = 500


def seed_dictionary_entries(db: Session, *, force: bool = False) -> dict[str, int | bool]:
    existing = db.query(DictionaryEntry).count()
    if existing > 0 and not force:
        return {"skipped": True, "count": existing}

    lookup = fetch_dict_lookup()
    rows = [
        {
            "lemma": lemma,
            "definition": entry["definition"],
            "source": entry.get("source", "cet4"),
            "pos": entry.get("pos"),
        }
        for lemma, entry in lookup.items()
    ]

    table = DictionaryEntry.__table__
    for offset in range(0, len(rows), _BATCH_SIZE):
        batch = rows[offset : offset + _BATCH_SIZE]
        stmt = insert(table).values(batch)
        stmt = stmt.on_conflict_do_update(
            index_elements=[table.c.lemma],
            set_={
                "definition": stmt.excluded.definition,
                "source": stmt.excluded.source,
                "pos": stmt.excluded.pos,
            },
        )
        db.execute(stmt)

    db.commit()
    clear_lookup_cache()
    count = db.query(DictionaryEntry).count()
    logger.info("Seeded dictionary_entries (%s rows)", count)
    return {"skipped": False, "count": count}
