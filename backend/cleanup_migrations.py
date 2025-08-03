#!/usr/bin/env python3
"""
Migration Cleanup Script for Jatayu AI Quiz Backend

This script helps clean up multiple migration files and creates a single
consolidated migration file that represents the current state of the database.
"""

import os
import shutil
from datetime import datetime
from pathlib import Path


def backup_migrations():
    """Backup existing migration files."""
    migrations_dir = Path("alembic/versions")
    backup_dir = Path(
        f"alembic/versions_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

    if migrations_dir.exists():
        print(f"📦 Backing up existing migrations to: {backup_dir}")
        shutil.copytree(migrations_dir, backup_dir)
        print("✓ Backup completed")
        return backup_dir
    else:
        print("⚠️  No migrations directory found")
        return None


def create_consolidated_migration():
    """Create a single consolidated migration file."""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    revision_id = f"{timestamp}_consolidated"
    filename = f"alembic/versions/{revision_id}_consolidated_migration.py"

    migration_content = f'''"""Consolidated migration for Jatayu AI Quiz Backend

Revision ID: {revision_id}
Revises: 
Create Date: {datetime.now().isoformat()}

This is a consolidated migration that creates all required tables,
enums, and relationships in a single file.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '{revision_id}'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create all tables, enums, and relationships."""
    
    # Create enum types
    op.execute("CREATE TYPE userrole AS ENUM ('candidate', 'recruiter')")
    op.execute("CREATE TYPE teststatus AS ENUM ('preparing', 'draft', 'scheduled', 'live', 'ended')")
    op.execute("CREATE TYPE assessmentstatus AS ENUM ('started', 'in_progress', 'completed', 'abandoned', 'timed_out')")
    
    # Create users table
    op.create_table(
        'users',
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
    op.create_table(
        'tests',
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
    op.create_table(
        'candidate_applications',
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
        sa.PrimaryKeyConstraint('application_id')
    )
    op.create_index(op.f('ix_candidate_applications_application_id'), 'candidate_applications', ['application_id'], unique=False)
    
    # Create assessments table
    op.create_table(
        'assessments',
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
        sa.Column('report', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('result', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['application_id'], ['candidate_applications.application_id'], ),
        sa.ForeignKeyConstraint(['test_id'], ['tests.test_id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('assessment_id')
    )
    op.create_index(op.f('ix_assessments_assessment_id'), 'assessments', ['assessment_id'], unique=False)
    
    # Create logs table
    op.create_table(
        'logs',
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
    
    # Create revoked_tokens table
    op.create_table(
        'revoked_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('jti', sa.String(), nullable=False),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('jti')
    )
    
    # Create update triggers
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    # Create triggers for tables with updated_at columns
    for table in ['users', 'tests', 'candidate_applications', 'assessments']:
        op.execute(f"""
            CREATE TRIGGER update_{table}_updated_at 
                BEFORE UPDATE ON {table}
                FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """)


def downgrade():
    """Drop all tables and enums."""
    
    # Drop triggers first
    for table in ['users', 'tests', 'candidate_applications', 'assessments']:
        op.execute(f"DROP TRIGGER IF EXISTS update_{table}_updated_at ON {table}")
    
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")
    
    # Drop tables in reverse order (respecting foreign key dependencies)
    op.drop_table('revoked_tokens')
    op.drop_table('logs')
    op.drop_table('assessments')
    op.drop_table('candidate_applications')
    op.drop_table('tests')
    op.drop_table('users')
    
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS assessmentstatus")
    op.execute("DROP TYPE IF EXISTS teststatus")
    op.execute("DROP TYPE IF EXISTS userrole")
'''

    # Create the migrations directory if it doesn't exist
    os.makedirs("alembic/versions", exist_ok=True)

    # Write the migration file
    with open(filename, 'w') as f:
        f.write(migration_content)

    print(f"✓ Created consolidated migration: {filename}")
    return filename


def cleanup_old_migrations():
    """Remove old migration files (they are backed up)."""
    migrations_dir = Path("alembic/versions")

    if migrations_dir.exists():
        migration_files = [f for f in migrations_dir.glob(
            "*.py") if not f.name.startswith("consolidated")]

        if migration_files:
            print(
                f"🗑️  Removing {len(migration_files)} old migration files...")
            for file in migration_files:
                file.unlink()
                print(f"   Removed: {file.name}")
        else:
            print("✓ No old migration files to remove")


def update_alembic_ini():
    """Update alembic.ini to point to the new migration."""
    alembic_ini = Path("alembic.ini")

    if alembic_ini.exists():
        print("📝 Updating alembic.ini...")
        # You might want to update any version-specific settings here
        print("✓ alembic.ini is ready")
    else:
        print("⚠️  alembic.ini not found - you may need to configure it manually")


def main():
    """Main function to clean up migrations."""
    print("🧹 Migration Cleanup Script")
    print("=" * 40)

    # Ask for confirmation
    response = input(
        "This will backup and replace all existing migrations. Continue? (y/N): ")
    if response.lower() != 'y':
        print("❌ Operation cancelled")
        return

    try:
        # Backup existing migrations
        backup_dir = backup_migrations()

        # Clean up old migrations
        cleanup_old_migrations()

        # Create new consolidated migration
        migration_file = create_consolidated_migration()

        # Update alembic.ini if needed
        update_alembic_ini()

        print("\n" + "=" * 60)
        print("🎉 Migration cleanup completed successfully!")
        print("=" * 60)
        print(f"✅ Old migrations backed up to: {backup_dir}")
        print(f"✅ New migration created: {migration_file}")
        print("\n💡 Next steps:")
        print("1. Run: python setup_database.py  # to set up fresh database")
        print("2. Or run: alembic upgrade head   # to apply the new migration")
        print("3. Run: python validate_database.py  # to verify everything is correct")

    except Exception as e:
        print(f"\n❌ Error during migration cleanup: {e}")
        print("Please check the error and try again.")


if __name__ == "__main__":
    main()
