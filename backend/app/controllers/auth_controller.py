from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from app.services.auth.AuthInterface import IAuthService
from app.services.auth.auth_service import AuthService, get_current_user
import app.schemas.user_schema as user_schema
from app.db.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import UserRole

router = APIRouter()
auth_service: IAuthService = AuthService()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

@router.post("/login")
async def login(data: user_schema.UserLogin, db: AsyncSession = Depends(get_db)):
    try:
        return await auth_service.login(data.email, data.password, db)
    except HTTPException as e:
        raise e

@router.post("/register")
async def register(data: user_schema.UserRegister, db: AsyncSession = Depends(get_db)):
    try:
        return {"user_id": await auth_service.signup(data.dict(), db)}
    except HTTPException as e:
        raise e

# User profile endpoints
@router.get("/me")
async def read_current_user(current_user=Depends(get_current_user)):
    """Get current user information"""
    return {
        "user_id": current_user.user_id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role.value if hasattr(current_user.role, 'value') else current_user.role
    }

@router.get("/profile")
async def get_user_profile(current_user=Depends(get_current_user)):
    """Get detailed user profile - alias for /me"""
    return {
        "user_id": current_user.user_id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role.value if hasattr(current_user.role, 'value') else current_user.role,
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at
    }

@router.get("/verify-token")
async def verify_token(current_user=Depends(get_current_user)):
    """Verify if the current token is valid"""
    return {
        "valid": True,
        "user_id": current_user.user_id,
        "email": current_user.email,
        "role": current_user.role.value if hasattr(current_user.role, 'value') else current_user.role
    }

def recruiter_required(current_user=Depends(get_current_user)):
    if current_user.role != UserRole.recruiter:
        raise HTTPException(status_code=403, detail="Recruiter access required")
    return current_user

def candidate_required(current_user=Depends(get_current_user)):
    if current_user.role != UserRole.candidate:
        raise HTTPException(status_code=403, detail="Candidate access required")
    return current_user

# Example protected endpoint for recruiters
@router.get("/recruiter-only")
async def recruiter_only_endpoint(current_user=Depends(recruiter_required)):
    return {"message": f"Hello Recruiter {current_user.name}"}

# Example protected endpoint for candidates
@router.get("/candidate-only")
async def candidate_only_endpoint(current_user=Depends(candidate_required)):
    return {"message": f"Hello Candidate {current_user.name}"}

@router.post("/logout")
async def logout(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    return await auth_service.logout(token, db)
