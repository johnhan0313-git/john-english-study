from __future__ import annotations

import logging
from pathlib import Path

from app.config import Settings, get_settings
from app.data_paths import get_data_dir
from app.services.vocabulary.definition_lookup import clear_lookup_cache
from app.services.vocabulary.dict_lookup_builder import ensure_dict_lookup

logger = logging.getLogger(__name__)


def ensure_data_files(settings: Settings | None = None) -> dict[str, str]:
    cfg = settings or get_settings()
    data_dir = get_data_dir(cfg)
    data_dir.mkdir(parents=True, exist_ok=True)

    result: dict[str, str] = {"data_dir": str(data_dir)}

    dict_path = ensure_dict_lookup(data_dir)
    clear_lookup_cache()
    if dict_path:
        result["dict_lookup"] = str(dict_path)
    else:
        result["dict_lookup"] = "missing"

    for name in ("word_groups.json", "pets_words.json", "dict_lookup_overrides.json"):
        path = data_dir / name
        result[name] = "present" if path.is_file() else "absent"

    logger.info("Data directory ready: %s", result)
    return result
