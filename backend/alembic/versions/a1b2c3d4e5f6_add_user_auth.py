"""Add user auth columns and migrate device_id to user_id."""

from typing import Optional, Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision = "a1b2c3d4e5f6"
down_revision: Optional[str] = "ce53e6acf63d"
branch_labels: Optional[Sequence[str]] = None
depends_on: Optional[Sequence[str]] = None


def _column_names(bind, table: str) -> set[str]:
    if not inspect(bind).has_table(table):
        return set()
    return {c["name"] for c in inspect(bind).get_columns(table)}


def upgrade() -> None:
    bind = op.get_bind()
    user_cols = _column_names(bind, "users")
    if "display_name" in user_cols:
        return

    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("display_name", sa.String(64), nullable=True))
        batch.add_column(sa.Column("avatar_url", sa.String(512), nullable=True))
        batch.add_column(sa.Column("last_login_at", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("oauth_provider", sa.String(32), nullable=True))
        batch.add_column(sa.Column("oauth_subject", sa.String(128), nullable=True))
        batch.add_column(sa.Column("legacy_device_id", sa.String(64), nullable=True))
        batch.create_index("ix_users_legacy_device_id", ["legacy_device_id"], unique=True)

    for table in ("user_word_progress", "scenario_attempts", "scenarios", "conversation_sessions", "learning_streaks"):
        if "user_id" in _column_names(bind, table):
            continue
        with op.batch_alter_table(table) as batch:
            batch.add_column(sa.Column("user_id", sa.Integer(), nullable=True))
            batch.create_foreign_key(f"fk_{table}_user_id", "users", ["user_id"], ["id"], ondelete="CASCADE")
            batch.create_index(f"ix_{table}_user_id", ["user_id"])

    if inspect(bind).has_table("user_word_progress"):
        with op.batch_alter_table("user_word_progress") as batch:
            batch.alter_column("device_id", existing_type=sa.String(64), nullable=True)
            batch.drop_constraint("uq_device_word", type_="unique")
            batch.create_unique_constraint("uq_user_word", ["user_id", "word_id"])

    if inspect(bind).has_table("learning_streaks"):
        with op.batch_alter_table("learning_streaks") as batch:
            batch.alter_column("device_id", existing_type=sa.String(64), nullable=True)
            batch.drop_constraint("uq_device_streak", type_="unique")
            batch.create_unique_constraint("uq_user_streak", ["user_id"])


def downgrade() -> None:
    raise NotImplementedError("Auth migration downgrade is not supported")
