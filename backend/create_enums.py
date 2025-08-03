#!/usr/bin/env python3
"""
Script to create PostgreSQL enum types before running migrations.
"""
import asyncio
import asyncpg
import os
from urllib.parse import urlparse

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@postgres:5432/jatayu_ai_quiz")

async def create_enum_types():
    """Create the required enum types in PostgreSQL."""
    print("Creating enum types...")
    
    # Parse the database URL
    parsed_url = urlparse(DATABASE_URL)
    
    # Connect to PostgreSQL
    conn = await asyncpg.connect(
        host=parsed_url.hostname,
        port=parsed_url.port,
        user=parsed_url.username,
        password=parsed_url.password,
        database=parsed_url.path[1:]  # Remove leading slash
    )
    
    try:
        # Create teststatus enum
        await conn.execute("""
            DO $$ BEGIN
                CREATE TYPE teststatus AS ENUM ('preparing', 'draft', 'scheduled', 'live', 'ended');
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """)
        print("✓ Created teststatus enum")
        
        # Create assessmentstatus enum
        await conn.execute("""
            DO $$ BEGIN
                CREATE TYPE assessmentstatus AS ENUM ('started', 'in_progress', 'completed', 'abandoned', 'timed_out');
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """)
        print("✓ Created assessmentstatus enum")
        
    except Exception as e:
        print(f"Error creating enum types: {e}")
        raise
    finally:
        await conn.close()
    
    print("Enum types created successfully!")

if __name__ == "__main__":
    asyncio.run(create_enum_types())
