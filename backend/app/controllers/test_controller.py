from pydantic import BaseModel


from fastapi import Body
import json
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.services.test_service import get_enhanced_test_service
from app.services.auth.auth_service import get_current_user
from app.schemas.test_schema import TestCreate, TestUpdate, TestResponse, TestSummary
from app.db.database import get_db
from app.models.user import User, UserRole
from app.schemas.test_schema import TestSchedule

from app.repositories.test_repo import TestRepository

router = APIRouter()
test_service = get_enhanced_test_service()
class QuestionCountUpdate(BaseModel):
    high_priority_questions: int
    medium_priority_questions: int
    low_priority_questions: int
    total_questions: int
    time_limit_minutes: int

def recruiter_required(current_user: User = Depends(get_current_user)):
    """Dependency to ensure only recruiters can access certain endpoints"""
    if current_user.role != UserRole.recruiter:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Recruiter access required"
        )
    return current_user





# New endpoint for updating per-priority question counts and total
@router.put("/{test_id}/update-question-counts")
async def update_question_counts(
    test_id: int,
    data: QuestionCountUpdate,
    current_user: User = Depends(recruiter_required),
    db: AsyncSession = Depends(get_db)
):
    """Update per-priority question counts, total_questions, and time_limit_minutes for a test."""
    return await test_service.update_question_counts(
        test_id=test_id,
        data=data,
        user_id=current_user.user_id,
        db=db
    )




@router.post("/", response_model=TestResponse)
async def create_test(
    test_data: TestCreate,
    current_user: User = Depends(recruiter_required),  # Only recruiters can create tests
    db: AsyncSession = Depends(get_db)
):
    """Create a new test with AI processing (recruiters only)"""
    return await test_service.create_test_with_ai(
        test_data=test_data,
        created_by=current_user.user_id,
        db=db
    )

@router.get("/", response_model=List[TestSummary])
async def get_all_tests(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(recruiter_required),  # Recruiters only
    db: AsyncSession = Depends(get_db)
):
    """Get tests created by the current user only (owner only)"""
    return await test_service.get_tests_by_creator(
        creator_id=current_user.user_id,
        db=db,
        skip=skip,
        limit=limit
    )


@router.get("/{test_id}", response_model=TestResponse)
async def get_test_by_id(
    test_id: int,
    current_user: User = Depends(recruiter_required),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific test by ID (owner only)"""
    test = await test_service.get_test_by_id(test_id=test_id, db=db)
    
    # Check if user is the owner
    if test.created_by != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own tests"
        )
    
    return test

@router.put("/{test_id}", response_model=TestResponse)
async def update_test(
    test_id: int,
    test_data: TestUpdate,
    current_user: User = Depends(recruiter_required),
    db: AsyncSession = Depends(get_db)
):
    """Update job description, resume_score_threshold, max_shortlisted_candidates, and auto_shortlist for a test (owner only, only in draft). Skill graph will be updated if job description changes."""
    existing_test = await test_service.get_test_by_id(test_id=test_id, db=db)
    if existing_test.created_by != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own tests"
        )
    if existing_test.status != "draft":
        raise HTTPException(status_code=403, detail="Test/job description can only be updated in 'draft' status.")
    return await test_service.update_test_job_description(
        test_id=test_id,
        test_data=test_data,
        updated_by=current_user.user_id,
        db=db
    )

@router.delete("/{test_id}")
async def delete_test(
    test_id: int,
    current_user: User = Depends(recruiter_required),
    db: AsyncSession = Depends(get_db)
):
    """Delete a test (owner only)"""
    # Check ownership first
    existing_test = await test_service.get_test_by_id(test_id=test_id, db=db)
    if existing_test.created_by != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own tests"
        )
    
    await test_service.delete_test(test_id=test_id, db=db)
    return {"message": "Test deleted successfully"}

# Additional role-based endpoints

@router.get("/recruiter/all", response_model=List[TestSummary])
async def get_all_tests_for_recruiters(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(recruiter_required),  # Recruiters only
    db: AsyncSession = Depends(get_db)
):
    """Get all tests - recruiter view with additional permissions"""
    return await test_service.get_all_tests(skip=skip, limit=limit, db=db)

# Additional endpoints for test lifecycle management


@router.post("/{test_id}/schedule", response_model=TestResponse)
async def schedule_test(
    test_id: int,
    schedule_data: TestSchedule,  # Use schema for validation
    current_user: User = Depends(recruiter_required),
    db: AsyncSession = Depends(get_db)
):
    """Schedule a test for publishing (owner only)"""
    # Check ownership first
    existing_test = await test_service.get_test_by_id(test_id=test_id, db=db)
    if existing_test.created_by != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only schedule your own tests"
        )
    if existing_test.status == "live":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot reschedule a test that is already live."
        )
    return await test_service.schedule_test(
        test_id=test_id,
        schedule_data=schedule_data,
        db=db
    )

@router.post("/{test_id}/publish")
async def publish_test(
    test_id: int,
    current_user: User = Depends(recruiter_required),
    db: AsyncSession = Depends(get_db)
):
    """Manually publish a test immediately (owner only)"""
    # Check ownership first
    existing_test = await test_service.get_test_by_id(test_id=test_id, db=db)
    if existing_test.created_by != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only publish your own tests"
        )
    
    return await test_service.publish_test(test_id=test_id, db=db)

@router.post("/{test_id}/unpublish")
async def unpublish_test(
    test_id: int,
    current_user: User = Depends(recruiter_required),
    db: AsyncSession = Depends(get_db)
):
    """Unpublish/pause a test (owner only)"""
    # Check ownership first
    existing_test = await test_service.get_test_by_id(test_id=test_id, db=db)
    if existing_test.created_by != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only unpublish your own tests"
        )
    
    return await test_service.unpublish_test(test_id=test_id, db=db)

@router.get("/{test_id}/status")
async def get_test_status(
    test_id: int,
    current_user: User = Depends(recruiter_required),
    db: AsyncSession = Depends(get_db)
):
    """Get test status and basic info (owner only)"""
    # Check ownership first
    existing_test = await test_service.get_test_by_id(test_id=test_id, db=db)
    if existing_test.created_by != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own test status"
        )
    
    return await test_service.get_test_status(test_id=test_id, db=db)

@router.post("/{test_id}/duplicate")
async def duplicate_test(
    test_id: int,
    current_user: User = Depends(recruiter_required),
    db: AsyncSession = Depends(get_db)
):
    """Create a copy of an existing test (owner only)"""
    # Check ownership first
    existing_test = await test_service.get_test_by_id(test_id=test_id, db=db)
    if existing_test.created_by != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only duplicate your own tests"
        )
    
    return await test_service.duplicate_test(
        test_id=test_id,
        created_by=current_user.user_id,
        db=db
    )
