"""Prevent duplicate daily scenarios per user and kind."""

from alembic import op

revision = "e5f6a7b8c9d0"
down_revision = "d4e5f6a7b8c9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Keep the oldest row if a previous scheduler race already created duplicates.
    op.execute(
        """
        DELETE FROM scenarios
        WHERE is_daily = TRUE
          AND daily_date IS NOT NULL
          AND daily_kind IS NOT NULL
          AND id NOT IN (
              SELECT MIN(id)
              FROM scenarios
              WHERE is_daily = TRUE AND daily_date IS NOT NULL AND daily_kind IS NOT NULL
              GROUP BY user_id, daily_date, daily_kind
          )
        """
    )
    op.create_unique_constraint(
        "uq_scenarios_user_daily_kind",
        "scenarios",
        ["user_id", "daily_date", "daily_kind"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_scenarios_user_daily_kind", "scenarios", type_="unique")
