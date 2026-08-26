"""Drop all physical foreign-key constraints (logical IDs + indexes remain)."""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
from sqlalchemy import inspect

revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    for table in insp.get_table_names():
        for fk in insp.get_foreign_keys(table):
            name = fk.get("name")
            if not name:
                continue
            op.drop_constraint(name, table_name=table, type_="foreignkey")


def downgrade() -> None:
    # Irreversible by design: physical FKs are not restored.
    pass
