from dataclasses import dataclass
from typing import List, Optional
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage


class EducationItem(BaseModel):
    degree: str = Field(
        ...,
        description="The degree, diploma, or educational qualification (e.g., 'Bachelor of Science in Computer Science', 'MBA', 'High School Diploma')"
    )
    institution: Optional[str] = Field(
        default=None,
        description="The name of the educational institution or school"
    )
    year: Optional[str] = Field(
        default=None,
        description="Year of graduation or completion, if mentioned"
    )


class ExperienceItem(BaseModel):
    title: str = Field(
        ...,
        description="Job title or position held (e.g., 'Software Developer', 'Data Analyst')"
    )
    company: Optional[str] = Field(
        default=None,
        description="Name of the company or organization"
    )
    duration: Optional[str] = Field(
        default=None,
        description="Duration of employment (e.g., '2019-2021', '2 years', 'Jan 2020 - Present')"
    )
    description: Optional[str] = Field(
        default=None,
        description="Brief description of responsibilities or achievements in this role"
    )


class ProjectItem(BaseModel):
    name: str = Field(
        ...,
        description="Name or title of the project"
    )
    description: Optional[str] = Field(
        default=None,
        description="Brief description of what the project involved or accomplished"
    )
    technologies: Optional[List[str]] = Field(
        default_factory=list,
        description="Technologies or tools used in the project"
    )


class ResumeFields(BaseModel):
    education: List[EducationItem] = Field(
        default_factory=list,
        description=(
            "List of educational qualifications, degrees, certifications, or academic credentials. "
            "Include formal education, online courses, bootcamps, or relevant training programs."
        )
    )
    experience: List[ExperienceItem] = Field(
        default_factory=list,
        description=(
            "List of work experiences including job titles, companies, duration, and responsibilities. "
            "Include full-time, part-time, internships, freelance, or volunteer work that's relevant."
        )
    )
    skills: List[str] = Field(
        default_factory=list,
        description=(
            "List of technical and professional skills mentioned in the resume. "
            "Include programming languages, tools, frameworks, soft skills, domain expertise, etc."
        )
    )
    projects: List[ProjectItem] = Field(
        default_factory=list,
        description=(
            "List of personal, academic, or professional projects that showcase technical abilities. "
            "Include project names, descriptions, and technologies used where available."
        )
    )
    certifications: List[str] = Field(
        default_factory=list,
        description=(
            "List of professional certifications, licenses, or additional qualifications. "
            "Include industry certifications, online course completions, or professional licenses."
        )
    )
    summary: Optional[str] = Field(
        default=None,
        description=(
            "Professional summary, objective, or profile section from the resume. "
            "A brief 2-4 sentence overview of the candidate's background and career goals."
        )
    )
    contact_info: Optional[str] = Field(
        default=None,
        description=(
            "Contact information if clearly mentioned (email, phone, LinkedIn, GitHub, etc.). "
            "Only extract if explicitly provided and relevant for professional purposes."
        )
    )
    extraction_uncertainties: List[str] = Field(
        default_factory=list,
        description=(
            "List of unclear, ambiguous, or missing information during extraction. "
            "Examples: 'Graduation year not mentioned', 'Company name unclear', 'Skills section not well-defined'"
        )
    )


# Resume parsing prompt - modified to work with structured output
RESUME_PARSING_SYSTEM_PROMPT = """
You are an expert resume analyzer. Extract structured information from the given resume text and organize it into the specified format.

Instructions:
1. Extract education information including degrees, institutions, and graduation years where available
2. Extract work experience with job titles, companies, duration, and key responsibilities
3. Identify all mentioned skills including technical skills, programming languages, tools, frameworks, and soft skills
4. Extract any projects mentioned, including personal, academic, or professional projects
5. Identify certifications, licenses, or additional qualifications
6. Extract professional summary or objective if present
7. Note any contact information that's professionally relevant
8. List any uncertainties or missing information that would be helpful to clarify

Focus on accuracy and completeness. If information is unclear or missing, note it in the extraction_uncertainties field.
"""


@dataclass
class Configuration:
    """Configuration for the resume parsing graph."""
    model: str = "gpt-4o-mini"
    temperature: float = 0.1


@dataclass
class State:
    """State for the resume parsing graph."""
    raw_resume: str = ""
    parsed_resume: Optional[ResumeFields] = None
    error: Optional[str] = None
