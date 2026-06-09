"""json_columns

JSONField TypeDecorator uses Text storage — no DDL change required.
Existing TEXT JSON values remain compatible via json_helpers.parse_json_field.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ce53e6acf63d'
down_revision: Union[str, None] = '46e63fc298a0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
