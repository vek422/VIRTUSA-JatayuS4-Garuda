"""merge_timezone_and_logs_heads

Revision ID: 00c2f678c131
Revises: 20250728_create_logs_table, b0994a0cb0a0
Create Date: 2025-07-29 14:25:51.925609

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '00c2f678c131'
down_revision: Union[str, Sequence[str], None] = ('20250728_create_logs_table', 'b0994a0cb0a0')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
