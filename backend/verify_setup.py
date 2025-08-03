"""
Quick verification script to check if the database setup is working
"""
import asyncio
from app.db.database import engine
from sqlalchemy import text


async def verify_setup():
    """Verify database connection and timezone setup"""
    print("Verifying database setup...")

    try:
        async with engine.begin() as conn:
            # Test connection
            result = await conn.execute(text("SELECT 1"))
            print("✅ Database connection successful")

            # Check if assessments table exists
            result = await conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'assessments'
                )
            """))

            table_exists = result.scalar()
            if table_exists:
                print("✅ Assessments table exists")

                # Check timezone columns
                result = await conn.execute(text("""
                    SELECT 
                        column_name, 
                        data_type,
                        CASE 
                            WHEN data_type = 'timestamp with time zone' THEN 'timezone-aware'
                            WHEN data_type = 'timestamp without time zone' THEN 'timezone-naive'
                            ELSE 'other'
                        END as timezone_status
                    FROM information_schema.columns 
                    WHERE table_name = 'assessments' 
                    AND column_name IN ('start_time', 'end_time', 'created_at', 'updated_at')
                    ORDER BY column_name
                """))

                columns = result.fetchall()
                print("\n📅 Timezone Column Status:")
                for col in columns:
                    status_icon = "✅" if col.timezone_status == "timezone-aware" else "❌"
                    print(
                        f"  {status_icon} {col.column_name}: {col.data_type} ({col.timezone_status})")

                # Check sample data
                result = await conn.execute(text("""
                    SELECT COUNT(*) FROM assessments
                """))
                count = result.scalar()
                print(f"\n📊 Total assessments in database: {count}")

            else:
                print("❌ Assessments table does not exist")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_setup())
