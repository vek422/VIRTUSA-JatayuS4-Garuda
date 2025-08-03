"""add_result_column_to_assessments

Revision ID: 0d8cf57ec8b1
Revises: c60aa5269ee1
Create Date: 2025-08-02 20:13:25.036032

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0d8cf57ec8b1'
down_revision: Union[str, Sequence[str], None] = 'c60aa5269ee1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add result column to assessments table
    op.add_column('assessments', sa.Column('result', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove result column from assessments table
    op.drop_column('assessments', 'result')
