"""
Add per-priority question count columns and remove question_distribution from tests table.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b7e1c2d3a4f5'
down_revision = 'a0c5d9f03b3a'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('tests', sa.Column('high_priority_questions', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('tests', sa.Column('medium_priority_questions', sa.Integer(), nullable=True, server_default='0'))
    op.add_column('tests', sa.Column('low_priority_questions', sa.Integer(), nullable=True, server_default='0'))
    op.drop_column('tests', 'question_distribution')

def downgrade():
    op.add_column('tests', sa.Column('question_distribution', sa.JSON(), nullable=True))
    op.drop_column('tests', 'high_priority_questions')
    op.drop_column('tests', 'medium_priority_questions')
    op.drop_column('tests', 'low_priority_questions')
