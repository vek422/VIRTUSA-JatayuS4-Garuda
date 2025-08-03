"""merge_multiple_heads_before_assessment_update

Revision ID: c60aa5269ee1
Revises: 225930a07bcc, d109c2f6f846
Create Date: 2025-08-02 20:11:32.144489

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c60aa5269ee1'
down_revision: Union[str, Sequence[str], None] = ('225930a07bcc', 'd109c2f6f846')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
