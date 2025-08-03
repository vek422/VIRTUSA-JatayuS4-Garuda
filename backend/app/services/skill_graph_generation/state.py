from dataclasses import dataclass
from typing import List, Literal, Optional, Union, TYPE_CHECKING
from pydantic import BaseModel, Field
from langchain_core.prompts import PromptTemplate
# Define priority type
Priority = Literal["H", "M", "L"]


class SkillNode(BaseModel):
    """Represents a skill node in the DAG with subskills and priority."""
    skill: str = Field(description="The name of the skill")
    priority: Priority = Field(
        description="Priority level: H (High), M (Medium), L (Low)")
    subskills: List["SkillNode"] = Field(
        default_factory=list, description="List of subskills")
    score: int = Field(default=0, description="Current score for this skill")
    total: int = Field(
        default=0, description="Total possible points for this skill")
    passed: bool = Field(
        default=False, description="Whether this skill assessment is passed")

    class Config:
        arbitrary_types_allowed = True


# Update forward references for recursive model
SkillNode.model_rebuild()


class SkillGraph(BaseModel):
    """Represents the complete skill graph with root nodes."""
    root_nodes: List[SkillNode] = Field(description="List of root skill nodes")


@dataclass
class Configuration:
    """Configuration for the skill graph generation."""
    model: str = "gpt-4o-mini"
    temperature: float = 0.1


@dataclass
class State:
    """State for the skill graph generation."""
    raw_job_description: str

    # Output
    skill_graph: Optional[SkillGraph] = None
    error: Optional[str] = None
