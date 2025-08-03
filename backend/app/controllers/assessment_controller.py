from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.repositories.assessment_repo import AssessmentRepository
from app.repositories.candidate_application_repo import CandidateApplicationRepository
from app.services.assessment_service import assessment_service
from sqlalchemy import select
from app.models.test import Test
from typing import Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/tests/{test_id}/assessment/add-candidate")
async def add_candidate_to_assessment(test_id: int, candidate_id: int, db: AsyncSession = Depends(get_db)):
    repo = AssessmentRepository(db)
    # Check if already exists
    existing = await repo.get_assessment_by_test_and_candidate(test_id, candidate_id)
    if existing:
        raise HTTPException(
            status_code=400, detail="Candidate already added to assessment for this test.")
    assessment = await repo.create_assessment(test_id=test_id, candidate_id=candidate_id)
    return {
        "assessment_id": assessment.assessment_id,
        "test_id": assessment.test_id,
        "candidate_id": assessment.candidate_id,
        "created_at": assessment.created_at,
        "message": "Candidate successfully added to assessment."
    }


@router.post("/{test_id}/shortlisted/assessments")
async def add_shortlisted_to_assessments(test_id: int, db: AsyncSession = Depends(get_db)):
    applications = await CandidateApplicationRepository.get_applications_by_test_id(db, test_id)
    shortlisted_apps = [app for app in applications if app.is_shortlisted]
    count = len(shortlisted_apps)
    if count == 0:
        raise HTTPException(
            status_code=404, detail="No shortlisted candidates found.")
    await AssessmentRepository.bulk_create_assessments(db, shortlisted_apps, test_id)
    return {
        "test_id": test_id, 
        "shortlisted_count": count,
        "message": f"{count} shortlisted candidates added to assessments table."
    }


@router.get("/candidates/{candidate_id}/assessments")
async def get_assessments_for_candidate(candidate_id: int, db: AsyncSession = Depends(get_db)):
    assessments = await AssessmentRepository.get_assessments_by_candidate(db, candidate_id)
    response = []
    for a in assessments:
        test = None
        if a.test_id:
            result = await db.execute(select(Test).where(Test.test_id == a.test_id))
            test = result.scalar_one_or_none()
        response.append({
            "assessment_id": a.assessment_id,
            "test_id": a.test_id,
            "created_at": a.created_at,
            "test_name": test.test_name if test else None,
            "job_description": test.job_description if test else None,
            "scheduled_at": test.scheduled_at if test else None,
            "assessment_deadline": test.assessment_deadline if test else None,
            "status": test.status if test else None
        })
    return response


@router.post("/assessments/{assessment_id}/generate-report")
async def generate_assessment_report(assessment_id: int, db: AsyncSession = Depends(get_db)):
    """Generate assessment report endpoint"""
    try:
        result = await assessment_service.generate_assessment_report(assessment_id, db)

        return {
            "success": True,
            "data": result
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate report: {str(e)}")


@router.get("/assessments/{assessment_id}/report")
async def get_assessment_report(assessment_id: int, db: AsyncSession = Depends(get_db)):
    """Get assessment report endpoint"""
    try:
        result = await assessment_service.get_assessment_report(assessment_id, db)

        if result is None:
            raise HTTPException(
                status_code=404, detail="Assessment or report not found")

        return {
            "success": True,
            "data": result
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve report: {str(e)}")


@router.get("/{test_id}/assessments")
async def get_assessments_by_test_id(
    test_id: int,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    page_size: int = Query(
        10, ge=1, le=100, description="Number of items per page"),
    status: Optional[str] = Query(
        None, description="Filter by assessment status (completed, in_progress)")
):
    """
    Get paginated assessments for a specific test ID with candidate information

    Args:
        test_id: Test ID to get assessments for
        page: Page number (starts from 1)
        page_size: Number of items per page (1-100)
        status: Optional filter by assessment status

    Returns:
        Paginated list of assessments with candidate details including:
        - candidate name and email
        - assessment status
        - percentage score
        - time taken
        - timestamps
        - pagination metadata
    """
    try:
        repo = AssessmentRepository(db)

        # Calculate skip value for pagination
        skip = (page - 1) * page_size

        # Get paginated assessments
        result = await repo.get_assessments_by_test_id_paginated(
            test_id=test_id,
            skip=skip,
            limit=page_size,
            status_filter=status
        )

        assessments = result["assessments"]
        pagination_info = result["pagination"]

        if not assessments:
            return {
                "test_id": test_id,
                "total_assessments": 0,
                "assessments": [],
                "pagination": pagination_info,                "summary": {
                    "completed": 0,
                    "in_progress": 0,
                    "average_score": None
                },
                "message": "No assessments found for this test"
            }

        # Format the response for frontend table display
        formatted_assessments = []
        for assessment in assessments:
            # Format time taken for display
            time_taken_display = None
            if assessment["time_taken_seconds"]:
                minutes = int(assessment["time_taken_seconds"] // 60)
                seconds = int(assessment["time_taken_seconds"] % 60)
                time_taken_display = f"{minutes}m {seconds}s"

            # Format percentage score
            score_display = f"{assessment['percentage_score']:.1f}%" if assessment['percentage_score'] is not None else "N/A"

            formatted_assessment = {
                "assessment_id": assessment["assessment_id"],
                "candidate_id": assessment["candidate_id"],
                "candidate_name": assessment["candidate_name"],
                "candidate_email": assessment["candidate_email"],
                "status": assessment["status"],
                "percentage_score": assessment["percentage_score"],
                "score_display": score_display,
                "time_taken_seconds": assessment["time_taken_seconds"],
                "time_taken_display": time_taken_display,
                "start_time": assessment["start_time"],
                "end_time": assessment["end_time"],
                "created_at": assessment["created_at"],
                "updated_at": assessment["updated_at"]
            }
            # Calculate summary statistics (for current page)
            formatted_assessments.append(formatted_assessment)
        completed_count = len(
            [a for a in formatted_assessments if a["status"] == "completed"])
        in_progress_count = len(
            [a for a in formatted_assessments if a["status"] == "in_progress"])

        # Calculate average score for assessments with scores
        scores = [a["percentage_score"]
                  for a in formatted_assessments if a["percentage_score"] is not None]
        average_score = sum(scores) / len(scores) if scores else None

        return {
            "test_id": test_id,
            "total_assessments": pagination_info["total_count"],
            "assessments": formatted_assessments,
            "pagination": {
                "current_page": pagination_info["current_page"],
                "total_pages": pagination_info["total_pages"],
                "page_size": pagination_info["page_size"],
                "total_count": pagination_info["total_count"],
                "has_next": pagination_info["has_next"],
                "has_previous": pagination_info["has_previous"],
                "next_page": pagination_info["current_page"] + 1 if pagination_info["has_next"] else None,
                "previous_page": pagination_info["current_page"] - 1 if pagination_info["has_previous"] else None
            },            "summary": {
                "page_completed": completed_count,
                "page_in_progress": in_progress_count,
                "page_average_score": average_score,
                "page_size": len(formatted_assessments)
            },
            "filters": {
                "status": status
            }
        }

    except Exception as e:
        logger.error(
            f"Error fetching paginated assessments for test {test_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch assessments: {str(e)}"
        )
