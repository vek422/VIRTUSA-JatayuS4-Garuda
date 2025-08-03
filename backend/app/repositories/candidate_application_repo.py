from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, insert
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict, Any
from app.models.candidate_application import CandidateApplication
from datetime import datetime
from app.models.user import User
class CandidateApplicationRepository:
    @staticmethod
    async def create_application(db: AsyncSession, data: dict) -> CandidateApplication:
        application = CandidateApplication(**data)
        db.add(application)
        await db.commit()
        await db.refresh(application)
        return application

    @staticmethod
    async def get_by_user_and_test(db: AsyncSession, user_id: int, test_id: int) -> Optional[CandidateApplication]:
        result = await db.execute(
            select(CandidateApplication).where(
                CandidateApplication.user_id == user_id,
                CandidateApplication.test_id == test_id
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_application(db: AsyncSession, application_id: int, update_data: dict) -> Optional[CandidateApplication]:
        result = await db.execute(
            select(CandidateApplication).where(CandidateApplication.application_id == application_id)
        )
        application = result.scalar_one_or_none()
        if not application:
            return None
        for k, v in update_data.items():
            setattr(application, k, v)
        application.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(application)
        return application

    @staticmethod
    async def get_by_id(db: AsyncSession, application_id: int) -> Optional[CandidateApplication]:
        result = await db.execute(
            select(CandidateApplication).where(CandidateApplication.application_id == application_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def bulk_create(db: AsyncSession, data_list: List[dict]) -> List[CandidateApplication]:
        applications = [CandidateApplication(**data) for data in data_list]
        db.add_all(applications)
        await db.commit()
        for app in applications:
            await db.refresh(app)
        return applications

    @staticmethod
    async def delete_application(db: AsyncSession, application_id: int) -> bool:
        result = await db.execute(
            select(CandidateApplication).where(CandidateApplication.application_id == application_id)
        )
        application = result.scalar_one_or_none()
        if not application:
            return False
        # Cascade delete handled by SQLAlchemy relationship
        await db.delete(application)
        await db.commit()
        return True

    @staticmethod
    async def get_applications_by_test_id(db: AsyncSession, test_id: int) -> List[CandidateApplication]:
        """Get all candidate applications for a specific test."""
        result = await db.execute(
            select(CandidateApplication).where(CandidateApplication.test_id == test_id)
        )
        return result.scalars().all()

    @staticmethod
    async def get_application_with_user_by_id(db: AsyncSession, application_id: int) -> Optional[CandidateApplication]:
        """Get a single application with user information."""
        from app.models.user import User
        result = await db.execute(
            select(CandidateApplication)
            .options(selectinload(CandidateApplication.user))
            .where(CandidateApplication.application_id == application_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_applications_by_test_id_with_user(db: AsyncSession, test_id: int) -> List[CandidateApplication]:
        """Get all candidate applications for a specific test with user information."""
        from sqlalchemy.orm import selectinload
        result = await db.execute(
            select(CandidateApplication)
            .where(CandidateApplication.test_id == test_id)
            .options(selectinload(CandidateApplication.user))
        )
        return result.scalars().all()

    @staticmethod
    async def get_applications_for_shortlisting(db: AsyncSession, test_id: int, min_score: int):
        from sqlalchemy.orm import selectinload
        from app.models.candidate_application import CandidateApplication
        result = await db.execute(
            select(CandidateApplication)
            .where(CandidateApplication.test_id == test_id)
            .where(CandidateApplication.resume_score >= min_score)
            .options(selectinload(CandidateApplication.user))
        )
        return result.scalars().all()

    @staticmethod
    async def get_shortlisted_candidates_with_emails(db: AsyncSession, test_id: int) -> List[Dict[str, Any]]:
        """Get all shortlisted candidates for a test with their email addresses."""

        
        result = await db.execute(
            select(CandidateApplication)
            .where(CandidateApplication.test_id == test_id)
            .where(CandidateApplication.is_shortlisted == True)
            .options(selectinload(CandidateApplication.user))
        )
        applications = result.scalars().all()
        
        candidates = []
        for app in applications:
            if app.user:  # Ensure user relationship is loaded
                candidates.append({
                    'application_id': app.application_id,
                    'user_id': app.user_id,
                    'name': app.user.name,
                    'email': app.user.email
                })
        
        return candidates