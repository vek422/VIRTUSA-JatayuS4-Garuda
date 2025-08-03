from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert, select, update
from sqlalchemy.exc import SQLAlchemyError
from app.models.assessment import Assessment
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from app.models.user import User
import logging

logger = logging.getLogger(__name__)


class AssessmentRepository:
    """Repository for Assessment entity operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_assessment_instance(
        self,
        application_id: int,
        user_id: int,
        test_id: int
    ) -> Optional[int]:
        """
        Create a new assessment instance when a candidate starts taking a test

        Args:
            application_id: Candidate application ID
            user_id: User taking the assessment  
            test_id: Test blueprint ID

        Returns:
            assessment_id if successful, None otherwise
        """
        try:            # Create new assessment instance
            assessment = Assessment(
                application_id=application_id,
                user_id=user_id,
                test_id=test_id,
                status="in_progress",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )

            self.db.add(assessment)
            await self.db.commit()
            await self.db.refresh(assessment)

            # Get the actual ID value from the refreshed object
            assessment_id = getattr(assessment, 'assessment_id')
            from app.services.logging import log_major_event
            await log_major_event(
                action="assessment_created",
                status="success",
                user=str(user_id),
                details=f"Assessment instance created for test {test_id} and user {user_id}.",
                entity=str(assessment_id)
            )
            logger.info(
                f"Created assessment instance {assessment_id} for user {user_id}, test {test_id}")
            return assessment_id

        except SQLAlchemyError as e:
            logger.error(
                f"Database error creating assessment instance: {str(e)}")
            await self.db.rollback()
            return None
        except Exception as e:
            logger.error(f"Error creating assessment instance: {str(e)}")
            await self.db.rollback()
            return None

    async def get_assessment_by_id(self, assessment_id: int) -> Optional[Assessment]:
        """Get assessment by ID"""
        try:
            result = await self.db.execute(
                select(Assessment).where(
                    Assessment.assessment_id == assessment_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(
                f"Error fetching assessment {assessment_id}: {str(e)}")
            return None

    async def get_user_assessment_for_test(self, user_id: int, test_id: int) -> Optional[Assessment]:
        """Check if user already has an assessment instance for this test"""
        try:
            result = await self.db.execute(
                select(Assessment).where(
                    Assessment.user_id == user_id,
                    Assessment.test_id == test_id
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(
                f"Error checking existing assessment for user {user_id}, test {test_id}: {str(e)}")
            return None

    async def update_assessment_status(
        self,
        assessment_id: int,
        status: str,
        percentage_score: float,
        end_time: Optional[datetime] = None,
        result: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update assessment with completion status and results

        Args:
            assessment_id: The assessment ID to update
            status: Assessment status string (e.g., "completed")
            percentage_score: Final percentage score for the assessment
            end_time: Optional end time for the assessment

        Returns:
            bool: True if update was successful, False otherwise
        """
        try:            # Prepare update values
            update_values = {
                "status": status,
                "percentage_score": percentage_score,
                "updated_at": datetime.now(timezone.utc),
                "result": result
            }

            # Add end_time if provided
            if end_time:
                update_values["end_time"] = end_time

            # Update assessment record using SQLAlchemy update statement
            stmt = update(Assessment).where(
                Assessment.assessment_id == assessment_id
            ).values(**update_values)

            result = await self.db.execute(stmt)
            await self.db.commit()

            return result.rowcount > 0

        except Exception as e:
            logger.error(
                f"Error updating assessment {assessment_id}: {str(e)}")
            await self.db.rollback()
            return False

    @staticmethod
    async def insert_assessment(db: AsyncSession, application_id: int, user_id: int, test_id: int):
        """Legacy method - kept for backward compatibility"""
        stmt = insert(Assessment).values(
            application_id=application_id,
            user_id=user_id,
            test_id=test_id,
            created_at=datetime.now(timezone.utc)
        )
        await db.execute(stmt)
        await db.commit()

    @staticmethod
    async def bulk_create_assessments(db: AsyncSession, applications: list, test_id: int):
        from sqlalchemy import select
        for app in applications:
            user_id = app.user_id
            application_id = app.application_id
            exists = await db.execute(
                select(Assessment).where(Assessment.user_id ==
                                         user_id, Assessment.test_id == test_id)
            )
            if not exists.scalar():
                stmt = insert(Assessment).values(user_id=user_id,
                                                 test_id=test_id, application_id=application_id)
                await db.execute(stmt)
        await db.commit()

    @staticmethod
    async def get_assessments_by_candidate(db: AsyncSession, user_id: int):
        from sqlalchemy import select
        result = await db.execute(
            select(Assessment).where(Assessment.user_id == user_id)
        )
        return result.scalars().all()

    async def is_assessment_completed(self, user_id: int, test_id: int) -> bool:
        """
        Check if user already has a completed assessment for this test

        Args:
            user_id: User ID to check
            test_id: Test ID to check        Returns:
            bool: True if user has a completed assessment, False otherwise
        """
        try:
            from app.models.assessment import AssessmentStatus

            result = await self.db.execute(
                select(Assessment).where(
                    Assessment.user_id == user_id,
                    Assessment.test_id == test_id,
                    Assessment.status == AssessmentStatus.COMPLETED.value
                )
            )
            completed_assessment = result.scalar_one_or_none()
            return completed_assessment is not None

        except Exception as e:
            logger.error(
                f"Error checking completed assessment for user {user_id}, test {test_id}: {str(e)}")
            return False

    async def get_assessment_with_relations(self, assessment_id: int) -> Optional[Dict[str, Any]]:
        """
        Get assessment with test, user, application, and candidate data for report generation

        Args:
            assessment_id: Assessment ID to fetch with relations

        Returns:
            Dict containing assessment and all related data, None if not found
        """
        try:
            from sqlalchemy.orm import selectinload
            from app.models.candidate_application import CandidateApplication
            from app.models.test import Test
            from app.models.user import User

            # Get assessment with all related data
            result = await self.db.execute(
                select(Assessment)
                .options(
                    selectinload(Assessment.application),
                    selectinload(Assessment.test),
                    selectinload(Assessment.user)
                )
                .where(Assessment.assessment_id == assessment_id)
            )
            assessment = result.scalar_one_or_none()

            if not assessment:
                return None

            # Convert to dictionary with all related data
            assessment_data = {
                "assessment": {
                    "assessment_id": assessment.assessment_id,
                    "status": getattr(assessment, 'status', None),
                    "percentage_score": getattr(assessment, 'percentage_score', None),
                    "start_time": getattr(assessment, 'start_time', None),
                    "end_time": getattr(assessment, 'end_time', None),
                    "created_at": getattr(assessment, 'created_at', None),
                    "updated_at": getattr(assessment, 'updated_at', None),
                    "report": getattr(assessment, 'report', None)
                },
                "test": {
                    "test_id": assessment.test.test_id if assessment.test else None,
                    "test_name": getattr(assessment.test, 'test_name', None) if assessment.test else None,
                    "parsed_job_description": getattr(assessment.test, 'parsed_job_description', None) if assessment.test else None,
                    "skill_graph": getattr(assessment.test, 'skill_graph', None) if assessment.test else None
                },                "user": {
                    "user_id": assessment.user.user_id if assessment.user else None,
                    "name": getattr(assessment.user, 'name', None) if assessment.user else None,
                    "email": getattr(assessment.user, 'email', None) if assessment.user else None
                },
                "application": {
                    "application_id": assessment.application.application_id if assessment.application else None,
                    "parsed_resume": getattr(assessment.application, 'parsed_resume', None) if assessment.application else None
                }
            }

            return assessment_data

        except Exception as e:
            logger.error(
                f"Error fetching assessment with relations {assessment_id}: {str(e)}")
            return None

    async def update_assessment_report(self, assessment_id: int, report_data: Dict[str, Any]) -> bool:
        """
        Update assessment report field with generated JSON data

        Args:
            assessment_id: Assessment ID to update
            report_data: Generated report JSON data

        Returns:
            bool: True if update successful, False otherwise
        """
        try:            # Update assessment record with report data
            stmt = update(Assessment).where(
                Assessment.assessment_id == assessment_id
            ).values(
                report=report_data,
                updated_at=datetime.now(timezone.utc)
            )

            result = await self.db.execute(stmt)
            await self.db.commit()

            return result.rowcount > 0

        except Exception as e:
            logger.error(
                f"Error updating assessment report {assessment_id}: {str(e)}")
            await self.db.rollback()
            return False

    async def get_assessment_report(self, assessment_id: int) -> Optional[Dict[str, Any]]:
        """
        Get existing assessment report if available with candidate information

        Args:
            assessment_id: Assessment ID to get report for

        Returns:
            Dict containing report data with candidate name or None if not generated
        """
        try:

            # Query assessment report with candidate information
            query = (
                select(
                    Assessment.report,
                    Assessment.status,
                    Assessment.updated_at,
                    Assessment.result,
                    Assessment.user_id,
                    Assessment.percentage_score,
                    User.name.label('candidate_name'),
                    User.email.label('candidate_email')
                )
                .select_from(Assessment)
                .join(User, Assessment.user_id == User.user_id)
                .where(Assessment.assessment_id == assessment_id)
            )

            result = await self.db.execute(query)
            row = result.first()

            if not row:
                return None

            return {
                "assessment_id": assessment_id,
                "report": row.report,
                "status": row.status,
                "result": row.result,
                "report_generated": row.report is not None,
                "last_updated": row.updated_at,
                "candidate_id": row.user_id,
                "candidate_name": row.candidate_name,
                "candidate_email": row.candidate_email,
                "percentage_score": row.percentage_score
            }

        except Exception as e:
            logger.error(
                f"Error fetching assessment report {assessment_id}: {str(e)}")
            return None

    async def get_assessments_by_test_id(self, test_id: int) -> List[Dict[str, Any]]:
        """
        Get all assessments for a specific test ID with candidate information

        Args:
            test_id: Test ID to get assessments for
              Returns:
            List of assessment data with candidate information
        """
        try:
            from app.models.user import User
            # Query assessments with related candidate information
            from app.models.candidate_application import CandidateApplication
            query = (
                select(
                    Assessment.assessment_id,
                    Assessment.status,
                    Assessment.percentage_score,
                    Assessment.start_time,
                    Assessment.end_time,
                    Assessment.created_at,
                    Assessment.updated_at,
                    User.user_id,
                    User.name,
                    User.email,
                    CandidateApplication.application_id
                )
                .select_from(Assessment)
                .join(User, Assessment.user_id == User.user_id)
                .join(CandidateApplication, Assessment.application_id == CandidateApplication.application_id)                .where(Assessment.test_id == test_id)
            )

            result = await self.db.execute(query)
            rows = result.fetchall()

            assessments = []
            for row in rows:
                # Calculate time taken if both start and end times are available
                time_taken = None
                if row.start_time and row.end_time:
                    time_taken = (
                        row.end_time - row.start_time).total_seconds()

                assessment_data = {
                    "assessment_id": row.assessment_id,
                    "candidate_id": row.user_id,
                    "candidate_name": row.name,
                    "candidate_email": row.email,
                    # Default to in_progress since assessment exists
                    "status": row.status or "in_progress",
                    "percentage_score": row.percentage_score,
                    "start_time": row.start_time,
                    "end_time": row.end_time,
                    "time_taken_seconds": time_taken,
                    "created_at": row.created_at,
                    "updated_at": row.updated_at,
                    "application_id": row.application_id
                }
                assessments.append(assessment_data)

            return assessments

        except Exception as e:
            logger.error(
                f"Error fetching assessments for test {test_id}: {str(e)}")
            return []

    async def get_assessments_by_test_id_paginated(
        self,
        test_id: int,
        skip: int = 0,
        limit: int = 10,
        status_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get paginated assessments for a specific test ID with candidate information

        Args:
            test_id: Test ID to get assessments for
            skip: Number of records to skip (offset)
            limit: Maximum number of records to return
            status_filter: Optional filter by assessment status        Returns:
            Dictionary containing paginated assessment data and metadata
        """
        try:
            from app.models.user import User
            from app.models.candidate_application import CandidateApplication
            from sqlalchemy import func, desc, case

            # Base query for assessments with candidate information
            base_query = (
                select(
                    Assessment.assessment_id,
                    Assessment.status,
                    Assessment.percentage_score,
                    Assessment.start_time,
                    Assessment.end_time,
                    Assessment.created_at,
                    Assessment.updated_at,
                    User.user_id,
                    User.name,
                    User.email,
                    CandidateApplication.application_id
                )
                .select_from(Assessment)
                .join(User, Assessment.user_id == User.user_id)
                .join(CandidateApplication, Assessment.application_id == CandidateApplication.application_id)
                .where(Assessment.test_id == test_id)
            )

            # Apply status filter if provided
            if status_filter:
                base_query = base_query.where(
                    Assessment.status == status_filter)
              # Count total records
            count_query = select(func.count()).select_from(
                base_query.subquery()
            )
            total_result = await self.db.execute(count_query)
            total_count = total_result.scalar() or 0

            # Apply pagination and ordering
            paginated_query = (
                base_query                .order_by(
                    # Order by status priority: completed, in_progress
                    case(
                        (Assessment.status == 'completed', 1),
                        (Assessment.status == 'in_progress', 2),
                        else_=3
                    ),
                    # Then by score descending
                    desc(Assessment.percentage_score),
                    desc(Assessment.created_at)  # Then by creation time
                )
                .offset(skip)
                .limit(limit))

            result = await self.db.execute(paginated_query)
            rows = result.fetchall()

            assessments = []
            for row in rows:
                # Calculate time taken if both start and end times are available
                time_taken = None
                if row.start_time and row.end_time:
                    time_taken = (
                        row.end_time - row.start_time).total_seconds()

                assessment_data = {
                    "assessment_id": row.assessment_id,
                    "candidate_id": row.user_id,
                    "candidate_name": row.name,
                    "candidate_email": row.email,
                    # Default to in_progress since assessment exists
                    "status": row.status or "in_progress",
                    "percentage_score": row.percentage_score,
                    "start_time": row.start_time,
                    "end_time": row.end_time,
                    "time_taken_seconds": time_taken,
                    "created_at": row.created_at,
                    "updated_at": row.updated_at,
                    "application_id": row.application_id
                }
                assessments.append(assessment_data)

            # Calculate pagination metadata
            total_pages = (total_count + limit -
                           1) // limit  # Ceiling division
            current_page = (skip // limit) + 1
            has_next = skip + limit < total_count
            has_previous = skip > 0

            return {
                "assessments": assessments,
                "pagination": {
                    "total_count": total_count,
                    "total_pages": total_pages,
                    "current_page": current_page,
                    "page_size": limit,
                    "has_next": has_next,
                    "has_previous": has_previous,
                    "skip": skip,
                    "limit": limit
                }
            }

        except Exception as e:
            logger.error(
                f"Error fetching paginated assessments for test {test_id}: {str(e)}")
            return {
                "assessments": [],
                "pagination": {
                    "total_count": 0,
                    "total_pages": 0,
                    "current_page": 1,
                    "page_size": limit,
                    "has_next": False,
                    "has_previous": False,
                    "skip": skip,
                    "limit": limit
                }
            }
