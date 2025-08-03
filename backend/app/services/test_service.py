
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.repositories.test_repo import TestRepository
from app.models.test import TestStatus
from sqlalchemy.orm import sessionmaker
import os
from typing import List, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.test_repo import TestRepository
from app.services.ai_service import get_ai_service
from app.services.notification_service import get_notification_service
from app.schemas.test_schema import TestCreate, TestUpdate, TestResponse,  TestSchedule
from app.models.test import Test, TestStatus
from app.models.user import User
import json
import logging

# import pytz


DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://user:password@localhost/recruitment")
engine = create_async_engine(DATABASE_URL, future=True)
AsyncSessionLocal = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession)


logger = logging.getLogger(__name__)


class TestService:
    async def update_question_counts(self, test_id: int, data, user_id: int, db: AsyncSession) -> dict:
        """Update per-priority question counts, total_questions, and time_limit_minutes for a test."""
        repo = TestRepository(db)
        test = await repo.get_test_by_id(test_id)
        if not test:
            raise HTTPException(status_code=404, detail="Test not found")
        if test.created_by != user_id:
            raise HTTPException(
                status_code=403, detail="You can only update your own tests")
        high = data.high_priority_questions
        medium = data.medium_priority_questions
        low = data.low_priority_questions
        total_questions = data.total_questions
        time_limit_minutes = data.time_limit_minutes
        await repo.update_question_counts(test_id, high, medium, low, total_questions, time_limit_minutes)
        return {
            "test_id": test_id,
            "high_priority_questions": high,
            "medium_priority_questions": medium,
            "low_priority_questions": low,
            "total_questions": total_questions,
            "time_limit_minutes": time_limit_minutes,
            "message": "Question counts and time limit updated successfully."
        }

    async def update_test_job_description(self, test_id: int, test_data: TestUpdate, updated_by: int, db: AsyncSession) -> TestResponse:
        """Update job description, resume_score_threshold, max_shortlisted_candidates, and auto_shortlist for a test. Skill graph will be updated if job description changes."""
        try:
            repo = TestRepository(db)
            test = await repo.get_test_by_id(test_id)
            if not test:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Test not found")
            # Only allow job description update in draft state
            if test.status != TestStatus.DRAFT.value:
                raise HTTPException(
                    status_code=400, detail="Job description can only be updated in draft state.")
            # Check if job_description is being updated and actually changed
            job_desc_updated = False
            if "job_description" in test_data.dict(exclude_unset=True):
                if test_data.job_description is not None and test_data.job_description != test.job_description:
                    job_desc_updated = True
            # Update fields
            updated_test = await repo.update_test(test_id, test_data, updated_by)
            # If job_description changed, re-run AI pipeline and update node counts
            if job_desc_updated and updated_test.job_description:
                parsed_jd = await self.ai_service.parse_job_description(updated_test.job_description)
                skill_graph = await self.ai_service.generate_skill_graph(parsed_jd)
                await repo.update_test_ai_data(updated_test.test_id, parsed_jd, skill_graph)
                from app.services.skill_graph_generation.state import SkillGraph
                from app.services.skill_graph_generation.graph import count_nodes_by_priority
                if skill_graph and isinstance(skill_graph, dict) and "root_nodes" in skill_graph:
                    node_counts = count_nodes_by_priority(
                        SkillGraph.model_validate(skill_graph))
                    high_priority_questions = node_counts["H"] * 5
                    medium_priority_questions = node_counts["M"] * 3
                    low_priority_questions = node_counts["L"] * 33

                    total_questions = high_priority_questions + \
                        medium_priority_questions + low_priority_questions
                    total_seconds = (
                        (high_priority_questions * 90) +
                        (medium_priority_questions * 60) +
                        (low_priority_questions * 45)
                    )
                    time_limit_minutes = max(5, min(480, total_seconds // 60))
                    total_marks = total_questions
                    await repo.update_skill_graph(
                        updated_test.test_id,
                        skill_graph,
                        total_questions
                    )
                    from sqlalchemy import text
                    await db.execute(
                        text("""
                        UPDATE tests SET high_priority_nodes = :h, medium_priority_nodes = :m, low_priority_nodes = :l, high_priority_questions = :hq, medium_priority_questions = :mq, low_priority_questions = :lq, total_questions = :tq, time_limit_minutes = :tlm, total_marks = :tm WHERE test_id = :tid
                        """),
                        {
                            "h": node_counts["H"],
                            "m": node_counts["M"],
                            "l": node_counts["L"],
                            "hq": high_priority_questions,
                            "mq": medium_priority_questions,
                            "lq": low_priority_questions,
                            "tq": total_questions,
                            "tlm": time_limit_minutes,
                            "tm": total_marks,
                            "tid": updated_test.test_id
                        }
                    )
                    await db.commit()
                # Refresh updated_test with new AI fields
                updated_test = await repo.get_test_by_id(test_id)
            creator = await self._get_user_by_id(updated_test.created_by, db)
            return await self._format_test_response(updated_test, creator)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating test {test_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update test: {str(e)}"
            )

    # async def schedule_test(self, test_id: int, schedule_data: TestSchedule, updated_by: int, db: AsyncSession) -> TestResponse:
    #     """Schedule a test: set scheduled_at, assessment_deadline, and schedule status update jobs"""
    #     repo = TestRepository(db)
    #     test = await repo.get_test_by_id(test_id)
    #     if not test:
    #         raise HTTPException(status_code=404, detail="Test not found")
    #     # Only allow scheduling if test is in draft
    #     if test.status != TestStatus.DRAFT.value:
    #         raise HTTPException(
    #             status_code=400, detail="Test can only be scheduled from draft state")
    #     # Store the schedule dates and update status
    #     test.scheduled_at = schedule_data.scheduled_at
    #     test.application_deadline = schedule_data.application_deadline
    #     test.assessment_deadline = schedule_data.assessment_deadline
    #     test.status = TestStatus.SCHEDULED.value
    #     test.updated_by = updated_by
    #     await db.commit()
    #     await db.refresh(test)

    #     # Schedule status update jobs using Celery

    #     def to_naive_utc(dt):
    #         if dt is None:
    #             return None
    #         if dt.tzinfo is not None:
    #             return dt.astimezone(pytz.UTC).replace(tzinfo=None)
    #         return dt

    #     naive_scheduled_at = to_naive_utc(test.scheduled_at)
    #     naive_assessment_deadline = to_naive_utc(test.assessment_deadline)

    #     if naive_scheduled_at:
    #         set_test_status_live.apply_async(
    #             args=[test.test_id], eta=naive_scheduled_at)
    #         logger.info(
    #             f"Scheduled set_test_status_live for test {test.test_id} at {naive_scheduled_at} (Celery)")
    #     if naive_assessment_deadline:
    #         set_test_status_ended.apply_async(
    #             args=[test.test_id], eta=naive_assessment_deadline)
    #         logger.info(
    #             f"Scheduled set_test_status_ended for test {test.test_id} at {naive_assessment_deadline} (Celery)")

    #     creator = await self._get_user_by_id(test.created_by, db)
    #     return await self._format_test_response(test, creator)
    # """Test Service with AI integration and notifications"""

    def __init__(self):
        self.ai_service = get_ai_service()
        self.notification_service = get_notification_service()

    async def create_test_with_ai(self, test_data: TestCreate, created_by: int, db: AsyncSession) -> TestResponse:
        """Create a new test with AI processing and auto question distribution"""
        try:
            # 1. If job_description is present, generate skill graph and set question fields
            if test_data.job_description:
                ai_service = self.ai_service
                parsed_jd = await ai_service.parse_job_description(test_data.job_description)
                skill_graph = await ai_service.generate_skill_graph(parsed_jd)
                from app.services.skill_graph_generation.state import SkillGraph
                from copy import deepcopy
                if skill_graph and isinstance(skill_graph, dict) and "root_nodes" in skill_graph:
                    # Count nodes by priority for new columns
                    from app.services.skill_graph_generation.graph import count_nodes_by_priority
                    node_counts = count_nodes_by_priority(
                        SkillGraph.model_validate(skill_graph))
                    test_data = deepcopy(test_data)
                    test_data.high_priority_nodes = node_counts["H"]
                    test_data.medium_priority_nodes = node_counts["M"]
                    test_data.low_priority_nodes = node_counts["L"]

                    # Set initial question counts based on node counts
                    test_data.high_priority_questions = node_counts["H"] * 5
                    test_data.medium_priority_questions = node_counts["M"] * 3
                    test_data.low_priority_questions = node_counts["L"] * 3
                    test_data.total_questions = (
                        test_data.high_priority_questions +
                        test_data.medium_priority_questions +
                        test_data.low_priority_questions
                    )
                    # Calculate time limit in minutes
                    total_seconds = (
                        test_data.high_priority_questions * 90 +
                        test_data.medium_priority_questions * 60 +
                        test_data.low_priority_questions * 45
                    )
                    test_data.time_limit_minutes = max(
                        5, min(480, total_seconds // 60))
                    test_data.total_marks = test_data.total_questions

            # 2. Create the test
            repo = TestRepository(db)
            test = await repo.create_test(test_data, created_by)

            # 3. Get creator info for notifications
            creator = await self._get_user_by_id(created_by, db)

            # 4. Process job description with AI if provided (update test with AI data)
            if test_data.job_description:
                await self._process_job_description_with_ai(test, creator, db)
                # Fetch updated test data after AI processing
                test = await repo.get_test_by_id(test.test_id)

            # 5. Log major event
            from app.services.logging import log_major_event
            await log_major_event(
                action="test_created",
                status="success",
                user=str(created_by),
                details=f"Test '{test.test_name}' created.",
                entity=str(test.test_id)
            )
            # 6. Return test response
            return await self._format_test_response(test, creator)

        except Exception as e:
            logger.error(f"Error creating test with AI: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create test: {str(e)}"
            )

    async def _process_job_description_with_ai(self, test: Test, creator: User, db: AsyncSession) -> None:
        """Process job description with AI in background"""
        try:
            repo = TestRepository(db)

            # 1. Parse job description
            parsed_jd = await self.ai_service.parse_job_description(test.job_description)

            # 2. Generate skill graph
            skill_graph = await self.ai_service.generate_skill_graph(parsed_jd)

            # 3. Update test with AI results
            await repo.update_test_ai_data(test.test_id, parsed_jd, skill_graph)

            logger.info(f"AI processing completed for test {test.test_id}")

        except Exception as e:
            logger.error(f"AI processing failed for test {test.test_id}: {e}")

    async def schedule_test(self, test_id: int, schedule_data: Any, db: AsyncSession) -> dict:
        """Schedule a test for publishing, enforcing one-or-nothing principle."""
        try:
            test_repo = TestRepository(db)
            # Get test and creator
            test = await test_repo.get_test_by_id(test_id)
            if not test:
                raise HTTPException(status_code=404, detail="Test not found")

            creator = await self._get_user_by_id(test.created_by, db)
            # Only allow scheduling if not already scheduled
            if test.status == TestStatus.SCHEDULED.value:
                raise HTTPException(
                    status_code=400, detail="Test is already scheduled.")
            # Convert schedule_data to dict for repository
            schedule_dict = schedule_data.dict(exclude_unset=True) if hasattr(
                schedule_data, 'dict') else schedule_data

            # Update test with schedule info
            await test_repo.update_test_schedule(test_id, schedule_dict)
            await test_repo.update_test_status(test_id, TestStatus.SCHEDULED.value)

            # Send notification to recruiter
            updated_test = await test_repo.get_test_by_id(test_id)
            await self.notification_service.send_test_scheduled_notification(updated_test, creator)
            
            # Send notifications to all shortlisted candidates
            try:
                response_codes = await self.notification_service.send_test_scheduled_notifications_to_shortlisted_candidates(updated_test, db)
                logger.info(f"Sent test scheduled notifications to shortlisted candidates for test {test_id}. Response codes: {response_codes}")
            except Exception as e:
                logger.error(f"Failed to send notifications to shortlisted candidates for test {test_id}: {str(e)}")
                # Don't fail the entire operation if email sending fails
            
            return await self._format_test_response(updated_test, creator)

        except Exception as e:
            logger.error(f"Error scheduling test {test_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to schedule test: {str(e)}"
            )

    async def publish_test(self, test_id: int, db: AsyncSession) -> Dict[str, Any]:
        """Manually publish a test"""
        try:
            test_repo = TestRepository(db)

            # Get test and creator
            test = await test_repo.get_test_by_id(test_id)
            if not test:
                raise HTTPException(status_code=404, detail="Test not found")

            creator = await self._get_user_by_id(test.created_by, db)

            # Update test status
            await test_repo.update_test_status(test_id, TestStatus.PUBLISHED.value)
            await test_repo.update_is_published(test_id, True)

            # Send notification
            updated_test = await test_repo.get_test_by_id(test_id)
            await self.notification_service.send_test_published_notification(updated_test, creator)

            return {
                "message": "Test published successfully",
                "test_id": test_id,
                "status": TestStatus.PUBLISHED.value,
                "is_published": True
            }

        except Exception as e:
            logger.error(f"Error publishing test {test_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to publish test: {str(e)}"
            )

    async def unpublish_test(self, test_id: int, db: AsyncSession) -> Dict[str, Any]:
        """Unpublish/pause a test"""
        try:
            test_repo = TestRepository(db)

            # Get test and creator
            test = await test_repo.get_test_by_id(test_id)
            if not test:
                raise HTTPException(status_code=404, detail="Test not found")

            creator = await self._get_user_by_id(test.created_by, db)

            # Update test status
            await test_repo.update_test_status(test_id, TestStatus.PAUSED.value)
            await test_repo.update_is_published(test_id, False)

            # Send notification
            updated_test = await test_repo.get_test_by_id(test_id)
            await self.notification_service.send_test_unpublished_notification(updated_test, creator)

            return {
                "message": "Test unpublished successfully",
                "test_id": test_id,
                "status": TestStatus.PAUSED.value,
                "is_published": False
            }

        except Exception as e:
            logger.error(f"Error unpublishing test {test_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to unpublish test: {str(e)}"
            )

    async def duplicate_test(self, test_id: int, created_by: int, db: AsyncSession) -> TestResponse:
        """Create a duplicate of an existing test"""
        try:
            test_repo = TestRepository(db)

            # Get original test
            original_test = await test_repo.get_test_by_id(test_id)
            if not original_test:
                raise HTTPException(status_code=404, detail="Test not found")

            # Create duplicate test data
            duplicate_data = TestCreate(
                test_name=f"{original_test.test_name} (Copy)",
                job_description=original_test.job_description,
                resume_score_threshold=original_test.resume_score_threshold,
                max_shortlisted_candidates=original_test.max_shortlisted_candidates,
                auto_shortlist=original_test.auto_shortlist,
                total_questions=original_test.total_questions,
                time_limit_minutes=original_test.time_limit_minutes,
                total_marks=original_test.total_marks,
                scheduled_at=None,  # Reset scheduling
                application_deadline=None,
                assessment_deadline=None
            )

            # Create the duplicate
            duplicate_test = await test_repo.create_test(duplicate_data, created_by)

            # Copy AI-generated content if available
            if original_test.parsed_job_description:
                await test_repo.update_parsed_jd(duplicate_test.test_id, json.loads(original_test.parsed_job_description))

            if original_test.skill_graph:
                await test_repo.update_skill_graph(duplicate_test.test_id, json.loads(original_test.skill_graph))

            # Get creator and return response
            creator = await self._get_user_by_id(created_by, db)
            return await self._format_test_response(duplicate_test, creator)

        except Exception as e:
            logger.error(f"Error duplicating test {test_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to duplicate test: {str(e)}"
            )

    async def get_test_status(self, test_id: int, db: AsyncSession) -> Dict[str, Any]:
        """Get test status information"""
        try:
            test_repo = TestRepository(db)
            test = await test_repo.get_test_by_id(test_id)

            if not test:
                raise HTTPException(status_code=404, detail="Test not found")

            return {
                "test_id": test.test_id,
                "test_name": test.test_name,
                "status": test.status,
                "is_published": test.is_published,
                "scheduled_at": test.scheduled_at,
                "application_deadline": test.application_deadline,
                "assessment_deadline": test.assessment_deadline,
                "created_at": test.created_at,
                "updated_at": test.updated_at,
                "has_parsed_jd": test.parsed_job_description is not None,
                "has_skill_graph": test.skill_graph is not None
            }

        except Exception as e:
            logger.error(f"Error getting test status {test_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get test status: {str(e)}"
            )

    async def get_all_tests(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[TestResponse]:
        """Get all tests with pagination"""
        try:
            repo = TestRepository(db)
            tests = await repo.get_all_tests(skip=skip, limit=limit)

            # Format responses with creator info
            responses = []
            for test in tests:
                creator = await self._get_user_by_id(test.created_by, db)
                response = await self._format_test_response(test, creator)
                responses.append(response)

            return responses

        except Exception as e:
            logger.error(f"Error getting all tests: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get tests: {str(e)}"
            )

    async def get_tests_by_creator(self, creator_id: int, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[TestResponse]:
        """Get tests created by a specific user"""
        try:
            repo = TestRepository(db)
            tests = await repo.get_tests_by_recruiter(recruiter_id=creator_id, skip=skip, limit=limit)

            # Get creator info once
            creator = await self._get_user_by_id(creator_id, db)

            # Format responses
            responses = []
            for test in tests:
                response = await self._format_test_response(test, creator)
                responses.append(response)

            return responses

        except Exception as e:
            logger.error(f"Error getting tests by creator {creator_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get tests: {str(e)}"
            )

    async def get_test_by_id(self, test_id: int, db: AsyncSession) -> TestResponse:
        """Get a test by ID"""
        try:
            repo = TestRepository(db)
            test = await repo.get_test_by_id(test_id)

            if not test:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Test not found"
                )

            # Get creator info
            creator = await self._get_user_by_id(test.created_by, db)

            return await self._format_test_response(test, creator)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting test {test_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get test: {str(e)}"
            )

    async def update_test(self, test_id: int, test_data: TestUpdate, updated_by: int, db: AsyncSession) -> TestResponse:
        """Update a test"""
        try:
            repo = TestRepository(db)

            # Check if test exists and user has permission
            test = await repo.get_test_by_id(test_id)
            if not test:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Test not found"
                )

            # Get the current test before update
            current_test = await repo.get_test_by_id(test_id)

            # Check if job_description is being updated and actually changed
            job_desc_updated = False
            if "job_description" in test_data.dict(exclude_unset=True):
                if test_data.job_description is not None and test_data.job_description != current_test.job_description:
                    job_desc_updated = True

            # Update the test
            updated_test = await repo.update_test(test_id, test_data, updated_by)

            # If job_description changed, re-run AI pipeline and update node counts
            if job_desc_updated and updated_test.job_description:
                parsed_jd = await self.ai_service.parse_job_description(updated_test.job_description)
                skill_graph = await self.ai_service.generate_skill_graph(parsed_jd)
                await repo.update_test_ai_data(updated_test.test_id, parsed_jd, skill_graph)
                # Also update node counts in the test table
                from app.services.skill_graph_generation.state import SkillGraph
                from app.services.skill_graph_generation.graph import count_nodes_by_priority
                if skill_graph and isinstance(skill_graph, dict) and "root_nodes" in skill_graph:
                    node_counts = count_nodes_by_priority(
                        SkillGraph.model_validate(skill_graph))
                    await repo.update_skill_graph(
                        updated_test.test_id,
                        skill_graph,
                        updated_test.total_questions
                    )
                    # Directly update node count columns
                    from sqlalchemy import text
                    await db.execute(
                        text("""
                        UPDATE tests SET high_priority_nodes = :h, medium_priority_nodes = :m, low_priority_nodes = :l WHERE test_id = :tid
                        """),
                        {"h": node_counts["H"], "m": node_counts["M"],
                            "l": node_counts["L"], "tid": updated_test.test_id}
                    )
                    await db.commit()
                # Refresh updated_test with new AI fields
                updated_test = await repo.get_test_by_id(test_id)

            # Get creator info
            creator = await self._get_user_by_id(updated_test.created_by, db)

            # Send notification (use send_test_created_notification as fallback, or skip if not needed)
            # await self.notification_service.send_test_created_notification(updated_test, creator)

            return await self._format_test_response(updated_test, creator)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating test {test_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update test: {str(e)}"
            )

    async def delete_test(self, test_id: int, db: AsyncSession) -> Dict[str, str]:
        """Delete a test"""
        try:
            repo = TestRepository(db)

            # Check if test exists
            test = await repo.get_test_by_id(test_id)
            if not test:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Test not found"
                )

            # Get creator info for notification
            creator = await self._get_user_by_id(test.created_by, db)

            # Delete the test
            await repo.delete_test(test_id)

            # Send notification
            self.notification_service.notify_test_deleted(
                test_name=test.test_name,
                test_id=test_id,
                recruiter_email=creator.email
            )

            from app.services.logging import log_major_event
            await log_major_event(
                action="test_deleted",
                status="success",
                user=str(test.created_by),
                details=f"Test {test.test_name} deleted.",
                entity=str(test_id)
            )
            return {"message": "Test deleted successfully"}

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting test {test_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete test: {str(e)}"
            )

    async def _get_user_by_id(self, user_id: int, db: AsyncSession) -> User:
        """Get user by ID"""
        from app.repositories.user_repo import get_user_by_id
        user = await get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    async def _format_test_response(self, test: Test, creator: User = None) -> TestResponse:
        """Format test response with creator info, total candidates, and duration"""
        import json
        from app.repositories.candidate_count_helper import count_candidates_by_test_id
        parsed_jd = None
        skill_graph = None
        try:
            if test.parsed_job_description:
                parsed_jd = json.loads(test.parsed_job_description)
        except Exception:
            parsed_jd = None
        try:
            if test.skill_graph:
                skill_graph = json.loads(test.skill_graph)
                if not isinstance(skill_graph, dict):
                    skill_graph = None
        except Exception:
            skill_graph = None

        # Get total candidates
        total_candidates = await count_candidates_by_test_id(self.db, test.test_id) if hasattr(self, 'db') and self.db else 0
        # If self.db is not set, fallback to 0 (should be set in service methods)

        # Calculate duration (in minutes) if scheduled_at and assessment_deadline are present
        duration = None
        if test.scheduled_at and test.assessment_deadline:
            duration = int((test.assessment_deadline -
                           test.scheduled_at).total_seconds() // 60)

        return TestResponse(
            test_id=test.test_id,
            test_name=test.test_name,
            job_description=test.job_description,
            parsed_job_description=parsed_jd,
            skill_graph=skill_graph,
            resume_score_threshold=test.resume_score_threshold,
            max_shortlisted_candidates=test.max_shortlisted_candidates,
            auto_shortlist=test.auto_shortlist,
            total_questions=test.total_questions,
            time_limit_minutes=test.time_limit_minutes,
            total_marks=test.total_marks,
            status=test.status,
            is_published=test.is_published,
            scheduled_at=test.scheduled_at,
            application_deadline=test.application_deadline,
            assessment_deadline=test.assessment_deadline,
            created_by=test.created_by,
            updated_by=test.updated_by,
            created_at=test.created_at,
            updated_at=test.updated_at,
            creator_name=creator.name if creator else None,
            creator_role=creator.role.value if creator else None,
            total_candidates=total_candidates,
            duration=duration,
            high_priority_questions=getattr(
                test, 'high_priority_questions', None),
            medium_priority_questions=getattr(
                test, 'medium_priority_questions', None),
            low_priority_questions=getattr(
                test, 'low_priority_questions', None),
            high_priority_nodes=getattr(test, 'high_priority_nodes', None),
            medium_priority_nodes=getattr(test, 'medium_priority_nodes', None),
            low_priority_nodes=getattr(test, 'low_priority_nodes', None)
        )


# Service instance
test_service = TestService()


def get_test_service() -> TestService:
    """Get test service instance"""
    return test_service

# Alias for backward compatibility


def get_enhanced_test_service() -> TestService:
    """Get enhanced test service instance (alias)"""
    return test_service
