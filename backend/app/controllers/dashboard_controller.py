from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.services.auth.auth_service import get_current_user
from app.models.user import UserRole
from app.services.dashboard_service import get_dashboard_summary

router = APIRouter()

@router.get("/dashboard/summary")
async def dashboard_summary(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    if current_user.role != UserRole.recruiter:
        raise HTTPException(status_code=403, detail="Only recruiters can access this endpoint.")
    return await get_dashboard_summary(db, current_user.user_id)
