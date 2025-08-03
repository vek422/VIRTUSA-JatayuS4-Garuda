"""merge_heads

Revision ID: 8fc1cbb04725
Revises: 11160bb3c74f, b0994a0cb0a0
Create Date: 2025-07-29 09:06:24.221315

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8fc1cbb04725'
down_revision: Union[str, Sequence[str], None] = ('11160bb3c74f', 'b0994a0cb0a0')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
