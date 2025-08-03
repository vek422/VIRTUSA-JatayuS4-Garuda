"""Merge multiple heads

Revision ID: 0f3170e5d262
Revises: a0c5d9f03b3a, 20250727_priority_question_counts
Create Date: 2025-07-27 01:03:41.623489

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0f3170e5d262'
down_revision: Union[str, Sequence[str], None] = ('a0c5d9f03b3a', 'b7e1c2d3a4f5')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
