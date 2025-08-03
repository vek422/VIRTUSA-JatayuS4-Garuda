"""Initial database schema with all tables

Revision ID: 001_initial_schema
Revises: 
Create Date: 2025-08-03 18:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables from scratch."""
    
    # Create enum types
    op.execute("CREATE TYPE userrole AS ENUM ('candidate', 'recruiter')")
    op.execute("CREATE TYPE teststatus AS ENUM ('preparing', 'draft', 'scheduled', 'live', 'ended')")
    
    # Create users table
    op.create_table('users',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('role', postgresql.ENUM('candidate', 'recruiter', name='userrole'), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('user_id')
    )
    op.create_index(op.f('ix_users_user_id'), 'users', ['user_id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Create tests table
    op.create_table('tests',
        sa.Column('test_id', sa.Integer(), nullable=False),
        sa.Column('test_name', sa.String(length=200), nullable=False),
        sa.Column('job_description', sa.Text(), nullable=True),
        sa.Column('parsed_job_description', sa.Text(), nullable=True),
        sa.Column('skill_graph', sa.Text(), nullable=True),
        sa.Column('resume_score_threshold', sa.Integer(), nullable=True),
        sa.Column('max_shortlisted_candidates', sa.Integer(), nullable=True),
        sa.Column('auto_shortlist', sa.Boolean(), nullable=True, default=False),
        sa.Column('total_questions', sa.Integer(), nullable=True),
        sa.Column('time_limit_minutes', sa.Integer(), nullable=True),
        sa.Column('total_marks', sa.Integer(), nullable=True),
        sa.Column('status', postgresql.ENUM('preparing', 'draft', 'scheduled', 'live', 'ended', name='teststatus'), nullable=False, default='draft'),
        sa.Column('is_published', sa.Boolean(), nullable=True, default=False),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('application_deadline', sa.DateTime(timezone=True), nullable=True),
        sa.Column('assessment_deadline', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('high_priority_questions', sa.Integer(), nullable=True, default=0),
        sa.Column('medium_priority_questions', sa.Integer(), nullable=True, default=0),
        sa.Column('low_priority_questions', sa.Integer(), nullable=True, default=0),
        sa.Column('high_priority_nodes', sa.Integer(), nullable=True, default=0),
        sa.Column('medium_priority_nodes', sa.Integer(), nullable=True, default=0),
        sa.Column('low_priority_nodes', sa.Integer(), nullable=True, default=0),
        sa.ForeignKeyConstraint(['created_by'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('test_id')
    )
    op.create_index(op.f('ix_tests_test_id'), 'tests', ['test_id'], unique=False)

    # Create candidate_applications table
    op.create_table('candidate_applications',
        sa.Column('application_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('test_id', sa.Integer(), nullable=False),
        sa.Column('resume_link', sa.String(), nullable=False),
        sa.Column('resume_text', sa.Text(), nullable=True),
        sa.Column('parsed_resume', sa.Text(), nullable=True),
        sa.Column('resume_score', sa.Integer(), nullable=True),
        sa.Column('skill_match_percentage', sa.Float(), nullable=True),
        sa.Column('experience_score', sa.Integer(), nullable=True),
        sa.Column('education_score', sa.Integer(), nullable=True),
        sa.Column('ai_reasoning', sa.Text(), nullable=True),
        sa.Column('is_shortlisted', sa.Boolean(), nullable=True, default=False),
        sa.Column('shortlist_reason', sa.Text(), nullable=True),
        sa.Column('screening_completed_at', sa.DateTime(), nullable=True),
        sa.Column('screening_status', sa.String(length=20), nullable=False, default='pending'),
        sa.Column('notified_at', sa.DateTime(), nullable=True),
        sa.Column('applied_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['test_id'], ['tests.test_id'], ),
        sa.PrimaryKeyConstraint('application_id'),
        sa.UniqueConstraint('user_id', 'test_id', name='unique_user_test_application')
    )
    op.create_index(op.f('ix_candidate_applications_application_id'), 'candidate_applications', ['application_id'], unique=False)

    # Create assessments table
    op.create_table('assessments',
        sa.Column('assessment_id', sa.Integer(), nullable=False),
        sa.Column('application_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('test_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True, default='in_progress'),
        sa.Column('percentage_score', sa.Float(), nullable=True),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('report', sa.JSON(), nullable=True),
        sa.Column('result', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['application_id'], ['candidate_applications.application_id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ),
        sa.ForeignKeyConstraint(['test_id'], ['tests.test_id'], ),
        sa.PrimaryKeyConstraint('assessment_id')
    )
    op.create_index(op.f('ix_assessments_assessment_id'), 'assessments', ['assessment_id'], unique=False)

    # Create revoked_tokens table
    op.create_table('revoked_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('jti', sa.String(), nullable=False),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_revoked_tokens_id'), 'revoked_tokens', ['id'], unique=False)
    op.create_index(op.f('ix_revoked_tokens_jti'), 'revoked_tokens', ['jti'], unique=True)

    # Create logs table
    op.create_table('logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('action', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('user', sa.String(length=255), nullable=True),
        sa.Column('entity', sa.String(length=255), nullable=True),
        sa.Column('source', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('logs')
    op.drop_index(op.f('ix_revoked_tokens_jti'), table_name='revoked_tokens')
    op.drop_index(op.f('ix_revoked_tokens_id'), table_name='revoked_tokens')
    op.drop_table('revoked_tokens')
    op.drop_index(op.f('ix_assessments_assessment_id'), table_name='assessments')
    op.drop_table('assessments')
    op.drop_index(op.f('ix_candidate_applications_application_id'), table_name='candidate_applications')
    op.drop_table('candidate_applications')
    op.drop_index(op.f('ix_tests_test_id'), table_name='tests')
    op.drop_table('tests')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_user_id'), table_name='users')
    op.drop_table('users')
    
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS teststatus")
    op.execute("DROP TYPE IF EXISTS userrole")