#!/usr/bin/env python3
"""
Script to reset alembic version table for clean migration setup
"""
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

async def reset_alembic_version():
    """Reset the alembic_version table"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not found in environment variables")
        return
    
    engine = create_async_engine(database_url)
    
    try:
        async with engine.begin() as conn:
            # Drop the alembic_version table to start fresh
            await conn.execute(text("DROP TABLE IF EXISTS alembic_version CASCADE;"))
            print("✅ Dropped alembic_version table")
            
        print("✅ Alembic version table reset successfully")
        
    except Exception as e:
        print(f"❌ Error resetting alembic version: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(reset_alembic_version())