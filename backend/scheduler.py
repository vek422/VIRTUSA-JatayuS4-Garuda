# scheduler.py - Enhanced Test State Management System

import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, or_, and_, func
from datetime import datetime, timezone, timedelta

from app.repositories.test_repo import TestRepository
from app.models.test import TestStatus, Test
from app.models.candidate_application import CandidateApplication
from app.db.database import AsyncSessionLocal

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestScheduler:
    """Enhanced test scheduler with comprehensive state management"""
    
    def __init__(self, check_interval_seconds=30):
        self.check_interval = check_interval_seconds
        self.preparing_timeout_minutes = 1  # Move PREPARING back to DRAFT after 1 minute if no candidates
        
    async def log_scheduler_event(self, action: str, test_id: int, details: str, status: str = "success"):
        """Log scheduler events to database"""
        try:
            from app.services.logging import log_major_event
            await log_major_event(
                action=f"scheduler_{action}",
                status=status,
                user="system",
                details=f"Test {test_id}: {details}",
                entity="test_scheduler"
            )
        except Exception as e:
            logger.warning(f"Failed to log scheduler event: {e}")

    async def handle_preparing_to_draft_transition(self, session):
        """Move PREPARING tests back to DRAFT if no candidates for specified time"""
        try:
            now = datetime.now(timezone.utc)
            timeout_threshold = now - timedelta(minutes=self.preparing_timeout_minutes)
            
            # Find PREPARING tests that are old enough and have no candidates
            preparing_tests_stmt = select(Test).where(
                and_(
                    Test.status == TestStatus.PREPARING.value,
                    Test.updated_at <= timeout_threshold
                )
            )
            preparing_result = await session.execute(preparing_tests_stmt)
            preparing_tests = preparing_result.scalars().all()
            
            for test in preparing_tests:
                # Check if test has any candidate applications
                candidate_count_stmt = select(func.count(CandidateApplication.application_id)).where(
                    CandidateApplication.test_id == test.test_id
                )
                candidate_count_result = await session.execute(candidate_count_stmt)
                candidate_count = candidate_count_result.scalar()
                
                if candidate_count == 0:
                    # No candidates, move back to DRAFT
                    repo = TestRepository(session)
                    await repo.update_test_status(test.test_id, TestStatus.DRAFT.value, is_published=False)
                    logger.info(f"[Scheduler] Test {test.test_id} moved from PREPARING to DRAFT (no candidates)")
                    await self.log_scheduler_event(
                        "preparing_to_draft", 
                        test.test_id, 
                        f"Moved to DRAFT after {self.preparing_timeout_minutes} minutes with no candidate applications"
                    )
                else:
                    logger.debug(f"[Scheduler] Test {test.test_id} staying in PREPARING (has {candidate_count} candidates)")
                    
        except Exception as e:
            logger.error(f"[Scheduler] Error in PREPARING→DRAFT transition: {e}")
            
    async def handle_scheduled_to_live_transition(self, session):
        """Move SCHEDULED tests to LIVE when scheduled time arrives"""
        try:
            now = datetime.now(timezone.utc)
            
            scheduled_stmt = select(Test).where(
                and_(
                    Test.status == TestStatus.SCHEDULED.value,
                    Test.scheduled_at <= now,
                    or_(
                        Test.assessment_deadline.is_(None),
                        Test.assessment_deadline > now
                    )
                )
            )
            scheduled_result = await session.execute(scheduled_stmt)
            scheduled_tests = scheduled_result.scalars().all()
            
            for test in scheduled_tests:
                try:
                    # Check if test has shortlisted candidates
                    shortlisted_count_stmt = select(func.count(CandidateApplication.application_id)).where(
                        and_(
                            CandidateApplication.test_id == test.test_id,
                            CandidateApplication.is_shortlisted == True
                        )
                    )
                    shortlisted_count_result = await session.execute(shortlisted_count_stmt)
                    shortlisted_count = shortlisted_count_result.scalar()
                    
                    repo = TestRepository(session)
                    await repo.update_test_status(test.test_id, TestStatus.LIVE.value, is_published=True)
                    logger.info(f"[Scheduler] Test {test.test_id} moved to LIVE ({shortlisted_count} shortlisted candidates)")
                    await self.log_scheduler_event(
                        "scheduled_to_live", 
                        test.test_id, 
                        f"Test went LIVE with {shortlisted_count} shortlisted candidates"
                    )
                    
                except Exception as e:
                    logger.error(f"[Scheduler] Failed to move test {test.test_id} to LIVE: {e}")
                    await self.log_scheduler_event(
                        "scheduled_to_live", 
                        test.test_id, 
                        f"Failed to move to LIVE: {str(e)}", 
                        "error"
                    )
                    
        except Exception as e:
            logger.error(f"[Scheduler] Error in SCHEDULED→LIVE transition: {e}")

    async def handle_live_to_ended_transition(self, session):
        """End LIVE tests when assessment deadline passes"""
        try:
            now = datetime.now(timezone.utc)
            
            ending_stmt = select(Test).where(
                and_(
                    Test.status == TestStatus.LIVE.value,
                    Test.assessment_deadline <= now
                )
            )
            ending_result = await session.execute(ending_stmt)
            ending_tests = ending_result.scalars().all()
            
            for test in ending_tests:
                try:
                    # Get candidate statistics
                    total_candidates_stmt = select(func.count(CandidateApplication.application_id)).where(
                        CandidateApplication.test_id == test.test_id
                    )
                    total_count_result = await session.execute(total_candidates_stmt)
                    total_candidates = total_count_result.scalar()
                    
                    shortlisted_candidates_stmt = select(func.count(CandidateApplication.application_id)).where(
                        and_(
                            CandidateApplication.test_id == test.test_id,
                            CandidateApplication.is_shortlisted == True
                        )
                    )
                    shortlisted_count_result = await session.execute(shortlisted_candidates_stmt)
                    shortlisted_candidates = shortlisted_count_result.scalar()
                    
                    repo = TestRepository(session)
                    await repo.update_test_status(test.test_id, TestStatus.ENDED.value)
                    logger.info(f"[Scheduler] Test {test.test_id} moved to ENDED ({total_candidates} total, {shortlisted_candidates} shortlisted)")
                    await self.log_scheduler_event(
                        "live_to_ended", 
                        test.test_id, 
                        f"Test ended with {total_candidates} total candidates, {shortlisted_candidates} shortlisted"
                    )
                    
                except Exception as e:
                    logger.error(f"[Scheduler] Failed to end test {test.test_id}: {e}")
                    await self.log_scheduler_event(
                        "live_to_ended", 
                        test.test_id, 
                        f"Failed to end test: {str(e)}", 
                        "error"
                    )
                    
        except Exception as e:
            logger.error(f"[Scheduler] Error in LIVE→ENDED transition: {e}")

    async def handle_scheduled_to_ended_transition(self, session):
        """End SCHEDULED tests if assessment deadline passes before scheduled time"""
        try:
            now = datetime.now(timezone.utc)
            
            expired_scheduled_stmt = select(Test).where(
                and_(
                    Test.status == TestStatus.SCHEDULED.value,
                    Test.assessment_deadline <= now
                )
            )
            expired_result = await session.execute(expired_scheduled_stmt)
            expired_tests = expired_result.scalars().all()
            
            for test in expired_tests:
                try:
                    repo = TestRepository(session)
                    await repo.update_test_status(test.test_id, TestStatus.ENDED.value)
                    logger.warning(f"[Scheduler] Test {test.test_id} moved to ENDED (expired before going live)")
                    await self.log_scheduler_event(
                        "scheduled_to_ended", 
                        test.test_id, 
                        "Test expired before going live - assessment deadline passed"
                    )
                    
                except Exception as e:
                    logger.error(f"[Scheduler] Failed to expire test {test.test_id}: {e}")
                    
        except Exception as e:
            logger.error(f"[Scheduler] Error in SCHEDULED→ENDED transition: {e}")

    async def cleanup_stale_tests(self, session):
        """Handle edge cases and cleanup stale test states"""
        try:
            now = datetime.now(timezone.utc)
            
            # Find tests that have been in PREPARING state for too long (over 1 hour)
            stale_preparing_stmt = select(Test).where(
                and_(
                    Test.status == TestStatus.PREPARING.value,
                    Test.updated_at <= now - timedelta(hours=1)
                )
            )
            stale_result = await session.execute(stale_preparing_stmt)
            stale_tests = stale_result.scalars().all()
            
            for test in stale_tests:
                logger.warning(f"[Scheduler] Found stale PREPARING test {test.test_id}, moving to DRAFT")
                repo = TestRepository(session)
                await repo.update_test_status(test.test_id, TestStatus.DRAFT.value, is_published=False)
                await self.log_scheduler_event(
                    "cleanup_stale", 
                    test.test_id, 
                    "Cleaned up stale PREPARING test (>1 hour old)"
                )
                
        except Exception as e:
            logger.error(f"[Scheduler] Error in cleanup: {e}")

    async def update_test_states(self):
        """Main scheduler function - handles all test state transitions"""
        start_time = datetime.now(timezone.utc)
        logger.info(f"[Scheduler] Starting test state update cycle at {start_time}")
        
        try:
            async with AsyncSessionLocal() as session:
                # Handle all state transitions
                await self.handle_preparing_to_draft_transition(session)
                await self.handle_scheduled_to_live_transition(session)
                await self.handle_live_to_ended_transition(session)
                await self.handle_scheduled_to_ended_transition(session)
                await self.cleanup_stale_tests(session)
                
                # Commit all changes
                await session.commit()
                
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()
            logger.info(f"[Scheduler] Completed test state update cycle in {duration:.2f}s")
            
        except Exception as e:
            logger.error(f"[Scheduler] Critical error in update cycle: {e}")
            try:
                await self.log_scheduler_event(
                    "critical_error", 
                    0, 
                    f"Critical scheduler error: {str(e)}", 
                    "error"
                )
            except:
                pass  # Don't fail if logging fails

    async def run(self):
        """Run the scheduler continuously"""
        scheduler = AsyncIOScheduler()
        scheduler.add_job(
            self.update_test_states, 
            'interval', 
            seconds=self.check_interval,
            max_instances=1  # Prevent overlapping runs
        )
        scheduler.start()
        
        logger.info(f"[Scheduler] Started enhanced test state manager (check interval: {self.check_interval}s)")
        logger.info(f"[Scheduler] PREPARING→DRAFT timeout: {self.preparing_timeout_minutes} minutes")
        
        try:
            while True:
                await asyncio.sleep(3600)  # Keep main thread alive
        except (KeyboardInterrupt, SystemExit):
            logger.info("[Scheduler] Shutting down...")
            scheduler.shutdown()

async def main():
    """Main entry point"""
    scheduler = TestScheduler(check_interval_seconds=10)  # Check every 10 seconds
    await scheduler.run()

if __name__ == "__main__":
    asyncio.run(main())
