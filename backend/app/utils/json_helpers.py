from __future__ import annotations

import json
from typing import Any


def parse_json_field(value: str | dict | list | None, default: Any = None) -> Any:
    if value is None or value == "":
        return default if default is not None else []
    if isinstance(value, (dict, list)):
        return value
    return json.loads(value)


def dump_json_field(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)
