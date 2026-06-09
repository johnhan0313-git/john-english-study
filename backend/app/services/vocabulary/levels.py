from __future__ import annotations

PETS_LEVELS = ("pets1", "pets2", "pets3", "pets4", "pets5")
CET_LEVELS = ("cet4", "cet6")
ALL_EXAM_LEVELS = ("cet4", "cet6", *PETS_LEVELS)

EXAM_LEVEL_ORDER = {level: index for index, level in enumerate(ALL_EXAM_LEVELS)}

LEVEL_LABELS: dict[str, str] = {
    "cet4": "CET-4",
    "cet6": "CET-6",
    "both": "CET-4/6",
    "pets1": "PETS-1",
    "pets2": "PETS-2",
    "pets3": "PETS-3",
    "pets4": "PETS-4",
    "pets5": "PETS-5",
}

# PETS 与 CET 难度对应：PETS-3≈四级，PETS-5≈六级
PETS_INHERIT_FROM_CET: dict[str, list[str]] = {
    "pets3": ["cet4", "both"],
    "pets4": ["both"],
    "pets5": ["cet6", "both"],
}


def is_exam_tag(tag: str) -> bool:
    return tag in ALL_EXAM_LEVELS


def levels_from_word_field(level: str) -> set[str]:
    if level == "both":
        return {"cet4", "cet6"}
    if level in ALL_EXAM_LEVELS:
        return {level}
    return set()


def resolve_exam_levels(word_level: str, tags: list[str]) -> list[str]:
    exams = levels_from_word_field(word_level)
    for tag in tags:
        if is_exam_tag(tag):
            exams.add(tag)
    return sorted(exams, key=lambda x: EXAM_LEVEL_ORDER.get(x, 99))


def exam_level_filter(db, exam_level: str):
    """Word matches if primary level or any exam tag includes this library."""
    from sqlalchemy import or_

    from app.models.word import Word, WordTag

    level_match = levels_from_word_field
    # Expand: cet4 filter matches level cet4/both OR tag cet4 OR tag pets3? 
    # User wants each library independent - pets3 tagged words should appear in pets3 filter only,
    # cet4 filter uses level cet4/both OR explicit cet4 tag
    conditions = []
    if exam_level == "cet4":
        conditions.append(Word.level.in_(["cet4", "both"]))
    elif exam_level == "cet6":
        conditions.append(Word.level.in_(["cet6", "both"]))
    elif exam_level in PETS_LEVELS:
        conditions.append(Word.level == exam_level)
    else:
        conditions.append(Word.level == exam_level)

    tagged_ids = db.query(WordTag.word_id).filter(WordTag.tag == exam_level)
    conditions.append(Word.id.in_(tagged_ids))
    return or_(*conditions)


def level_filter_values(level: str) -> list[str]:
    if level == "cet4":
        return ["cet4", "both"]
    if level == "cet6":
        return ["cet6", "both"]
    if level in PETS_LEVELS:
        return [level]
    return [level]
