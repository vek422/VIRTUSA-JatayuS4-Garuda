#!/usr/bin/env python3
"""
Database Setup Script for Jatayu AI Quiz Backend

This script creates a single consolidated migration that ensures the database
has all required tables, enums, and relationships in the correct state.
"""

import os
import asyncio
import asyncpg
from urllib.parse import urlparse
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/jatayu_ai_quiz")


class DatabaseSetup:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.conn = None

    async def connect(self):
        """Connect to the database."""
        try:
            parsed_url = urlparse(self.database_url)
            # Handle both postgresql:// and postgresql+asyncpg:// URLs
            if parsed_url.scheme == 'postgresql+asyncpg':
                # Remove the +asyncpg part for asyncpg connection
                clean_url = self.database_url.replace(
                    'postgresql+asyncpg://', 'postgresql://')
                parsed_url = urlparse(clean_url)

            self.conn = await asyncpg.connect(
                host=parsed_url.hostname,
                port=parsed_url.port or 5432,
                user=parsed_url.username,
                password=parsed_url.password,
                database=parsed_url.path[1:] if parsed_url.path else 'postgres'
            )
            print("✓ Database connection established")
        except Exception as e:
            print(f"❌ Failed to connect to database: {e}")
            return False
        return True

    async def disconnect(self):
        """Disconnect from the database."""
        if self.conn:
            await self.conn.close()

    async def create_enum_types(self):
        """Create all required enum types."""
        print("📋 Creating enum types...")

        enums = [
            ("userrole", ["candidate", "recruiter"]),
            ("teststatus", ["preparing", "draft",
             "scheduled", "live", "ended"]),
            ("assessmentstatus", ["started", "in_progress",
             "completed", "abandoned", "timed_out"])
        ]

        for enum_name, values in enums:
            try:
                values_str = "', '".join(values)
                await self.conn.execute(f"""
                    DO $$ BEGIN
                        CREATE TYPE {enum_name} AS ENUM ('{values_str}');
                        RAISE NOTICE 'Created enum type: {enum_name}';
                    EXCEPTION
                        WHEN duplicate_object THEN 
                            RAISE NOTICE 'Enum type {enum_name} already exists';
                    END $$;
                """)
                print(f"✓ Enum '{enum_name}' created/verified")
            except Exception as e:
                print(f"❌ Error creating enum '{enum_name}': {e}")
                raise

    async def create_tables(self):
        """Create all required tables."""
        print("📊 Creating tables...")

        # Create tables in order (respecting foreign key dependencies)
        tables_sql = [
            # Users table
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                role userrole NOT NULL,
                hashed_password VARCHAR NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
            """,

            # Tests table
            """
            CREATE TABLE IF NOT EXISTS tests (
                test_id SERIAL PRIMARY KEY,
                test_name VARCHAR(200) NOT NULL,
                job_description TEXT,
                parsed_job_description TEXT,
                skill_graph TEXT,
                resume_score_threshold INTEGER,
                max_shortlisted_candidates INTEGER,
                auto_shortlist BOOLEAN DEFAULT FALSE,
                total_questions INTEGER,
                time_limit_minutes INTEGER,
                total_marks INTEGER,
                status teststatus DEFAULT 'draft' NOT NULL,
                is_published BOOLEAN DEFAULT FALSE,
                scheduled_at TIMESTAMP WITH TIME ZONE,
                application_deadline TIMESTAMP WITH TIME ZONE,
                assessment_deadline TIMESTAMP WITH TIME ZONE,
                created_by INTEGER NOT NULL REFERENCES users(user_id),
                updated_by INTEGER REFERENCES users(user_id),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                high_priority_questions INTEGER DEFAULT 0,
                medium_priority_questions INTEGER DEFAULT 0,
                low_priority_questions INTEGER DEFAULT 0,
                high_priority_nodes INTEGER DEFAULT 0,
                medium_priority_nodes INTEGER DEFAULT 0,
                low_priority_nodes INTEGER DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_tests_test_id ON tests(test_id);
            CREATE INDEX IF NOT EXISTS idx_tests_created_by ON tests(created_by);
            """,

            # Candidate Applications table
            """
            CREATE TABLE IF NOT EXISTS candidate_applications (
                application_id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(user_id),
                test_id INTEGER NOT NULL,
                resume_link VARCHAR NOT NULL,
                resume_text TEXT,
                parsed_resume TEXT,
                resume_score INTEGER,
                skill_match_percentage DOUBLE PRECISION,
                experience_score INTEGER,
                education_score INTEGER,
                ai_reasoning TEXT,
                is_shortlisted BOOLEAN DEFAULT FALSE,
                shortlist_reason TEXT,
                screening_completed_at TIMESTAMP,
                screening_status VARCHAR(20) DEFAULT 'pending' NOT NULL,
                notified_at TIMESTAMP,
                applied_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS idx_candidate_applications_application_id ON candidate_applications(application_id);
            CREATE INDEX IF NOT EXISTS idx_candidate_applications_user_id ON candidate_applications(user_id);
            """,

            # Assessments table
            """
            CREATE TABLE IF NOT EXISTS assessments (
                assessment_id SERIAL PRIMARY KEY,
                application_id INTEGER NOT NULL REFERENCES candidate_applications(application_id),
                user_id INTEGER NOT NULL REFERENCES users(user_id),
                test_id INTEGER NOT NULL REFERENCES tests(test_id),
                status VARCHAR(20) DEFAULT 'in_progress',
                percentage_score DOUBLE PRECISION,
                start_time TIMESTAMP WITH TIME ZONE,
                end_time TIMESTAMP WITH TIME ZONE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                report JSONB,
                result JSONB
            );
            CREATE INDEX IF NOT EXISTS idx_assessments_assessment_id ON assessments(assessment_id);
            CREATE INDEX IF NOT EXISTS idx_assessments_application_id ON assessments(application_id);
            CREATE INDEX IF NOT EXISTS idx_assessments_user_id ON assessments(user_id);
            CREATE INDEX IF NOT EXISTS idx_assessments_test_id ON assessments(test_id);
            """,

            # Logs table
            """
            CREATE TABLE IF NOT EXISTS logs (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                action VARCHAR(255) NOT NULL,
                status VARCHAR(50) NOT NULL,
                details TEXT,
                "user" VARCHAR(255),
                entity VARCHAR(255),
                source VARCHAR(255)
            );
            CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp);
            CREATE INDEX IF NOT EXISTS idx_logs_action ON logs(action);
            """,

            # Revoked Tokens table
            """
            CREATE TABLE IF NOT EXISTS revoked_tokens (
                id SERIAL PRIMARY KEY,
                jti VARCHAR NOT NULL UNIQUE,
                revoked_at TIMESTAMP DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS idx_revoked_tokens_jti ON revoked_tokens(jti);
            """
        ]

        for i, sql in enumerate(tables_sql, 1):
            try:
                await self.conn.execute(sql)
                table_name = self._extract_table_name(sql)
                print(f"✓ Table '{table_name}' created/verified")
            except Exception as e:
                print(f"❌ Error creating table {i}: {e}")
                raise

    def _extract_table_name(self, sql: str) -> str:
        """Extract table name from CREATE TABLE statement."""
        lines = sql.strip().split('\n')
        for line in lines:
            if 'CREATE TABLE' in line and 'IF NOT EXISTS' in line:
                parts = line.split()
                idx = parts.index('EXISTS') + 1
                return parts[idx] if idx < len(parts) else 'unknown'
        return 'unknown'

    async def create_triggers(self):
        """Create triggers for auto-updating timestamps."""
        print("⚡ Creating triggers...")

        # Function for updating timestamps
        await self.conn.execute("""
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = NOW();
                RETURN NEW;
            END;
            $$ language 'plpgsql';
        """)

        # Triggers for tables with updated_at columns
        tables_with_updated_at = ['users', 'tests',
                                  'candidate_applications', 'assessments']

        for table in tables_with_updated_at:
            try:
                await self.conn.execute(f"""
                    DROP TRIGGER IF EXISTS update_{table}_updated_at ON {table};
                    CREATE TRIGGER update_{table}_updated_at 
                        BEFORE UPDATE ON {table}
                        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
                """)
                print(f"✓ Trigger for '{table}' created")
            except Exception as e:
                print(f"❌ Error creating trigger for '{table}': {e}")

    async def create_alembic_version_table(self):
        """Create alembic version table if it doesn't exist."""
        print("📝 Setting up Alembic version tracking...")

        try:
            await self.conn.execute("""
                CREATE TABLE IF NOT EXISTS alembic_version (
                    version_num VARCHAR(32) NOT NULL,
                    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
                );
            """)

            # Check if there's a version already
            current_version = await self.conn.fetchval(
                "SELECT version_num FROM alembic_version LIMIT 1"
            )

            if not current_version:
                # Insert a consolidated version number
                consolidated_version = datetime.now().strftime(
                    "%Y%m%d_%H%M%S") + "_consolidated_migration"
                await self.conn.execute(
                    "INSERT INTO alembic_version (version_num) VALUES ($1)",
                    consolidated_version
                )
                print(f"✓ Set Alembic version to: {consolidated_version}")
            else:
                print(f"✓ Alembic version already set: {current_version}")

        except Exception as e:
            print(f"❌ Error setting up Alembic version: {e}")

    async def verify_setup(self):
        """Verify that everything was set up correctly."""
        print("🔍 Verifying database setup...")

        # Check tables
        tables = await self.conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)

        expected_tables = {
            'users', 'tests', 'candidate_applications',
            'assessments', 'logs', 'revoked_tokens', 'alembic_version'
        }

        actual_tables = {row['table_name'] for row in tables}
        missing_tables = expected_tables - actual_tables

        if missing_tables:
            print(f"❌ Missing tables: {missing_tables}")
            return False

        print(f"✓ All required tables present: {sorted(actual_tables)}")

        # Check enums
        enums = await self.conn.fetch("""
            SELECT typname FROM pg_type WHERE typtype = 'e' ORDER BY typname
        """)

        expected_enums = {'userrole', 'teststatus', 'assessmentstatus'}
        actual_enums = {row['typname'] for row in enums}
        missing_enums = expected_enums - actual_enums

        if missing_enums:
            print(f"❌ Missing enums: {missing_enums}")
            return False

        print(f"✓ All required enums present: {sorted(actual_enums)}")

        # Check foreign keys
        fks = await self.conn.fetch("""
            SELECT 
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
            ORDER BY tc.table_name, kcu.column_name
        """)

        print(f"✓ Foreign key relationships: {len(fks)} found")
        for fk in fks:
            print(
                f"   {fk['table_name']}.{fk['column_name']} -> {fk['foreign_table_name']}.{fk['foreign_column_name']}")

        return True

    async def setup_database(self):
        """Run the complete database setup."""
        print("🚀 Starting Database Setup...")
        print(f"Database URL: {self.database_url}")
        print("=" * 60)

        if not await self.connect():
            return False

        try:
            await self.create_enum_types()
            await self.create_tables()
            await self.create_triggers()
            await self.create_alembic_version_table()

            if await self.verify_setup():
                print("\n" + "=" * 60)
                print("🎉 Database setup completed successfully!")
                print("✅ Your database is now ready for the Jatayu AI Quiz Backend")
                print("=" * 60)
                return True
            else:
                print("\n❌ Database setup verification failed!")
                return False

        except Exception as e:
            print(f"\n❌ Database setup failed: {e}")
            return False
        finally:
            await self.disconnect()


async def main():
    """Main function to run database setup."""
    import sys

    if len(sys.argv) > 1:
        database_url = sys.argv[1]
    else:
        database_url = DATABASE_URL

    if not database_url:
        print("❌ Error: DATABASE_URL not provided")
        print("Usage: python setup_database.py [DATABASE_URL]")
        print("Or set DATABASE_URL environment variable")
        sys.exit(1)

    setup = DatabaseSetup(database_url)
    success = await setup.setup_database()

    if success:
        print("\n💡 Next steps:")
        print("1. Run: python validate_database.py  # to verify everything is correct")
        print("2. Start your application!")
    else:
        print("\n💥 Setup failed. Please check the errors above and try again.")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
