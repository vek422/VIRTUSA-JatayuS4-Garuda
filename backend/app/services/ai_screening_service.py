import os
import json
import re
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from app.services.resume_screening import resume_screening_graph
from app.services.resume_screening.graph import State as ResumeScreeningState
try:
    from PyPDF2 import PdfReader
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    from openai import OpenAI
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

class AIScreeningService:
    """Service for AI-powered resume screening and job matching using notebook logic"""
    # Interface for resume-related tasks
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.ai_enabled = bool(self.api_key and self.api_key != "your-openai-api-key-here" and AI_AVAILABLE)
        if self.ai_enabled:
            self.client = OpenAI(api_key=self.api_key)
        # ...existing code...

    def extract_text_from_file(self, file_path: str) -> str:
        if not file_path or not os.path.exists(file_path):
            return "Error: File path is invalid or file does not exist"
        try:
            ext = os.path.splitext(file_path)[1].lower()
            if ext == '.pdf' and PDFPLUMBER_AVAILABLE:
                with pdfplumber.open(file_path) as pdf:
                    text = "\n".join(page.extract_text() or "" for page in pdf.pages)
                return text.strip() or "No text extracted from PDF"
            elif ext in ['.docx', '.doc'] and DOCX_AVAILABLE:
                doc = Document(file_path)
                text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
                return text.strip() or "No text extracted from DOCX file"
            else:
                return f"Unsupported file type: {ext}"
        except Exception as e:
            return f"Error extracting text: {e}"

    def screen_resume_text(self, resume_text: str, job_description: str, parsed_job_description: Optional[dict] = None, skill_graph: Optional[dict] = None, min_resume_score: Optional[int] = None) -> Dict[str, Any]:
        from app.services.resume_screening import resume_screening_graph
        from app.services.resume_screening.graph import State as ResumeScreeningState
        jd_struct = parsed_job_description if parsed_job_description else {"raw_job_description": job_description}
        state = ResumeScreeningState(parsed_jd=jd_struct, resume=resume_text)
        result_state = resume_screening_graph.invoke(state)
        if isinstance(result_state, dict):
            result_state = ResumeScreeningState(**result_state)
        result = result_state.screening_result
        # Ensure all expected fields are present
        default_fields = {
            "resume_score": None,
            "skill_match_percentage": None,
            "experience_score": None,
            "education_score": None,
            "ai_reasoning": None,
            "is_shortlisted": False,
            "shortlist_reason": None,
        }
        output = result.model_dump() if hasattr(result, "model_dump") else dict(result) if result else {}
        for k, v in default_fields.items():
            output.setdefault(k, v)
        output["error"] = result_state.error
        
        # Map match_score to resume_score for consistency
        if output.get("match_score") is not None:
            output["resume_score"] = output.get("match_score")
        
        # Auto shortlisting logic based on resume score threshold
        print(f"[AUTO-SHORTLIST-DEBUG] min_resume_score={min_resume_score}, match_score={output.get('match_score')}, resume_score={output.get('resume_score')}")
        
        if min_resume_score is not None and output.get("match_score") is not None:
            resume_score = output.get("match_score")
            print(f"[AUTO-SHORTLIST-DEBUG] Comparing: {resume_score} >= {min_resume_score} = {resume_score >= min_resume_score}")
            
            if resume_score >= min_resume_score:
                output["is_shortlisted"] = True
                output["shortlist_reason"] = f"Auto-shortlisted: Resume score {resume_score} meets threshold {min_resume_score}"
                print(f"[AUTO-SHORTLIST] ✅ Candidate shortlisted: score={resume_score}, threshold={min_resume_score}")
                
                # Log the auto shortlisting decision
                try:
                    import asyncio
                    from app.services.logging import log_major_event
                    
                    def log_async():
                        return log_major_event(
                            action="candidate_auto_shortlisted",
                            status="success", 
                            user="system",
                            details=f"Candidate auto-shortlisted with resume score {resume_score} (threshold: {min_resume_score})",
                            entity="resume_screening"
                        )
                    
                    # Try to log but don't fail if logging fails
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            loop.create_task(log_async())
                        else:
                            asyncio.run(log_async())
                    except RuntimeError:
                        asyncio.run(log_async())  
                    print(f"[AUTO-SHORTLIST] ✅ Logged shortlisting decision")
                except Exception as e:
                    print(f"[WARNING] Failed to log auto-shortlisting: {e}")
            else:
                output["is_shortlisted"] = False
                output["shortlist_reason"] = f"Not shortlisted: Resume score {resume_score} below threshold {min_resume_score}"
                print(f"[AUTO-SHORTLIST] ❌ Candidate not shortlisted: score={resume_score}, threshold={min_resume_score}")
        else:
            print(f"[AUTO-SHORTLIST] ⏭️ Skipped - min_resume_score={min_resume_score}, match_score={output.get('match_score')}")
        
        return output

    def _parse_resume_basic(self, resume_text: str) -> Dict[str, Any]:
        return {
            "raw_text": resume_text,
            "parsed_at": datetime.now().isoformat()
        }
