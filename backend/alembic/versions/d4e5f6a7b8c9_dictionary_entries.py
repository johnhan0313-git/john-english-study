"""Add dictionary_entries table for vocabulary definitions."""

from typing import Optional, Sequence

import sqlalchemy as sa
from alembic import op

revision = "d4e5f6a7b8c9"
down_revision: Optional[str] = "c3d4e5f6a7b8"
branch_labels: Optional[Sequence[str]] = None
depends_on: Optional[Sequence[str]] = None


def upgrade() -> None:
    op.create_table(
        "dictionary_entries",
        sa.Column("lemma", sa.String(length=128), nullable=False),
        sa.Column("definition", sa.Text(), nullable=False),
        sa.Column("pos", sa.String(length=32), nullable=True),
        sa.Column("source", sa.String(length=32), nullable=False, server_default="cet4"),
        sa.PrimaryKeyConstraint("lemma"),
    )


def downgrade() -> None:
    op.drop_table("dictionary_entries")
