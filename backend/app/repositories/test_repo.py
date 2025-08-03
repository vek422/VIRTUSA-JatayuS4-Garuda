"""
Test Repository - Data Access Layer
Handles all database operations for tests
"""
import json
from sqlalchemy import update
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import and_, or_, desc
from app.models.test import Test, TestStatus
from app.models.user import User
from app.schemas.test_schema import TestCreate, TestUpdate
import logging

logger = logging.getLogger(__name__)


class TestRepository:
    async def update_skill_graph(self, test_id: int, skill_graph: dict, total_questions: int):
        """Update the skill_graph and total_questions fields for a test."""
        try:
            query = (
                update(Test)
                .where(Test.test_id == test_id)
                .values(
                    skill_graph=json.dumps(skill_graph) if skill_graph else None,
                    total_questions=total_questions
                )
            )
            await self.db.execute(query)
            await self.db.commit()
            logger.info(f"Updated skill_graph for test {test_id}")
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating skill_graph for test {test_id}: {str(e)}")
            raise

    async def get_test_by_id(self, test_id: int, created_by=None) -> Optional[Test]:
        """Get test by ID with optional ownership check"""
        try:
            query = select(Test).where(Test.test_id == test_id)
            if created_by:
                query = query.where(Test.created_by == created_by)
            result = await self.db.execute(query)
            return result.scalars().first()
        except Exception as e:
            logger.error(f"Error getting test: {str(e)}")
            return None

    async def get_live_tests(self) -> List[Test]:
        """Get tests that are currently live and need to be ended if deadline passed"""
        try:
            from datetime import datetime
            query = select(Test).where(
                and_(
                    Test.status == TestStatus.LIVE.value,
                    Test.assessment_deadline != None
                )
            )
            result = await self.db.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting live tests: {str(e)}")
            return []
    """Repository for Test entity following Repository Pattern"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def update_question_counts(self, test_id: int, high: int, medium: int, low: int, total_questions: int, time_limit_minutes: int):
        query = (
            update(Test)
            .where(Test.test_id == test_id)
            .values(
                high_priority_nodes=high,
                medium_priority_nodes=medium,
                low_priority_nodes=low,
                total_questions=total_questions,
                time_limit_minutes=time_limit_minutes
            )
        )
        await self.db.execute(query)
        await self.db.commit()
    async def create_test(self, test_data: TestCreate, created_by: int) -> Test:
        """Create a new test"""
        try:
            test = Test(
                test_name=test_data.test_name,
                job_description=test_data.job_description,
                resume_score_threshold=test_data.resume_score_threshold,
                max_shortlisted_candidates=test_data.max_shortlisted_candidates,
                auto_shortlist=test_data.auto_shortlist,
                total_questions=test_data.total_questions,
                time_limit_minutes=test_data.time_limit_minutes,
                total_marks=test_data.total_marks,
                high_priority_nodes=getattr(test_data, 'high_priority_nodes', None),
                medium_priority_nodes=getattr(test_data, 'medium_priority_nodes', None),
                low_priority_nodes=getattr(test_data, 'low_priority_nodes', None),
                high_priority_questions=getattr(test_data, 'high_priority_questions', None),
                medium_priority_questions=getattr(test_data, 'medium_priority_questions', None),
                low_priority_questions=getattr(test_data, 'low_priority_questions', None),
                scheduled_at=None,
                application_deadline=None,
                assessment_deadline=None,
                created_by=created_by,
                status=TestStatus.DRAFT.value
            )

            self.db.add(test)
            await self.db.commit()
            await self.db.refresh(test)

            logger.info(f"Created test {test.test_id} by user {created_by}")
            return test

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error creating test: {str(e)}")
            raise
            return result.scalars().first()

        except Exception as e:
            logger.error(f"Error getting test {test_id}: {str(e)}")
            return None

    async def get_tests_by_recruiter(self, recruiter_id: int, skip: int = 0, limit: int = 100) -> List[Test]:
        """Get all tests created by a specific recruiter"""
        try:
            query = select(Test).options(
                selectinload(Test.creator)
            ).where(Test.created_by == recruiter_id).order_by(desc(Test.created_at)).offset(skip).limit(limit)

            result = await self.db.execute(query)
            return list(result.scalars().all())

        except Exception as e:
            logger.error(
                f"Error getting tests for recruiter {recruiter_id}: {str(e)}")
            return []

    async def update_test(self, test_id: int, test_data: TestUpdate, updated_by: int, created_by=None) -> Optional[Test]:
        """Update test with ownership check"""
        try:
            query = select(Test).where(Test.test_id == test_id)
            if created_by:
                query = query.where(Test.created_by == created_by)

            result = await self.db.execute(query)
            test = result.scalar_one_or_none()

            if not test:
                return None

            # Update fields
            update_data = test_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                if field in ["high_priority_nodes", "medium_priority_nodes", "low_priority_nodes"]:
                    setattr(test, field, value)
                else:
                    setattr(test, field, value)

            test.updated_by = updated_by

            await self.db.commit()
            await self.db.refresh(test)

            logger.info(f"Updated test {test_id} by user {updated_by}")
            return test

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating test {test_id}: {str(e)}")
            raise

    async def delete_test(self, test_id: int, created_by: int = None) -> bool:
        """Delete test with ownership check"""
        try:
            query = select(Test).where(Test.test_id == test_id)
            if created_by:
                query = query.where(Test.created_by == created_by)

            result = await self.db.execute(query)
            test = result.scalar_one_or_none()

            if not test:
                return False

            await self.db.delete(test)
            await self.db.commit()

            logger.info(f"Deleted test {test_id}")
            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting test {test_id}: {str(e)}")
            return False

    async def update_test_ai_data(self, test_id: int, parsed_jd: Dict[str, Any], skill_graph: Dict[str, Any]) -> Optional[Test]:
        """Update test with AI-generated data"""
        try:
            result = await self.db.execute(select(Test).where(Test.test_id == test_id))
            test = result.scalar_one_or_none()

            if not test:
                return None

            test.parsed_job_description = json.dumps(parsed_jd)
            test.skill_graph = json.dumps(skill_graph)

            await self.db.commit()
            await self.db.refresh(test)

            logger.info(f"Updated AI data for test {test_id}")
            return test

        except Exception as e:
            await self.db.rollback()
            logger.error(
                f"Error updating AI data for test {test_id}: {str(e)}")
            raise

    async def update_test_status(self, test_id: int, status: str, is_published: bool = None) -> Optional[Test]:
        """Update test status and publishing state"""
        try:
            result = await self.db.execute(select(Test).where(Test.test_id == test_id))
            test = result.scalar_one_or_none()

            if not test:
                return None

            test.status = status
            if is_published is not None:
                test.is_published = is_published

            await self.db.commit()
            await self.db.refresh(test)

            logger.info(f"Updated status for test {test_id} to {status}")
            return test

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating status for test {test_id}: {str(e)}")
            raise

    async def get_scheduled_tests(self) -> List[Test]:
        """Get tests that need to be published"""
        try:
            from datetime import datetime

            query = select(Test).where(
                and_(
                    Test.status == TestStatus.SCHEDULED.value,
                    Test.scheduled_at <= datetime.utcnow(),
                    Test.is_published == False
                )
            )

            result = await self.db.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Error getting scheduled tests: {str(e)}")
            return []

    async def update_test_standalone(self, test_id: int, test_data: dict, updated_by: int) -> Optional[Test]:
        """Update an existing test"""
        result = await self.db.execute(select(Test).where(Test.test_id == test_id))
        test = result.scalar_one_or_none()

        if not test:
            return None

        # Update fields if provided
        if "test_name" in test_data and test_data["test_name"] is not None:
            test.test_name = test_data["test_name"]
        if "job_description" in test_data:
            test.job_description = test_data["job_description"]
        if "parsed_job_description" in test_data:
            test.parsed_job_description = json.dumps(
                test_data["parsed_job_description"]) if test_data["parsed_job_description"] else None
        if "skill_graph" in test_data:
            test.skill_graph = json.dumps(
                test_data["skill_graph"]) if test_data["skill_graph"] else None
        if "scheduled_at" in test_data:
            test.scheduled_at = test_data["scheduled_at"]

        test.updated_by = updated_by

        await self.db.commit()
        await self.db.refresh(test)
        return test

    async def delete_test_standalone(self, test_id: int) -> bool:
        """Delete a test"""
        result = await self.db.execute(select(Test).where(Test.test_id == test_id))
        test = result.scalar_one_or_none()

        if not test:
            return False

        await self.db.delete(test)
        await self.db.commit()
        return True

    async def get_all_tests(self, skip: int = 0, limit: int = 100) -> List[Test]:
        """Get all tests with pagination"""
        try:
            query = select(Test).options(
                selectinload(Test.creator)
            ).order_by(desc(Test.created_at)).offset(skip).limit(limit)

            result = await self.db.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Error getting all tests: {str(e)}")
            return []

    async def update_test_schedule(self, test_id: int, schedule_data: Dict[str, Any]) -> Optional[Test]:
        """Update test schedule information"""
        try:
            result = await self.db.execute(select(Test).where(Test.test_id == test_id))
            test = result.scalar_one_or_none()

            if not test:
                return None

            if "scheduled_at" in schedule_data:
                test.scheduled_at = schedule_data["scheduled_at"]
            if "application_deadline" in schedule_data:
                test.application_deadline = schedule_data["application_deadline"]
            if "assessment_deadline" in schedule_data:
                test.assessment_deadline = schedule_data["assessment_deadline"]

            await self.db.commit()
            await self.db.refresh(test)

            logger.info(f"Updated schedule for test {test_id}")
            return test

        except Exception as e:
            await self.db.rollback()
            logger.error(
                f"Error updating schedule for test {test_id}: {str(e)}")
            raise

    async def update_is_published(self, test_id: int, is_published: bool) -> Optional[Test]:
        """Update test published status"""
        try:
            result = await self.db.execute(select(Test).where(Test.test_id == test_id))
            test = result.scalar_one_or_none()

            if not test:
                return None

            test.is_published = is_published

            await self.db.commit()
            await self.db.refresh(test)

            logger.info(
                f"Updated is_published for test {test_id} to {is_published}")
            return test

        except Exception as e:
            await self.db.rollback()
            logger.error(
                f"Error updating is_published for test {test_id}: {str(e)}")
            raise


async def get_test_by_id(db: AsyncSession, test_id: int):
    repo = TestRepository(db)
    return await repo.get_test_by_id(test_id)
