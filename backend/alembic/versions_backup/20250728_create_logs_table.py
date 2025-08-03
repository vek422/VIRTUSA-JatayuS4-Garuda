"""
Revision ID: 20250728_create_logs_table
Revises: 
Create Date: 2025-07-28
"""
revision = '20250728_create_logs_table'
down_revision = None  # or set to previous revision id if needed
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'logs',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('timestamp', sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column('action', sa.String(255), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('details', sa.Text, nullable=True),
        sa.Column('user', sa.String(255), nullable=True),
        sa.Column('entity', sa.String(255), nullable=True),
        sa.Column('source', sa.String(255), nullable=True)
    )

def downgrade():
    op.drop_table('logs')
