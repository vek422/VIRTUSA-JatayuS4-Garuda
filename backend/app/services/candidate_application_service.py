import os
import tempfile
import requests
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.candidate_application_repo import CandidateApplicationRepository
from app.repositories.test_repo import get_test_by_id
from app.models.candidate_application import CandidateApplication
from app.models.assessment import Assessment
from app.schemas.candidate_application_schema import (
    CandidateApplicationCreate, CandidateApplicationBulkCreate,
    CandidateApplicationResponse, CandidateApplicationBulkResponse,
    CandidateApplicationSummaryResponse
)
from datetime import datetime
from app.services.ai_screening_service import AIScreeningService
from sqlalchemy import insert
from app.repositories.assessment_repo import AssessmentRepository
from app.repositories.user_repo import get_user_by_email, create_user
from app.models.user import User, UserRole
from app.core.security import get_password_hash
import random
import string
from app.services.notification_service import NotificationService
from app.services.auth.auth_service import get_current_user


class CandidateApplicationService:
    async def process_bulk_applications(self, db: AsyncSession, bulk_data: CandidateApplicationBulkCreate, current_user: User = None) -> CandidateApplicationBulkResponse:
        results = []
        success = 0
        failed = 0
        for app in bulk_data.applications:
            try:
                result = await self.process_single_application(db, app, current_user)
                if "error" in result:
                    failed += 1
                else:
                    success += 1
                results.append(result)
            except Exception as e:
                results.append({"error": str(e)})
                failed += 1
        return CandidateApplicationBulkResponse(results=results, total=len(bulk_data.applications), success=success, failed=failed)

    async def get_applications_summary_by_test_id(self, db: AsyncSession, test_id: int) -> List[CandidateApplicationSummaryResponse]:
        applications = await CandidateApplicationRepository.get_applications_by_test_id_with_user(db, test_id)
        response_list = []
        for app in applications:
            app_dict = {
                "application_id": app.application_id,
                "user_id": app.user_id,
                "test_id": app.test_id,
                "resume_link": app.resume_link,
                "resume_score": app.resume_score,
                "is_shortlisted": app.is_shortlisted,
                "candidate_name": app.user.name if app.user else None,
                "candidate_email": app.user.email if app.user else None,
                "screening_status": app.screening_status,

            }
            response_list.append(
                CandidateApplicationSummaryResponse(**app_dict))
        return response_list

    def __init__(self):
        self.ai_service = AIScreeningService()

    # ...existing code for __init__ ...

    async def process_single_application(self, db: AsyncSession, data: CandidateApplicationCreate, current_user: User = None) -> Dict[str, Any]:
        # Check or create user by email
        sanitized_email = data.email.replace("mailto:", "")
        print(f"[DEBUG] Using sanitized email: {sanitized_email}")
        user = await get_user_by_email(db, sanitized_email)
        generated_password = None
        if not user:
            # Use safe characters only - avoid ambiguous and HTML-problematic characters
            safe_chars = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
            # Remove ambiguous characters
            safe_chars = ''.join(c for c in safe_chars if c not in '0O1lI')
            generated_password = ''.join(random.choices(safe_chars, k=12))
            print(f"[DEBUG] Generated password for {sanitized_email}: {generated_password}")
            hashed_password = get_password_hash(generated_password)
            print(f"[DEBUG] Password hashed successfully for {sanitized_email}")
            name = data.name or sanitized_email.split('@')[0]
            new_user = await create_user(db, name=name, email=sanitized_email, hashed_password=hashed_password, role=UserRole.candidate)
            user_id = new_user.user_id
            print(f"[DEBUG] User created successfully with ID: {user_id}")
            
            # Test password verification immediately after creation
            from app.core.security import verify_password
            verification_test = verify_password(generated_password, hashed_password)
            print(f"[DEBUG] Immediate password verification test: {verification_test}")
            
            NotificationService().send_account_creation_email(
                to_email=sanitized_email,
                username=sanitized_email,
                password=generated_password
            )
            print(f"[DEBUG] Account creation email sent to {sanitized_email}")
        else:
            user_id = user.user_id
        # Check for duplicate
        existing = await CandidateApplicationRepository.get_by_user_and_test(db, user_id, data.test_id)
        if existing:
            return {"error": "Application already exists for this user and test."}
        # Fetch JD/skill graph from test table
        test = await get_test_by_id(db, data.test_id)
        if not test:
            return {"error": "Test not found."}
        if test.status == "draft":
            from app.repositories.test_repo import TestRepository
            await TestRepository(db).update_test_status(test.test_id, "preparing")
        # Prepare DB data (no screening yet)
        app_data = data.dict()
        app_data["user_id"] = user_id
        app_data.pop("email", None)
        app_data.pop("name", None)
        app_data.update({
            "resume_text": None,
            "parsed_resume": None,
            "resume_score": None,
            "skill_match_percentage": None,
            "experience_score": None,
            "education_score": None,
            "ai_reasoning": None,
            "is_shortlisted": False,
            "applied_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "screening_completed_at": None,
            "screening_status": "pending"})
        application = await CandidateApplicationRepository.create_application(db, app_data)
        if current_user:
            print(f"[DEBUG] Logging candidate application creation: actor_id={current_user.user_id}, role={getattr(current_user, 'role', None)}")
        else:
            print(f"[DEBUG] Logging candidate application creation: actor_id={user_id} (no current_user)")
        from app.services.logging import log_major_event
        actor_id = str(current_user.user_id) if current_user else str(user_id)
        await log_major_event(
            action="candidate_application_created",
            status="success",
            user=actor_id,
            details=f"Candidate application created for test {application.test_id}.",
            entity=str(application.application_id)
        )

        print(
            f"Creating a celery task for screening application: {application.application_id}")

        # Queue screening job to Celery (non-blocking)
        try:
            print(f"[DEBUG] Attempting to import celery_app...")
            from celery_app import screen_resume_task
            print(f"[DEBUG] Successfully imported screen_resume_task")
            print(
                f"[DEBUG] Queuing screening task for application ID: {application.application_id}")

            screen_resume_task.delay(application.application_id, data.resume_link,
                                     test.job_description, test.resume_score_threshold if test.auto_shortlist else None)
            print(f"[DEBUG] Task queued successfully!")

        except Exception as e:
            print(f"[ERROR] Failed to import/queue celery task: {e}")
            import traceback
            traceback.print_exc()
            # Continue without queuing the task
            print(f"[WARNING] Skipping Celery task due to error")

        # Prepare response
        response_dict = {
            "application_id": application.application_id,
            "user_id": application.user_id,
            "test_id": application.test_id,
            "resume_link": application.resume_link,
            "resume_text": application.resume_text,
            "parsed_resume": application.parsed_resume,
            "resume_score": application.resume_score,
            "skill_match_percentage": application.skill_match_percentage,
            "experience_score": application.experience_score,
            "education_score": application.education_score,
            "ai_reasoning": application.ai_reasoning,
            "is_shortlisted": application.is_shortlisted,
            "shortlist_reason": application.shortlist_reason,
            "screening_completed_at": application.screening_completed_at,
            "notified_at": application.notified_at,
            "applied_at": application.applied_at,
            "updated_at": application.updated_at,
            "screening_status": application.screening_status if hasattr(application, "screening_status") else "pending",
            "candidate_name": data.name or sanitized_email.split('@')[0],
            "candidate_email": sanitized_email
        }
        if generated_password:
            response_dict["generated_password"] = generated_password
        return response_dict

    async def get_single_application_with_user(self, db: AsyncSession, application_id: int) -> Optional[CandidateApplicationResponse]:
        application = await CandidateApplicationRepository.get_application_with_user_by_id(db, application_id)
        if not application:
            return None
        return CandidateApplicationResponse(
            application_id=application.application_id,
            user_id=application.user_id,
            test_id=application.test_id,
            resume_link=application.resume_link,
            resume_text=application.resume_text,
            parsed_resume=application.parsed_resume,
            resume_score=application.resume_score,
            skill_match_percentage=application.skill_match_percentage,
            experience_score=application.experience_score,
            education_score=application.education_score,
            ai_reasoning=application.ai_reasoning,
            is_shortlisted=application.is_shortlisted,
            shortlist_reason=application.shortlist_reason,
            screening_completed_at=application.screening_completed_at,
            notified_at=application.notified_at,
            applied_at=application.applied_at,
            updated_at=application.updated_at,
            candidate_name=application.user.name,
            candidate_email=application.user.email,
            screening_status=application.screening_status
        )

    async def shortlist_bulk_candidates(self, db: AsyncSession, test_id: int, min_score: int):
        from app.repositories.candidate_application_repo import CandidateApplicationRepository
        from app.services.notification_service import NotificationService
        applications = await CandidateApplicationRepository.get_applications_by_test_id_with_user(db, test_id)
        shortlisted = []
        notified_count = 0
        for app in applications:
            should_shortlist = app.resume_score is not None and app.resume_score >= min_score
            was_shortlisted = app.is_shortlisted
            app.is_shortlisted = should_shortlist
            db.add(app)
            if should_shortlist:
                shortlisted.append({
                    "candidate_email": app.user.email if app.user else None,
                    "resume_score": app.resume_score
                })
                if not was_shortlisted:
                    try:
                        await NotificationService.notify_candidate_shortlisted(db, app)
                        notified_count += 1
                    except Exception:
                        pass
        await db.commit()
        from app.services.logging import log_major_event
        await log_major_event(
            action="candidate_screening_done",
            status="success",
            user="system",
            details=f"Bulk candidate screening done for test {test_id}.",
            entity=str(test_id)
        )
        return {
            "shortlisted": shortlisted,
            "notified": notified_count,
            "message": f"{notified_count} candidates shortlisted and notified."
        }
