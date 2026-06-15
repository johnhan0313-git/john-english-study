"""Make users.hashed_password nullable for passwordless auth."""

from typing import Optional, Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision = "b2c3d4e5f6a7"
down_revision: Optional[str] = "a1b2c3d4e5f6"
branch_labels: Optional[Sequence[str]] = None
depends_on: Optional[Sequence[str]] = None


def upgrade() -> None:
    bind = op.get_bind()
    if not inspect(bind).has_table("users"):
        return
    cols = {c["name"]: c for c in inspect(bind).get_columns("users")}
    password_col = cols.get("hashed_password")
    if password_col and password_col.get("nullable"):
        return

    with op.batch_alter_table("users") as batch:
        batch.alter_column(
            "hashed_password",
            existing_type=sa.String(256),
            nullable=True,
        )


def downgrade() -> None:
    raise NotImplementedError("Password nullable migration downgrade is not supported")
