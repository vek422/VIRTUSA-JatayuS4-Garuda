#!/usr/bin/env python3
"""
Database Fix Script for Jatayu AI Quiz Backend

This script fixes common database issues identified by the validation script.
"""

import os
import asyncio
import asyncpg
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/jatayu_ai_quiz")


class DatabaseFixer:
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

    async def fix_unique_constraint_on_email(self):
        """Add unique constraint on users.email if it doesn't exist."""
        print("🔧 Fixing unique constraint on users.email...")

        try:
            # Check if unique constraint already exists
            constraint_exists = await self.conn.fetchrow("""
                SELECT 1
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu 
                    ON tc.constraint_name = kcu.constraint_name
                WHERE tc.table_name = 'users' 
                    AND kcu.column_name = 'email'
                    AND tc.constraint_type = 'UNIQUE'
            """)

            if constraint_exists:
                print("✓ Unique constraint on users.email already exists")
                return True

            # Check for duplicate emails first
            duplicates = await self.conn.fetch("""
                SELECT email, COUNT(*) as count
                FROM users 
                GROUP BY email 
                HAVING COUNT(*) > 1
            """)

            if duplicates:
                print(f"⚠️  Found {len(duplicates)} duplicate email(s):")
                for dup in duplicates:
                    print(
                        f"   Email: {dup['email']} (appears {dup['count']} times)")

                print("🔧 Cleaning up duplicate emails...")
                for dup in duplicates:
                    email = dup['email']
                    # Keep the first user, update others with unique emails
                    users_with_email = await self.conn.fetch("""
                        SELECT user_id FROM users WHERE email = $1 ORDER BY user_id
                    """, email)

                    # Skip first user
                    for i, user in enumerate(users_with_email[1:], 1):
                        new_email = f"{email}.duplicate_{i}"
                        await self.conn.execute("""
                            UPDATE users SET email = $1 WHERE user_id = $2
                        """, new_email, user['user_id'])
                        print(
                            f"   Updated user_id {user['user_id']}: {email} -> {new_email}")

            # Now add the unique constraint
            await self.conn.execute("""
                ALTER TABLE users ADD CONSTRAINT users_email_unique UNIQUE (email)
            """)
            print("✓ Added unique constraint on users.email")
            return True

        except Exception as e:
            print(f"❌ Error fixing unique constraint on users.email: {e}")
            return False

    async def verify_database_indexes(self):
        """Ensure all important indexes exist."""
        print("📇 Verifying important indexes...")

        indexes_to_create = [
            ("users", "email", "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)"),
            ("users", "user_id",
             "CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id)"),
            ("tests", "test_id",
             "CREATE INDEX IF NOT EXISTS idx_tests_test_id ON tests(test_id)"),
            ("tests", "created_by",
             "CREATE INDEX IF NOT EXISTS idx_tests_created_by ON tests(created_by)"),
            ("candidate_applications", "application_id",
             "CREATE INDEX IF NOT EXISTS idx_candidate_applications_application_id ON candidate_applications(application_id)"),
            ("candidate_applications", "user_id",
             "CREATE INDEX IF NOT EXISTS idx_candidate_applications_user_id ON candidate_applications(user_id)"),
            ("assessments", "assessment_id",
             "CREATE INDEX IF NOT EXISTS idx_assessments_assessment_id ON assessments(assessment_id)"),
            ("assessments", "application_id",
             "CREATE INDEX IF NOT EXISTS idx_assessments_application_id ON assessments(application_id)"),
            ("assessments", "user_id",
             "CREATE INDEX IF NOT EXISTS idx_assessments_user_id ON assessments(user_id)"),
            ("assessments", "test_id",
             "CREATE INDEX IF NOT EXISTS idx_assessments_test_id ON assessments(test_id)"),
            ("logs", "timestamp",
             "CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp)"),
            ("logs", "action", "CREATE INDEX IF NOT EXISTS idx_logs_action ON logs(action)"),
            ("revoked_tokens", "jti",
             "CREATE INDEX IF NOT EXISTS idx_revoked_tokens_jti ON revoked_tokens(jti)"),
        ]

        for table, column, sql in indexes_to_create:
            try:
                await self.conn.execute(sql)
                print(f"✓ Index verified on {table}.{column}")
            except Exception as e:
                print(f"⚠️  Could not create index on {table}.{column}: {e}")

    async def update_enum_values(self):
        """Update enum types to match current database state."""
        print("📋 Updating enum type definitions...")

        # Check current teststatus enum values
        current_values = await self.conn.fetch("""
            SELECT enumlabel FROM pg_enum 
            WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'teststatus')
            ORDER BY enumsortorder
        """)

        current_teststatus_values = [row['enumlabel']
                                     for row in current_values]
        expected_values = ['preparing', 'draft', 'scheduled', 'live', 'ended']

        # Add any missing expected values
        for value in expected_values:
            if value not in current_teststatus_values:
                try:
                    await self.conn.execute(f"ALTER TYPE teststatus ADD VALUE '{value}'")
                    print(f"✓ Added '{value}' to teststatus enum")
                except Exception as e:
                    print(
                        f"⚠️  Could not add '{value}' to teststatus enum: {e}")

        print(f"✓ Current teststatus values: {current_teststatus_values}")

    async def fix_all_issues(self):
        """Fix all identified database issues."""
        print("🚀 Starting Database Fixes...")
        print(f"Database URL: {self.database_url}")
        print("=" * 60)

        if not await self.connect():
            return False

        try:
            success = True

            # Fix unique constraint on email
            if not await self.fix_unique_constraint_on_email():
                success = False

            # Verify indexes
            await self.verify_database_indexes()

            # Update enum values
            await self.update_enum_values()

            if success:
                print("\n" + "=" * 60)
                print("🎉 Database fixes completed successfully!")
                print("✅ Your database should now pass validation")
                print("=" * 60)
                print("\n💡 Next step: Run validation again:")
                print("   python validate_database.py")
            else:
                print("\n❌ Some fixes failed. Please review the errors above.")

            return success

        except Exception as e:
            print(f"\n❌ Database fix failed: {e}")
            return False
        finally:
            await self.disconnect()


async def main():
    """Main function to run database fixes."""
    import sys

    if len(sys.argv) > 1:
        database_url = sys.argv[1]
    else:
        database_url = DATABASE_URL

    if not database_url:
        print("❌ Error: DATABASE_URL not provided")
        print("Usage: python fix_database.py [DATABASE_URL]")
        print("Or set DATABASE_URL environment variable")
        sys.exit(1)

    fixer = DatabaseFixer(database_url)
    success = await fixer.fix_all_issues()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
