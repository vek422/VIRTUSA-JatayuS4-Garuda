"""Add H, M, L node count columns to test table"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '7c05a3cbc49b'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('tests', sa.Column('high_priority_nodes',
                  sa.Integer(), nullable=True, server_default='0'))
    op.add_column('tests', sa.Column('medium_priority_nodes',
                  sa.Integer(), nullable=True, server_default='0'))
    op.add_column('tests', sa.Column('low_priority_nodes',
                  sa.Integer(), nullable=True, server_default='0'))


def downgrade():
    op.drop_column('tests', 'high_priority_nodes')
    op.drop_column('tests', 'medium_priority_nodes')
    op.drop_column('tests', 'low_priority_nodes')
