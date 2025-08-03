from dataclasses import dataclass
from typing import List, Optional, Literal
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from app.services.prompts import JOB_DESCRIPTION_SYSTEM_PROMPT


DepthLevel = Literal["basic", "intermediate", "advanced"]


class ResponsibilityItem(BaseModel):
    skill: str = Field(
        ...,
        description=(
            "The specific technology, tool, or domain skill associated with a responsibility mentioned in the job description. "
            "Examples include 'Python', 'Docker', 'CI/CD', 'Machine Learning', etc. "
            "This should be a concrete skill or technology the candidate is expected to work with."
        )
    )
    description: str = Field(
        ...,
        description=(
            "A brief explanation of what the candidate is expected to do with the corresponding skill. "
            "This can include actions like 'develop microservices', 'maintain CI/CD pipelines', 'analyze data', etc. "
            "It should capture the job task or duty in which the skill is applied, ideally as described in the job description."
        )
    )


class SkillDepthItem(BaseModel):
    skill: str = Field(
        ...,
        description="The skill or technology being assessed for depth level (e.g., 'React', 'Python')."
    )
    depth: DepthLevel = Field(
        ...,
        description="The expected knowledge depth for this skill: 'basic', 'intermediate', or 'advanced'."
    )


class JobDescriptionFields(BaseModel):
    required_skills: List[str] = Field(
        default_factory=list,
        description=(
            "A list of core technical or domain-specific skills that the job explicitly requires. "
            "These are usually found in sections like 'Requirements', 'Must-Have Skills', or 'Qualifications'. "
            "Examples: ['Java', 'React', 'PostgreSQL', 'AWS']. Only include direct mentions, not inferred skills."
        )
    )
    experience_level: Optional[str] = Field(
        default=None,
        description=(
            "The seniority level expected for the candidate, such as 'entry', 'mid', or 'senior'. "
            "This can be derived from terms like '2+ years of experience', 'senior-level', 'fresher', etc. "
            "Return null if no clear level is mentioned."
        )
    )
    responsibilities: List[ResponsibilityItem] = Field(
        default_factory=list,
        description=(
            "A list of responsibilities mentioned in the JD, each paired with the relevant skill involved. "
            "This represents what tasks the candidate will perform and what skills are needed for them. "
            "Each item should contain a 'skill' and a 'description' of what is done with that skill."
        )
    )
    preferred_qualifications: List[str] = Field(
        default_factory=list,
        description=(
            "Optional but desirable skills, certifications, or experiences that would give a candidate an edge. "
            "These are usually found under 'Preferred Qualifications', 'Nice to Have', or similar sections. "
            "Include only what is explicitly mentioned as preferred or optional."
        )
    )
    general_notes: List[str] = Field(
        default_factory=list,
        description=(
            "Other non-technical information that describes the work environment, methodologies, or company culture. "
            "This can include things like 'agile development process', 'remote-first team', 'fast-paced startup', etc. "
            "These help give context about how the work is done but are not skills or qualifications."
        )
    )
    skill_depths: List[SkillDepthItem] = Field(
        default_factory=list,
        description=(
            "A mapping of required skills to expected depth of knowledge. "
            "Use 'basic', 'intermediate', or 'advanced'. "
            "This can be inferred from the JD or flagged for human input if unclear."
        )
    )
    extraction_uncertainties: List[str] = Field(
        default_factory=list,
        description=(
            "List of issues, missing data, or uncertain elements found during extraction. "
            "These should be used to ask follow-up questions or involve a human. "
            "Example: 'Experience level not found.', 'Unclear depth requirement for React.', "
            "'Responsibilities vague for Docker.'"
        )
    )


@dataclass
class Configuration:
    """Configuration for the job description parsing graph."""
    model: str = "gpt-4o-mini"
    temperature: float = 0.1


@dataclass
class State:
    """State for the job description parsing graph."""
    raw_job_description: str = ""
    parsed_job_description: Optional[JobDescriptionFields] = None
    error: Optional[str] = None
