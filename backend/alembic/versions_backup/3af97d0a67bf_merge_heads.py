"""Merge heads

Revision ID: 3af97d0a67bf
Revises: 225930a07bcc, d109c2f6f846
Create Date: 2025-07-31 22:55:34.812111

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3af97d0a67bf'
down_revision: Union[str, Sequence[str], None] = ('225930a07bcc', 'd109c2f6f846')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
