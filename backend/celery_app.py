
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from celery import Celery
from datetime import datetime
import asyncio
import os
import sys

from app import services
from app.repositories.candidate_application_repo import CandidateApplicationRepository
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

load_dotenv()
celery = Celery(
    "jatayu_tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_async_engine(DATABASE_URL, future=True)
AsyncSessionLocal = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession)


@celery.task
def screen_resume_task(application_id, resume_link, job_description, min_resume_score=None):
    import asyncio
    print("[Celery] Starting resume screening task for application_id:",
          application_id)

    async def process():
        from app.services.ai_screening_service import AIScreeningService
        from app.repositories.candidate_application_repo import CandidateApplicationRepository
        from app.models.candidate_application import CandidateApplication
        from app.models.assessment import Assessment
        import json
        import requests
        import tempfile
        import os
        from datetime import datetime

        service = AIScreeningService()
        async with AsyncSessionLocal() as db:
            resume_text = None
            try:
                if 'drive.google.com' in resume_link:
                    import re
                    match = re.search(r'/d/([\w-]+)', resume_link)
                    if match:
                        file_id = match.group(1)
                        download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
                    else:
                        return "Error: Invalid Google Drive link."
                else:
                    download_url = resume_link
                print("[Celery] Downloading resume from:",
                      download_url, flush=True)
                response = requests.get(
                    download_url, timeout=30, allow_redirects=True)
                response.raise_for_status()
                # Save to temp file (preserve extension if possible)
                ext = os.path.splitext(download_url)[-1] or '.pdf'
                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
                    tmp_file.write(response.content)
                    tmp_file_path = tmp_file.name
                resume_text = service.extract_text_from_file(tmp_file_path)
                print("[Celery] Extracted resume text:",
                      resume_text[:100], flush=True)
                os.remove(tmp_file_path)
            except Exception as e:
                resume_text = f"Error downloading or extracting resume: {e}"
            if not resume_text:
                return "Error: Resume text is empty or invalid."
            print(f"[Celery] Calling screen_resume_text with min_resume_score={min_resume_score}")
            screening_result = service.screen_resume_text(
                resume_text, job_description, min_resume_score=min_resume_score)
            print("[Celery] screening_result:", screening_result)
            if not screening_result:
                return "Error: Screening result is empty or invalid."
            update_data = {
                "resume_text": resume_text,
                "parsed_resume": json.dumps(service._parse_resume_basic(resume_text)),
                "resume_score": screening_result.get("match_score"),
                "skill_match_percentage": screening_result.get("skills_match_score"),
                "experience_score": screening_result.get("experience_alignment_score"),
                "education_score": screening_result.get("education_score", None),
                "ai_reasoning": screening_result.get("reason"),
                "is_shortlisted": screening_result.get("is_shortlisted", False),
                "shortlist_reason": screening_result.get("shortlist_reason", None),
                "screening_completed_at": datetime.utcnow(),
                "screening_status": "completed"
            }
            print("[Celery] update_data:", update_data)
            await CandidateApplicationRepository.update_application(db, application_id, update_data)

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(process())
        else:
            loop.run_until_complete(process())
    except RuntimeError:
        asyncio.run(process())
