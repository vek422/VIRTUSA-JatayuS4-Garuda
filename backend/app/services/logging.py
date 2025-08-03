from sqlalchemy import insert
from datetime import datetime, timezone
from app.models import Log
from app.db.database import AsyncSessionLocal
from typing import Optional
import asyncio


async def log_major_event(action: str, status: str, user: str, details: Optional[str] = None, entity: Optional[str] = None, source: Optional[str] = None):
    """
    Async log function for major events. Use 'await log_major_event(...)' in async code.
    Prints debug info before and after DB write, and raises on error.
    """
    print(
        f"[DEBUG] Attempting to log event: action={action}, status={status}, user={user}, entity={entity}, details={details}, source={source}")

    async with AsyncSessionLocal() as session:
        try:
            log_entry = {
                'timestamp': datetime.now(timezone.utc),
                'action': action,
                'status': status,
                'details': details,
                'user': user,
                'entity': entity,
                'source': source
            }
            result = await session.execute(insert(Log), [log_entry])
            await session.commit()
            print(f"[DEBUG] Log event committed to DB: {log_entry}")
            return result
        except Exception as e:
            await session.rollback()
            print(f"[ERROR] Logging error: {e}")
            import traceback
            traceback.print_exc()
            raise
