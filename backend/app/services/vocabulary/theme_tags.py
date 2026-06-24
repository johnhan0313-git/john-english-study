from __future__ import annotations

import json
import logging
from functools import lru_cache

from sqlalchemy.orm import Session

from app.models.word import Word, WordTag
from app.seed_paths import resolve_seed_path
from app.services.vocabulary.levels import is_exam_tag
from app.utils.json_helpers import parse_json_field

logger = logging.getLogger(__name__)


def _load_word_groups() -> list[dict]:
    path = resolve_seed_path("word_groups.json")
    if not path.is_file():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def get_theme_slugs() -> frozenset[str]:
    return frozenset(group["slug"] for group in _load_word_groups())


def is_theme_tag(tag: str) -> bool:
    return tag in get_theme_slugs()


@lru_cache(maxsize=1)
def _load_theme_tag_rules() -> dict[str, dict[str, list[str]]]:
    path = resolve_seed_path("theme_tag_rules.json")
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _lemma_matches(lemma: str, keyword: str) -> bool:
    if len(keyword) < 3:
        return False
    if lemma == keyword:
        return True
    if len(keyword) >= 4 and lemma.startswith(keyword):
        return True
    if len(keyword) >= 5 and keyword in lemma:
        return True
    return False


def _definition_matches(definitions: list[str], keywords: list[str]) -> bool:
    if not definitions or not keywords:
        return False
    text = "".join(definitions)
    return any(keyword in text for keyword in keywords)


def infer_theme_tags(lemma: str, definitions: list[str]) -> set[str]:
    lemma_l = lemma.strip().lower()
    if not lemma_l:
        return set()

    themes: set[str] = set()
    for slug, rules in _load_theme_tag_rules().items():
        if slug not in get_theme_slugs():
            continue
        lemma_keywords = rules.get("lemma", [])
        definition_keywords = rules.get("definition_zh", [])
        if any(_lemma_matches(lemma_l, keyword.lower()) for keyword in lemma_keywords):
            themes.add(slug)
            continue
        if _definition_matches(definitions, definition_keywords):
            themes.add(slug)
    return themes


def _seed_theme_tags() -> dict[str, set[str]]:
    mapping: dict[str, set[str]] = {}
    for group in _load_word_groups():
        slug = group["slug"]
        for lemma in group.get("words", []):
            key = lemma.strip().lower()
            if not key:
                continue
            mapping.setdefault(key, set()).add(slug)
    return mapping


def sync_all_theme_tags(db: Session) -> dict[str, int]:
    """Apply theme WordTags from seed lemmas + keyword rules across the full vocabulary."""
    theme_slugs = get_theme_slugs()
    seed_map = _seed_theme_tags()

    existing = {
        (row[0], row[1])
        for row in db.query(WordTag.word_id, WordTag.tag).filter(WordTag.tag.in_(theme_slugs)).all()
    }

    added = 0
    tagged_words: set[int] = set()
    per_theme: dict[str, int] = {slug: 0 for slug in theme_slugs}

    words = db.query(Word).all()
    for word in words:
        definitions = parse_json_field(word.definitions, [])
        themes = infer_theme_tags(word.lemma, definitions)
        themes.update(seed_map.get(word.lemma.lower(), set()))

        for theme in themes:
            if theme not in theme_slugs:
                continue
            key = (word.id, theme)
            if key in existing:
                per_theme[theme] += 1
                tagged_words.add(word.id)
                continue
            db.add(WordTag(word_id=word.id, tag=theme))
            existing.add(key)
            added += 1
            per_theme[theme] += 1
            tagged_words.add(word.id)

    if added:
        db.commit()

    logger.info(
        "Theme tags synced: added=%s words_tagged=%s themes=%s",
        added,
        len(tagged_words),
        {slug: per_theme[slug] for slug in sorted(per_theme)},
    )
    return {
        "added": added,
        "words_tagged": len(tagged_words),
        "per_theme": per_theme,
    }


def count_theme_tagged_words(db: Session, theme: str) -> int:
    return db.query(WordTag.word_id).filter(WordTag.tag == theme).distinct().count()


def non_exam_tags(tags: list[str]) -> list[str]:
    return [tag for tag in tags if is_theme_tag(tag)]
