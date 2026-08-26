from __future__ import annotations

from typing import Any, Protocol


class ActivityReadRepository(Protocol):
    def get_overview(self, user_id: int) -> dict[str, Any]: ...

    def get_timeline(
        self, user_id: int, *, skip: int = 0, limit: int = 30
    ) -> tuple[list[dict[str, Any]], int]: ...
