"""Allow nullable device_id on user-owned tables after auth migration."""

from typing import Optional, Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision = "c3d4e5f6a7b8"
down_revision: Optional[str] = "b2c3d4e5f6a7"
branch_labels: Optional[Sequence[str]] = None
depends_on: Optional[Sequence[str]] = None


def _device_id_nullable(bind, table: str) -> bool:
    if not inspect(bind).has_table(table):
        return True
    cols = {c["name"]: c for c in inspect(bind).get_columns(table)}
    device_col = cols.get("device_id")
    if not device_col:
        return True
    return bool(device_col.get("nullable"))


def upgrade() -> None:
    bind = op.get_bind()
    for table in ("conversation_sessions", "scenario_attempts", "scenarios"):
        if _device_id_nullable(bind, table):
            continue
        with op.batch_alter_table(table) as batch:
            batch.alter_column(
                "device_id",
                existing_type=sa.String(64),
                nullable=True,
            )


def downgrade() -> None:
    raise NotImplementedError("Nullable device_id migration downgrade is not supported")
