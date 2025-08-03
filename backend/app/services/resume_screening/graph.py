"""
This graph is used to screen and evaluate resumes against job descriptions
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END, START
from langchain_openai import ChatOpenAI
import json


def get_llm():
    """Get LLM instance lazily to avoid initialization issues during import."""
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.1,
    )

# Define BaseModel for Resume Screening Results


class ScreeningResult(BaseModel):
    match_score: int = Field(
        ...,
        description="Overall match score from 0 to 100 based on how well the candidate fits the job requirements",
        ge=0,
        le=100
    )
    reason: str = Field(
        ...,
        description="Brief explanation of the score highlighting key strengths and weaknesses of the candidate"
    )
    experience_alignment_score: Optional[int] = Field(
        default=None,
        description="Score for experience alignment (0-100)",
        ge=0,
        le=100
    )
    skills_match_score: Optional[int] = Field(
        default=None,
        description="Score for required skills match (0-100)",
        ge=0,
        le=100
    )
    responsibility_match_score: Optional[int] = Field(
        default=None,
        description="Score for responsibility alignment (0-100)",
        ge=0,
        le=100
    )
    preferred_skills_score: Optional[int] = Field(
        default=None,
        description="Score for preferred skills coverage (0-100)",
        ge=0,
        le=100
    )
    certifications_score: Optional[int] = Field(
        default=None,
        description="Score for relevant certifications (0-100)",
        ge=0,
        le=100
    )
    project_impact_score: Optional[int] = Field(
        default=None,
        description="Score for project impact and relevance (0-100)",
        ge=0,
        le=100
    )
    education_score: Optional[int] = Field(
        default=None,
        description="Score for education alignment (0-100)",
        ge=0,
        le=100
    )
    extraction_uncertainties: Optional[List[str]] = Field(
        default_factory=list,
        description="Any uncertainties or missing information that affected the evaluation"
    )


# Resume screening prompt
RESUME_SCREENING_SYSTEM_PROMPT = """
You are an expert AI recruiter with deep experience in technical hiring and candidate evaluation.

Your task is to evaluate a candidate's resume against a specific job description and provide a comprehensive scoring analysis.

Evaluation Criteria and Weights:
- Experience alignment (35%): How well does the candidate's work experience match the role requirements?
- Required skills match (20%): Coverage of must-have technical skills mentioned in the JD
- Responsibility match (10%): Alignment between past responsibilities and job expectations
- Preferred skills (5%): Coverage of nice-to-have skills and qualifications
- Certifications (5%): Relevant professional certifications and credentials
- Education alignment (5%): How well does the candidate's education match the job requirements? (Provide a separate education_score)
- Soft skills (5%): Communication, leadership, teamwork abilities inferred from experience
- Project impact (10%): Quality and relevance of projects showcasing technical abilities
- Overall fit (5%): General alignment with company culture and role expectations

Instructions:
1. Analyze the resume thoroughly against the job description
2. Provide an overall match score from 0-100
3. Give a concise but informative reason explaining the score
4. Provide individual category scores for detailed breakdown, including education_score (0-100)
5. Note any missing information that could affect the evaluation
6. Be objective and fair in your assessment
7. Consider both strengths and areas of concern

Focus on technical fit, experience relevance, education alignment, and potential for success in the role.
"""


@dataclass
class Configuration:
    """Configuration for the resume screening graph."""
    model: str = "gpt-4o-mini"
    temperature: float = 0.1


@dataclass
class State:
    """State for the resume screening graph."""
    parsed_jd: Optional[Dict[str, Any]] = None
    resume: str = ""
    screening_result: Optional[ScreeningResult] = None
    error: Optional[str] = None


def evaluate_resume(state: State) -> State:
    """Evaluate resume against job description."""
    try:
        jd = state.parsed_jd
        resume = state.resume

        if not jd or not resume:
            return State(
                parsed_jd=state.parsed_jd,
                resume=state.resume,
                screening_result=None,
                error="Missing job description or resume data"
            )

        # Create the evaluation prompt
        evaluation_prompt = f"""
You are an expert AI recruiter.

Evaluate the following candidate resume against the given job description.

Use these weights:
- Experience alignment (35%)
- Required skills match (20%)
- Responsibility match (10%)
- Preferred skills (5%)
- Certifications (5%)
- Education alignment (5%)
- Soft skills (5%)
- Project impact (10%)
- Overall fit (5%)

Your task:
- Score the candidate from 0 to 100.
- Provide a brief explanation of the score highlighting key strengths and weaknesses.
- Consider both technical fit and experience relevance.
- Provide a field named education_score (0-100) for education alignment in your output.

Job Description:
{json.dumps(jd, indent=2)}

Resume:
{resume}
"""

        llm = get_llm()
        extractor_llm = llm.with_structured_output(ScreeningResult)

        messages = [
            {"role": "system", "content": RESUME_SCREENING_SYSTEM_PROMPT},
            {"role": "user", "content": evaluation_prompt}
        ]

        result = extractor_llm.invoke(messages)

        # Ensure we get a ScreeningResult instance
        if isinstance(result, dict):
            result = ScreeningResult(**result)

        return State(
            parsed_jd=state.parsed_jd,
            resume=state.resume,
            screening_result=result,
            error=None
        )

    except Exception as e:
        return State(
            parsed_jd=state.parsed_jd,
            resume=state.resume,
            screening_result=None,
            error=str(e)
        )


def create_resume_screening_graph():
    """Create the resume screening graph."""
    workflow = StateGraph(State)

    # Add nodes
    workflow.add_node("evaluate_resume", evaluate_resume)

    # Add edges
    workflow.add_edge(START, "evaluate_resume")
    workflow.add_edge("evaluate_resume", END)

    return workflow.compile()


# Export the graph
graph = create_resume_screening_graph()
