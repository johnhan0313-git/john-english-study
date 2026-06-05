from __future__ import annotations

import json
from typing import Any


def parse_json_field(value: str | None, default: Any = None) -> Any:
    if not value:
        return default if default is not None else []
    return json.loads(value)


def dump_json_field(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)
