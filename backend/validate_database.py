#!/usr/bin/env python3
"""
Database Validation Script for Jatayu AI Quiz Backend

This script validates the database consistency and ensures all required
tables, columns, enums, and relationships are present and correctly configured.
"""

import os
import asyncio
import asyncpg
from urllib.parse import urlparse
from typing import Dict, List, Tuple, Any, Optional
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/jatayu_ai_quiz")


class DatabaseValidator:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.conn = None
        self.errors = []
        self.warnings = []
        self.success_count = 0

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
            self.success_count += 1
        except Exception as e:
            self.errors.append(f"Failed to connect to database: {e}")
            return False
        return True

    async def disconnect(self):
        """Disconnect from the database."""
        if self.conn:
            await self.conn.close()

    async def check_enum_types(self):
        """Check if required enum types exist."""
        print("\n📋 Checking Enum Types...")

        required_enums = {
            'teststatus': ['preparing', 'draft', 'scheduled', 'live', 'ended'],
            'assessmentstatus': ['started', 'in_progress', 'completed', 'abandoned', 'timed_out'],
            'userrole': ['candidate', 'recruiter']
        }

        for enum_name, expected_values in required_enums.items():
            try:
                # Check if enum exists
                result = await self.conn.fetchrow("""
                    SELECT 1 FROM pg_type WHERE typname = $1 AND typtype = 'e'
                """, enum_name)

                if not result:
                    self.errors.append(
                        f"Enum type '{enum_name}' does not exist")
                    continue

                # Check enum values
                enum_values = await self.conn.fetch("""
                    SELECT enumlabel FROM pg_enum 
                    WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = $1)
                    ORDER BY enumsortorder
                """, enum_name)

                actual_values = [row['enumlabel'] for row in enum_values]

                if set(actual_values) != set(expected_values):
                    missing = set(expected_values) - set(actual_values)
                    extra = set(actual_values) - set(expected_values)

                    if missing:
                        self.errors.append(
                            f"Enum '{enum_name}' missing values: {missing}")
                    if extra:
                        self.warnings.append(
                            f"Enum '{enum_name}' has extra values: {extra}")
                else:
                    print(
                        f"✓ Enum '{enum_name}' is valid with values: {actual_values}")
                    self.success_count += 1

            except Exception as e:
                self.errors.append(f"Error checking enum '{enum_name}': {e}")

    async def check_tables_and_columns(self):
        """Check if all required tables and columns exist."""
        print("\n📊 Checking Tables and Columns...")

        required_tables = {
            'users': {
                'user_id': 'integer',
                'name': 'character varying',
                'email': 'character varying',
                'role': 'userrole',
                'hashed_password': 'character varying',
                'created_at': 'timestamp with time zone',
                'updated_at': 'timestamp with time zone'
            },
            'tests': {
                'test_id': 'integer',
                'test_name': 'character varying',
                'job_description': 'text',
                'parsed_job_description': 'text',
                'skill_graph': 'text',
                'resume_score_threshold': 'integer',
                'max_shortlisted_candidates': 'integer',
                'auto_shortlist': 'boolean',
                'total_questions': 'integer',
                'time_limit_minutes': 'integer',
                'total_marks': 'integer',
                'status': 'teststatus',
                'is_published': 'boolean',
                'scheduled_at': 'timestamp with time zone',
                'application_deadline': 'timestamp with time zone',
                'assessment_deadline': 'timestamp with time zone',
                'created_by': 'integer',
                'updated_by': 'integer',
                'created_at': 'timestamp with time zone',
                'updated_at': 'timestamp with time zone',
                'high_priority_questions': 'integer',
                'medium_priority_questions': 'integer',
                'low_priority_questions': 'integer',
                'high_priority_nodes': 'integer',
                'medium_priority_nodes': 'integer',
                'low_priority_nodes': 'integer'
            },
            'candidate_applications': {
                'application_id': 'integer',
                'user_id': 'integer',
                'test_id': 'integer',
                'resume_link': 'character varying',
                'resume_text': 'text',
                'parsed_resume': 'text',
                'resume_score': 'integer',
                'skill_match_percentage': 'double precision',
                'experience_score': 'integer',
                'education_score': 'integer',
                'ai_reasoning': 'text',
                'is_shortlisted': 'boolean',
                'shortlist_reason': 'text',
                'screening_completed_at': 'timestamp without time zone',
                'screening_status': 'character varying',
                'notified_at': 'timestamp without time zone',
                'applied_at': 'timestamp without time zone',
                'updated_at': 'timestamp without time zone'
            },
            'assessments': {
                'assessment_id': 'integer',
                'application_id': 'integer',
                'user_id': 'integer',
                'test_id': 'integer',
                'status': 'character varying',
                'percentage_score': 'double precision',
                'start_time': 'timestamp with time zone',
                'end_time': 'timestamp with time zone',
                'created_at': 'timestamp with time zone',
                'updated_at': 'timestamp with time zone',
                'report': 'jsonb',
                'result': 'jsonb'
            },
            'logs': {
                'id': 'integer',
                'timestamp': 'timestamp with time zone',
                'action': 'character varying',
                'status': 'character varying',
                'details': 'text',
                'user': 'character varying',
                'entity': 'character varying',
                'source': 'character varying'
            },
            'revoked_tokens': {
                'id': 'integer',
                'jti': 'character varying',
                'revoked_at': 'timestamp without time zone'
            }
        }

        for table_name, columns in required_tables.items():
            try:
                # Check if table exists
                table_exists = await self.conn.fetchrow("""
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_name = $1 AND table_schema = 'public'
                """, table_name)

                if not table_exists:
                    self.errors.append(f"Table '{table_name}' does not exist")
                    continue

                print(f"✓ Table '{table_name}' exists")

                # Check columns
                existing_columns = await self.conn.fetch("""
                    SELECT column_name, data_type, udt_name
                    FROM information_schema.columns 
                    WHERE table_name = $1 AND table_schema = 'public'
                """, table_name)

                existing_col_dict = {
                    col['column_name']: col['udt_name'] if col['data_type'] == 'USER-DEFINED' else col['data_type']
                    for col in existing_columns
                }

                for col_name, expected_type in columns.items():
                    if col_name not in existing_col_dict:
                        self.errors.append(
                            f"Column '{col_name}' missing in table '{table_name}'")
                    elif existing_col_dict[col_name] != expected_type:
                        actual_type = existing_col_dict[col_name]
                        # Some flexibility for similar types
                        if not self._types_compatible(actual_type, expected_type):
                            self.warnings.append(
                                f"Column '{col_name}' in table '{table_name}' has type '{actual_type}' "
                                f"but expected '{expected_type}'"
                            )
                    else:
                        self.success_count += 1

            except Exception as e:
                self.errors.append(f"Error checking table '{table_name}': {e}")

    def _types_compatible(self, actual: str, expected: str) -> bool:
        """Check if two database types are compatible."""
        # Define compatible type mappings
        compatible_types = {
            ('character varying', 'varchar'),
            ('timestamp with time zone', 'timestamptz'),
            ('timestamp without time zone', 'timestamp'),
            ('double precision', 'float8'),
            ('jsonb', 'json'),
        }

        return (actual, expected) in compatible_types or (expected, actual) in compatible_types

    async def check_primary_keys(self):
        """Check if all tables have proper primary keys."""
        print("\n🔑 Checking Primary Keys...")

        expected_pks = {
            'users': 'user_id',
            'tests': 'test_id',
            'candidate_applications': 'application_id',
            'assessments': 'assessment_id',
            'logs': 'id',
            'revoked_tokens': 'id'
        }

        for table_name, expected_pk in expected_pks.items():
            try:
                pk_info = await self.conn.fetchrow("""
                    SELECT a.attname
                    FROM pg_index i
                    JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
                    WHERE i.indrelid = $1::regclass AND i.indisprimary
                """, table_name)

                if not pk_info:
                    self.errors.append(
                        f"Table '{table_name}' has no primary key")
                elif pk_info['attname'] != expected_pk:
                    self.errors.append(
                        f"Table '{table_name}' has primary key '{pk_info['attname']}' "
                        f"but expected '{expected_pk}'"
                    )
                else:
                    print(
                        f"✓ Table '{table_name}' has correct primary key: {expected_pk}")
                    self.success_count += 1

            except Exception as e:
                self.errors.append(
                    f"Error checking primary key for table '{table_name}': {e}")

    async def check_foreign_keys(self):
        """Check if all required foreign key relationships exist."""
        print("\n🔗 Checking Foreign Key Relationships...")

        expected_fks = [
            ('candidate_applications', 'user_id', 'users', 'user_id'),
            ('assessments', 'application_id',
             'candidate_applications', 'application_id'),
            ('assessments', 'user_id', 'users', 'user_id'),
            ('assessments', 'test_id', 'tests', 'test_id'),
            ('tests', 'created_by', 'users', 'user_id'),
            ('tests', 'updated_by', 'users', 'user_id'),
        ]

        for table, column, ref_table, ref_column in expected_fks:
            try:
                fk_exists = await self.conn.fetchrow("""
                    SELECT 1
                    FROM information_schema.referential_constraints rc
                    JOIN information_schema.key_column_usage kcu1 
                        ON rc.constraint_name = kcu1.constraint_name
                    JOIN information_schema.key_column_usage kcu2 
                        ON rc.unique_constraint_name = kcu2.constraint_name
                    WHERE kcu1.table_name = $1 
                        AND kcu1.column_name = $2
                        AND kcu2.table_name = $3
                        AND kcu2.column_name = $4
                """, table, column, ref_table, ref_column)

                if fk_exists:
                    print(
                        f"✓ Foreign key: {table}.{column} -> {ref_table}.{ref_column}")
                    self.success_count += 1
                else:
                    self.warnings.append(
                        f"Missing foreign key: {table}.{column} -> {ref_table}.{ref_column}"
                    )

            except Exception as e:
                self.errors.append(
                    f"Error checking foreign key {table}.{column}: {e}")

    async def check_indexes(self):
        """Check if important indexes exist."""
        print("\n📇 Checking Important Indexes...")

        expected_indexes = [
            ('users', 'email'),
            ('users', 'user_id'),
            ('tests', 'test_id'),
            ('candidate_applications', 'application_id'),
            ('assessments', 'assessment_id'),
        ]

        for table, column in expected_indexes:
            try:
                index_exists = await self.conn.fetchrow("""
                    SELECT 1
                    FROM pg_indexes
                    WHERE tablename = $1 
                        AND indexdef LIKE '%' || $2 || '%'
                """, table, column)

                if index_exists:
                    print(f"✓ Index exists on {table}.{column}")
                    self.success_count += 1
                else:
                    self.warnings.append(f"No index found on {table}.{column}")

            except Exception as e:
                self.errors.append(
                    f"Error checking index on {table}.{column}: {e}")

    async def check_constraints(self):
        """Check important constraints."""
        print("\n⚠️ Checking Constraints...")

        # Check unique constraints
        unique_constraints = [
            ('users', 'email'),
        ]

        for table, column in unique_constraints:
            try:
                constraint_exists = await self.conn.fetchrow("""
                    SELECT 1
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu 
                        ON tc.constraint_name = kcu.constraint_name
                    WHERE tc.table_name = $1 
                        AND kcu.column_name = $2
                        AND tc.constraint_type = 'UNIQUE'
                """, table, column)

                if constraint_exists:
                    print(f"✓ Unique constraint exists on {table}.{column}")
                    self.success_count += 1
                else:
                    self.errors.append(
                        f"Missing unique constraint on {table}.{column}")

            except Exception as e:
                self.errors.append(
                    f"Error checking unique constraint on {table}.{column}: {e}")

    async def check_data_integrity(self):
        """Perform basic data integrity checks."""
        print("\n🔍 Checking Data Integrity...")

        try:
            # Check for orphaned records
            orphaned_assessments = await self.conn.fetchval("""
                SELECT COUNT(*)
                FROM assessments a
                LEFT JOIN candidate_applications ca ON a.application_id = ca.application_id
                WHERE ca.application_id IS NULL
            """)

            if orphaned_assessments > 0:
                self.warnings.append(
                    f"Found {orphaned_assessments} orphaned assessments")
            else:
                print("✓ No orphaned assessments found")
                self.success_count += 1

            # Check for invalid enum values in assessments status
            invalid_status = await self.conn.fetchval("""
                SELECT COUNT(*)
                FROM assessments
                WHERE status NOT IN ('started', 'in_progress', 'completed', 'abandoned', 'timed_out')
            """)

            if invalid_status > 0:
                self.errors.append(
                    f"Found {invalid_status} assessments with invalid status values")
            else:
                print("✓ All assessment status values are valid")
                self.success_count += 1

        except Exception as e:
            self.errors.append(f"Error during data integrity check: {e}")

    async def validate_all(self):
        """Run all validation checks."""
        print("🚀 Starting Database Validation...")
        print(f"Database URL: {self.database_url}")
        print("=" * 60)

        if not await self.connect():
            return False

        try:
            await self.check_enum_types()
            await self.check_tables_and_columns()
            await self.check_primary_keys()
            await self.check_foreign_keys()
            await self.check_indexes()
            await self.check_constraints()
            await self.check_data_integrity()

        finally:
            await self.disconnect()

        # Print summary
        self.print_summary()

        return len(self.errors) == 0

    def print_summary(self):
        """Print validation summary."""
        print("\n" + "=" * 60)
        print("📊 VALIDATION SUMMARY")
        print("=" * 60)

        print(f"✅ Successful checks: {self.success_count}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        print(f"❌ Errors: {len(self.errors)}")

        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"   • {warning}")

        if self.errors:
            print("\n❌ ERRORS:")
            for error in self.errors:
                print(f"   • {error}")

        if len(self.errors) == 0:
            print(
                "\n🎉 Database validation PASSED! Your database is consistent and ready to use.")
        else:
            print("\n💥 Database validation FAILED! Please fix the errors above.")
            print("\n💡 Suggested actions:")
            print("   1. Run the database migrations: alembic upgrade head")
            print("   2. Create missing enum types: python create_enums.py")
            print("   3. Check your database schema and fix any structural issues")


async def main():
    """Main function to run database validation."""
    if len(sys.argv) > 1:
        database_url = sys.argv[1]
    else:
        database_url = DATABASE_URL

    if not database_url:
        print("❌ Error: DATABASE_URL not provided")
        print("Usage: python validate_database.py [DATABASE_URL]")
        print("Or set DATABASE_URL environment variable")
        sys.exit(1)

    validator = DatabaseValidator(database_url)
    success = await validator.validate_all()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
