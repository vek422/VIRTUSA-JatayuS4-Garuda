"""merge_heads_for_clean_setup

Revision ID: efd66b2fa31c
Revises: 0d8cf57ec8b1, 3af97d0a67bf
Create Date: 2025-08-03 14:41:46.664343

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'efd66b2fa31c'
down_revision: Union[str, Sequence[str], None] = ('0d8cf57ec8b1', '3af97d0a67bf')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
