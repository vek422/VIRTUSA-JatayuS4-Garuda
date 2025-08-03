"""create_enum_types

Revision ID: d109c2f6f846
Revises: 8fc1cbb04725
Create Date: 2025-07-29 09:07:13.769391

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd109c2f6f846'
down_revision: Union[str, Sequence[str], None] = '8fc1cbb04725'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create enum types
    test_status_enum = sa.Enum('preparing', 'draft', 'scheduled', 'live', 'ended', name='teststatus', create_type=True)
    test_status_enum.create(op.get_bind(), checkfirst=True)
    
    assessment_status_enum = sa.Enum('started', 'in_progress', 'completed', 'abandoned', 'timed_out', name='assessmentstatus', create_type=True)
    assessment_status_enum.create(op.get_bind(), checkfirst=True)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop enum types
    op.execute('DROP TYPE IF EXISTS teststatus CASCADE')
    op.execute('DROP TYPE IF EXISTS assessmentstatus CASCADE')
