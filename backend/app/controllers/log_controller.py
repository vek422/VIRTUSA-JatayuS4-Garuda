from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.log import Log
from app.schemas.log import LogSchema
from typing import List
from app.db.database import get_db
from fastapi import HTTPException
from app.services.auth.auth_service import get_current_user
from app.models.user import UserRole
router = APIRouter()
from app.models.user import User

@router.get("/", response_model=List[LogSchema])
async def get_logs(skip: int = 0, limit: int = 50, db: AsyncSession = Depends(get_db), current_user = Depends(get_current_user)):
    if not current_user or current_user.role != UserRole.recruiter:
        raise HTTPException(status_code=403, detail="Unauthorized")
    stmt = (
        select(Log)
        .where(Log.user == str(current_user.user_id))
        .order_by(Log.timestamp.desc())
    )
    result = await db.execute(stmt)
    logs = result.scalars().all()

    for log in logs:
        try:
            user_id_int = int(log.user)
        except (TypeError, ValueError):
            user_id_int = None
        if user_id_int is not None:
            user_stmt = select(User).where(User.user_id == user_id_int)
            user_result = await db.execute(user_stmt)
            user_obj = user_result.scalar_one_or_none()
            if user_obj:
                log.user = user_obj.name

    return logs