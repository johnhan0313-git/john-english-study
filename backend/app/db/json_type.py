from __future__ import annotations

import json
from typing import Any

from sqlalchemy.types import Text, TypeDecorator

from app.utils.json_helpers import dump_json_field, parse_json_field


class JSONField(TypeDecorator[Any]):
    impl = Text
    cache_ok = True

    def process_bind_param(self, value: Any, dialect: object) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            return value
        return dump_json_field(value)

    def process_result_value(self, value: str | None, dialect: object) -> Any:
        if value is None:
            return None
        return parse_json_field(value, None)
