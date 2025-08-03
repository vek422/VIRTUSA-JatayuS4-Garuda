from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime


class PerformanceSummary(BaseModel):
    total_score: float
    total_questions: int
    correct_answers: int
    passed_skills_H: int
    passed_skills_M: int
    passed_skills_L: int
    strengths: List[str]
    weaknesses: List[str]


class ReportState(BaseModel):
    candidate_name: Optional[str]
    parsed_resume: Optional[str] = None
    parsed_jd: str
    performance_summary: PerformanceSummary
    assessment_date: datetime
    # Input skills with scores and priorities
    skill_breakdown: List[Dict[str, Any]]

    # Enhanced fields for integrated analysis
    # skill -> priority level (H/M/L)
    skill_priorities: Optional[Dict[str, str]] = None
    # skills found in resume
    resume_skills_mentioned: Optional[List[str]] = None
    # skill -> {basic: 2, intermediate: 3, advanced: 1}
    question_difficulty_breakdown: Optional[Dict[str, Dict[str, int]]] = None
    # skill -> {priority: "H", depth: "advanced", required: true}
    jd_skill_requirements: Optional[Dict[str, Dict[str, Any]]] = None
    # skill -> validated_in_assessment
    resume_skill_validation: Optional[Dict[str, bool]] = None

    # Additional metadata for enhanced reporting
    assessment_metadata: Optional[Dict[str, Any]
                                  ] = None  # general assessment context
    # final generated report storage
    generated_report: Optional[Dict[str, Any]] = None
