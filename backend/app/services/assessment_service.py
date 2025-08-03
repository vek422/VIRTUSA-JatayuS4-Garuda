"""
Assessment Service - Business logic for assessment operations including report generation
"""

from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.assessment_repo import AssessmentRepository
from app.models.assessment import AssessmentStatus
from app.services.report_generation_service import report_generation_service
import logging

logger = logging.getLogger(__name__)


class AssessmentService:
    """Service class for assessment business logic"""

    def __init__(self):
        pass

    async def generate_assessment_report(self, assessment_id: int, db: AsyncSession) -> Dict[str, Any]:
        """
        Generate assessment report - checks if assessment is completed first
        Returns existing report if already generated

        Args:
            assessment_id: Assessment ID to generate report for
            db: Database session

        Returns:
            Dict containing report data and metadata

        Raises:
            ValueError: If assessment not completed
            FileNotFoundError: If assessment not found
            Exception: If report generation fails
        """
        # TODO: Implement this method
        # 1. Check if assessment exists
        # 2. Validate assessment status is "completed"
        # 3. Check if report already exists (return existing if found)
        # 4. Fetch assessment with all related data
        # 5. Prepare ReportState from assessment data
        # 6. Call LangGraph to generate report
        # 7. Store report JSON in assessment.report field
        # 8. Return generated report

        repo = AssessmentRepository(db)

        # Get assessment with relations
        assessment_data = await repo.get_assessment_with_relations(assessment_id)
        if not assessment_data:
            raise FileNotFoundError(f"Assessment {assessment_id} not found")

        # Check if assessment is completed
        assessment_status = assessment_data["assessment"]["status"]
        if assessment_status != AssessmentStatus.COMPLETED.value:
            raise ValueError(
                f"Assessment must be completed before generating report. Current status: {assessment_status}")

        # Check if report already exists
        existing_report = assessment_data["assessment"]["report"]
        if existing_report:
            return {
                "assessment_id": assessment_id,
                "report_generated": True,
                "generated_at": assessment_data["assessment"]["updated_at"],
                "report": existing_report,
                "message": "Report already exists"
            }

        # Generate new report using ReportGenerationService
        try:
            logger.info(
                f"Generating new report for assessment {assessment_id}")
            report_result = await report_generation_service.generate_assessment_report(
                assessment_id, db
            )
            logger.info(
                f"Successfully generated report for assessment {assessment_id}")
            return report_result

        except Exception as e:
            logger.error(
                f"Failed to generate report for assessment {assessment_id}: {str(e)}", exc_info=True)
            raise Exception(f"Report generation failed: {str(e)}")

    async def get_assessment_report(self, assessment_id: int, db: AsyncSession) -> Optional[Dict[str, Any]]:
        """
        Get assessment report - returns None if not generated

        Args:
            assessment_id: Assessment ID to get report for
            db: Database session

        Returns:
            Dict with report data or None if not found
        """
        repo = AssessmentRepository(db)
        return await repo.get_assessment_report(assessment_id)


# Global service instance
assessment_service = AssessmentService()
